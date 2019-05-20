#!./venv/bin/python3

# perform some analysis on a downloaded Facebook Messenger chat history json
import sys, json, unicodedata, urllib.parse
import numpy as np # https://www.numpy.org/
from textblob import TextBlob # https://textblob.readthedocs.io/
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from enum import Enum

SPECIAL_TIMERANGE = "__timerange__"
SPECIAL_TIMEDIVIDER = "__timedivider__"

EVERYONE_STICKER_KEY = "everyone"
COUNTER_KEYS = [ "reacts_received_use",
                 "reacts_given_use",
                 "sticker_use",
                 "photo_use",
                 "share_use",
                 "emoji_use",
                 "words_use" ]

TEST_FILE = "bjork_message.json"
TEST_SAVE = "bjork_analysis.json"
TEST_PLACEHOLDER = "__test__"

class TimePeriod(Enum):
    ALL = 0
    YEAR = 1
    MONTH = 2
    WEEK = 3
    DAY = 4

    def describe(self):
        if self == TimePeriod.ALL:
            return "all-time"
        if self == TimePeriod.YEAR:
            return "yearly"
        if self == TimePeriod.MONTH:
            return "monthly"
        if self == TimePeriod.WEEK:
            return "weekly"
        if self == TimePeriod.DAY:
            return "daily"
        return self.name + "-ly"

    def formats(self):
        if self == TimePeriod.ALL:
            return "all-time"
        if self == TimePeriod.YEAR:
            return "%Y"
        if self == TimePeriod.MONTH:
            return "%b%y"
        if self == TimePeriod.WEEK:
            return "w%Wy%y"
        if self == TimePeriod.DAY:
            return "%d%b%y"
        return self.name + "?"

    @staticmethod
    def parse(s):
        if s in ("a", "all"):
            return TimePeriod.ALL
        if s in ("y", "year"):
            return TimePeriod.YEAR
        if s in ("m", "month"):
            return TimePeriod.MONTH
        if s in ("w", "week"):
            return TimePeriod.WEEK
        if s in ("d", "day"):
            return TimePeriod.DAY
        raise ValueError("{} could not be interpreted as a time period.".format(s))

TEST_PERIOD = TimePeriod.MONTH

# things to try still:
# sentiment analysis

# cosine similarity of participants' sticker usage vectors
def sticker_similarity(trc, mincount=3, excludeself=False):
    stickers = []
    names = [EVERYONE_STICKER_KEY]
    usage = {}

    for name in trc.percount:
        names.append(name)

    for name in names:
        usage[name] = [] # personal usage vector

    for stk, ct in trc.allcount["sticker_use"].items():
        if ct < mincount:
            continue
        stickers.append(stk)
        usage[EVERYONE_STICKER_KEY].append(ct)
        for name in trc.percount:
            if stk in trc.percount[name]["sticker_use"]:
                usage[name].append(trc.percount[name]["sticker_use"][stk])
            else:
                usage[name].append(0)

    print("{} stickers with usage over {}.".format(len(stickers), mincount))

    similarity = [[0] * len(names) for _ in range(len(names))]
    for i in range(len(similarity)):
        for j in range(len(similarity[0])):
            va = np.array(usage[names[i]])
            vb = np.array(usage[names[j]])

            if excludeself:
                if names[i] == EVERYONE_STICKER_KEY and names[j] == EVERYONE_STICKER_KEY:
                    va, vb = va - vb, vb - va 
                elif names[i] == EVERYONE_STICKER_KEY:
                    va = va - vb
                elif names[j] == EVERYONE_STICKER_KEY:
                    vb = vb - va

            va = (va / np.linalg.norm(va) if np.linalg.norm(va) != 0 else va)
            vb = (vb / np.linalg.norm(vb) if np.linalg.norm(vb) != 0 else vb)
            divisor = (np.linalg.norm(va) * np.linalg.norm(vb))
            if divisor == 0:
                divisor = 1
            similarity[i][j] = np.dot(va, vb) / divisor

    if excludeself:
        names[0] += " else"

    return (names, similarity, stickers, usage)

def counterify(dct):
    for key in COUNTER_KEYS:
        dct[key] = Counter(dct[key])
    return dct

def loadjson(filename):
    def decoder(dct):
        if SPECIAL_TIMERANGE in dct:
            return TimeRangeCount.decode(dct)
        if SPECIAL_TIMEDIVIDER in dct:
            return TimeDivider.decode(dct)
        return dct

    with open(filename, 'r') as file:
        return json.load(file, object_hook=decoder)
    return None

def savejson(obj, filename):
    obj["__special__"] = True
    with open(filename, 'w') as file:
        json.dump(obj, file, indent=2)
    return

def create_count():
    ctr = {
            "msg" : 0,
            "sticker" : 0,
            "photos" : 0,
            "share" : 0,
            "emoji" : 0,
            "words" : 0,
            "reacts_given" : 0,
            "reacts_received_messages" : 0, # counts up only once for each message that gets at least one react
            "reacts_received_total" : 0,    # counts up for each react (can be multiple per message)

            "sentiment_total" : [0,0],
            "content" : 0,
        }

    ctr["reacts_received_use"] = Counter()
    ctr["reacts_given_use"] = Counter()

    ctr["sticker_use"] = Counter()
    ctr["photo_use"] = Counter()
    ctr["share_use"] = Counter()

    ctr["emoji_use"] = Counter()
    ctr["words_use"] = Counter()

    ctr["sentiments"] = []

    return ctr

class TimeRangeCount:
    def __init__(self, timerange=None):
        self.timerange = timerange
        self.allcount = create_count()
        self.percount = defaultdict(create_count)
        if timerange != None:
            if len(timerange) != 2:
                print("! time range invalid (start, end)")
            elif self.timerange[0] > self.timerange[1]:
                print("! time range invalid (start > end)")

    @staticmethod
    def decode(dct):
        trange = None
        if dct["timerange"] is not None:
            trange = (datetime.fromtimestamp(dct["timerange"][0]), datetime.fromtimestamp(dct["timerange"][1]))
        trc = TimeRangeCount(timerange=trange)
        trc.allcount = counterify(dct["allcount"])
        trc.percount = {}
        for k, d in dct["percount"].items():
            trc.percount[k] = counterify(d) 
        return trc

    def serializable(self):
        s = {}
        s[SPECIAL_TIMERANGE] = True
        s["timerange"] = None if self.timerange is None else (self.timerange[0].timestamp(), self.timerange[1].timestamp())
        s["allcount"] = self.allcount
        s["percount"] = self.percount
        return s

    def rangestr(self):
        if self.timerange is None:
            return "all time"
        return "{} - {}".format(self.timerange[0], self.timerange[1])

    def inrange(self, dt):
        if self.timerange is None:
            return True
        return dt >= self.timerange[0] and dt < self.timerange[1]

    def message(self, msg):
        if self.timerange != None and "timestamp_ms" in msg:
            msg_dt = datetime.fromtimestamp(msg["timestamp_ms"]/1000.0)
            if not self.inrange(msg_dt):
                print("message not in time range ({} to {})".format(self.timerange[0], self.timerange[1]))
                return

        # count things
        count_message(msg, self.allcount, self.percount)

        # tally reactions
        count_reacts(msg, self.allcount, self.percount)

class TimeDivider:
    ALL_KEY = "TimeDivider_ALLKEY"

    def __init__(self, period=TimePeriod.ALL):
        self.trcounts = {}
        self.period = period
        if self.period not in TimePeriod:
            print("! invalid period")
        self.trcounts[TimeDivider.ALL_KEY] = TimeRangeCount()

    @staticmethod
    def decode(dct):
        td = TimeDivider(TimePeriod(dct["period"]))
        trcs = {}
        for timestamp in dct["trcounts"]:
            if timestamp == TimeDivider.ALL_KEY:
                trcs[timestamp] = dct["trcounts"][timestamp]
            else:
                trcs[datetime.fromtimestamp(float(timestamp))] = dct["trcounts"][timestamp]
        td.trcounts = trcs
        return td

    def serializable(self):
        s = {}
        s[SPECIAL_TIMEDIVIDER] = True
        s["trcounts"] = {}
        for k in self.trcounts:
            if isinstance(k, datetime):
                s["trcounts"][k.timestamp()] = self.trcounts[k].serializable()
            else:
                s["trcounts"][k] = self.trcounts[k].serializable()
        s["period"] = self.period.value
        return s

    def alltime(self):
        return self.trcounts[TimeDivider.ALL_KEY]

    # sorted
    def getallkeys(self):
        keys = [k for k in self.trcounts if k != TimeDivider.ALL_KEY]
        return sorted(keys)

    def message(self, msg):
        self.trcounts[TimeDivider.ALL_KEY].message(msg)

        if self.period != TimePeriod.ALL:
            msg_dt = None if "timestamp_ms" not in msg else datetime.fromtimestamp(msg["timestamp_ms"]/1000.0)
            timekey = self.getkey(msg_dt)

            if timekey not in self.trcounts:
                self.trcounts[timekey] = self.createtrcount(timekey)
            self.trcounts[timekey].message(msg)

    # a datetime representing the start of a time period to be counted for
    def getkey(self, dt):
        if self.period is TimePeriod.ALL:
            return TimeDivider.ALL_KEY
        elif self.period is TimePeriod.YEAR:
            return datetime(year=dt.year, month=1, day=1)
        elif self.period is TimePeriod.MONTH:
            return datetime(year=dt.year, month=dt.month, day=1)
        elif self.period is TimePeriod.WEEK:
            pdt = dt - timedelta(days=dt.weekday())
            return datetime(year=pdt.year, month=pdt.month, day=pdt.day) # key using first day of week
        elif self.period is TimePeriod.DAY:
            return datetime(year=dt.year, month=dt.month, day=dt.day)
        return None

    # a datetime tuple with the start and end of a time period to be counted
    def getrange(self, key):
        if self.period is TimePeriod.ALL:
            return None
        elif self.period is TimePeriod.YEAR:
            return (key, datetime(year=key.year+1, month=1, day=1))
        elif self.period is TimePeriod.MONTH:
            if key.month == 12:
                return (key, datetime(year=key.year+1, month=1, day=1))
            return (key, datetime(year=key.year, month=key.month+1, day=1))
        elif self.period is TimePeriod.WEEK:
            return (key, key + timedelta(days=7))
        elif self.period is TimePeriod.DAY:
            return (key, key + timedelta(days=1))
        return None

    def createtrcount(self, key):
        return TimeRangeCount(self.getrange(key))

def count_message(msg, ctr, p_ctr):
    if ctr is None:
        print("no count object")
        return

    sender = ""
    if "sender_name" in msg:
        sender = msg["sender_name"]
    if sender not in p_ctr:
        p_ctr[sender] = create_count()

    ctr["msg"] += 1
    p_ctr[sender]["msg"] += 1

    # what kind of message is it?
    for key in ("sticker", "photos", "share"):
        if key in msg:
            ctr[key] += 1
            p_ctr[sender][key] += 1

    # track sticker usage
    if "sticker" in msg:
        sticker = "unknown"
        if "uri" in msg["sticker"]:
            sticker = msg["sticker"]["uri"]
        ctr["sticker_use"][sticker] += 1
        p_ctr[sender]["sticker_use"][sticker] += 1

    # track repeated image use
    if "photos" in msg:
        for phobj in msg["photos"]:
            photo = "unknown"
            if "uri" in phobj:
                photo = phobj["uri"]
            ctr["photo_use"][photo] += 1
            p_ctr[sender]["photo_use"][photo] += 1

    # track shared link domains
    if "share" in msg:
        if "link" in msg["share"]:
            domain = urllib.parse.urlparse(msg["share"]["link"]).netloc
            ctr["share_use"][domain] += 1
            p_ctr[sender]["share_use"][domain] += 1
        #if "share_text" in msg["share"]:
        #if len(msg["share"].keys()) != 1 or "link" not in msg["share"]:
            #print(msg)

    if "content" in msg:
        ctr["content"] += 1
        p_ctr[sender]["content"] += 1

        # --------
        # track emoji use
        i = 0
        while i < len(msg["content"]):
            ch = msg["content"][i]
            chsize = 1
            if ch == '\u00f0': # emoticon or symbol
                if i+7 < len(msg["content"]) and msg["content"][i+2] is '\u0087': # country code, 8 bytes
                    chsize = 8
                else: # 4 "bytes"
                    chsize = 4
            elif ch == '\u00e2' or ch == '\u00e3': # dingbat or other 3 "bytes"
                chsize = 3
            elif ch == '\u00c2': # copyright or registered sign
                chsize = 2

            if chsize != 1:
                if i + chsize <= len(msg["content"]):
                    #print("trying to understand ({}) {}".format(chsize, bytes(msg["content"][i:i+chsize], encoding="raw_unicode_escape")))
                    emoji = weirdbytes_to_utf(msg["content"][i:i+chsize])
                    ctr["emoji"] += 1
                    ctr["emoji_use"][emoji] += 1

                    p_ctr[sender]["emoji"] += 1
                    p_ctr[sender]["emoji_use"][emoji] += 1
                else:    # message ended before emoji detected?
                    print("tried to find emoji past end of message")

            i += chsize

        # ----------
        # track word use
        for word in msg["content"].split(" "):
            ctr["words"] += 1
            ctr["words_use"][word] += 1
            p_ctr[sender]["words"] += 1
            p_ctr[sender]["words_use"][word] += 1

        # ---------
        # text processing, sentiment analysis
        track_sentiment(msg, ctr, p_ctr) 

    return

def count_reacts(msg, all_ctr, p_ctr):
    if all_ctr is None or p_ctr is None:
        print("missing count object")
        return

    if "reactions" in msg:
        name = msg["sender_name"]
        
        all_ctr["reacts_received_messages"] += 1
        p_ctr[name]["reacts_received_messages"] += 1

        for react in msg["reactions"]:
            content = react["reaction"]
            actor = react["actor"]

            if actor not in p_ctr:
                p_ctr[actor] = create_count()
            
            # message poster
            p_ctr[name]["reacts_received_total"] += 1
            p_ctr[name]["reacts_received_use"][content] += 1

            # reactor
            p_ctr[actor]["reacts_given"] += 1
            p_ctr[actor]["reacts_given_use"][content] += 1

            # total
            all_ctr["reacts_given"] += 1
            all_ctr["reacts_given_use"][content] += 1
            all_ctr["reacts_received_total"] += 1
            all_ctr["reacts_received_use"][content] += 1
    return

def track_sentiment(msg, all_ctr, p_ctr):
    if "content" not in msg:
        return

    blob = TextBlob(msg["content"])
    sentiment = blob.sentiment #(blob.sentiment.polarity, blob.sentiment.subjectivity)
    all_ctr["sentiments"].append(sentiment)
    all_ctr["sentiment_total"][0] += sentiment.polarity
    all_ctr["sentiment_total"][1] += sentiment.subjectivity
    p_ctr[msg["sender_name"]]["sentiments"].append(sentiment)
    p_ctr[msg["sender_name"]]["sentiment_total"][0] += sentiment.polarity
    p_ctr[msg["sender_name"]]["sentiment_total"][1] += sentiment.subjectivity

    return

def ratiostr(a, b):
    return str(a) + " / " + str(b) + " (" + str(round(a/b * 100, 3)) + " %)"

def print_count(ctr):
    print("stickers: " + ratiostr(ctr["sticker"], ctr["msg"]))
    print_stickers(ctr, 2)
    print("photos: " + ratiostr(ctr["photos"], ctr["msg"]))
    print("links: " + ratiostr(ctr["share"], ctr["msg"]))
    print()
    return

def print_reacts(ctr, total_msgs=None, most_common=2):
    print("reacts: ")
    print("received on: " + ratiostr(ctr["reacts_received_messages"], ctr["msg"]))
    print("received total: {} ({} / message)".format(ctr["reacts_received_total"], round(ctr["reacts_received_total"] / ctr["msg"], 3)))

    # try to show the most_common most common reacts, skipping the "total" and "message" counters
    common_received = ctr["reacts_received_use"].most_common()[:most_common]
    print("\t{} most common received reacts:".format(most_common))
    for i in range(len(common_received)):
        react = common_received[i]
        print("\t\t{}: {}".format(get_emoji_name(react[0]), ratiostr(react[1], ctr["reacts_received_total"])))

    # overall total provided, so this is a specific user; show this since received/given differ
    if total_msgs:
        print("given: " + ratiostr(ctr["reacts_given"], total_msgs))
        common_given = ctr["reacts_given_use"].most_common()[:most_common]
        print("\t{} most common given reacts:".format(most_common))
        for i in range(len(common_given)):
            react = common_given[i]
            print("\t\t{}: {}".format(get_emoji_name(react[0]), ratiostr(react[1], ctr["reacts_given"])))
    return

def weirdbytes_to_utf(ch):
    return bytes(ch, encoding='raw_unicode_escape').decode("utf-8")

def get_emoji_name(emojistr):
    return unicodedata.name(weirdbytes_to_utf(emojistr)[0])

def print_stickers(ctr, most_common=3):
    common_stickers = ctr["sticker_use"].most_common()[:most_common]
    print("\t{} most common stickers:".format(most_common))
    for sticker in common_stickers[:most_common]:
        print("\t\t{}: {}".format(sticker[1], sticker[0]))
    return

def analyze(chat, period=TimePeriod.ALL, restrict_range=None):
    if "messages" not in chat:
        print("no messages")
        return
 
    messages = chat["messages"]

    total = len(messages)
    progress = 0
    checkpoints = [i * (total // 10) for i in range(1,10)]

    td = TimeDivider(period=period)
    for msg in messages:
        if progress in checkpoints:
            print("\t... {}/{}".format(progress+1, total))
        # if restrict_range is None or msg in range:
        td.message(msg)
        progress += 1
   
    return td

def print_analysis(td):
    for timekey, trcount in td.trcounts.items():
        print("\n=========== chat stats for " + trcount.rangestr())
        for name, pstats in trcount.percount.items():
            print("---\nfor {}:".format(name))
            print("messages: {} / {} = {} %".format(pstats["msg"], trcount.allcount["msg"], round(pstats["msg"] / trcount.allcount["msg"] * 100, 3)))
            print_count(pstats)
            print_reacts(pstats, trcount.allcount["msg"])

        print("---\ntime period totals:")
        print("messages sent: " + str(trcount.allcount["msg"]))
        print_count(trcount.allcount)
        print_reacts(trcount.allcount)
        print("============ end stats for " + trcount.rangestr())
    return

def main():
    loadfile = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != TEST_PLACEHOLDER else TEST_FILE
    savefile = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != TEST_PLACEHOLDER else TEST_SAVE
    period = TimePeriod.parse(sys.argv[3]) if len(sys.argv) > 3 else TEST_PERIOD

    print("loading messages from {}".format(loadfile))
    bjork = loadjson(loadfile)
    print("... loaded. analyzing. ({} period)".format(period.describe()))
    td = analyze(bjork, period)
    
    #print_analysis(td)

    print("saving to {}".format(savefile))
    savejson(td.serializable(), savefile)
    print("saved to {}".format(savefile))

    return

if __name__ == '__main__':
    main()
