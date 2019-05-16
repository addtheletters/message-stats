#!/usr/bin/python3

# perform some analysis on a downloaded Facebook Messenger chat history json
import json, unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from enum import Enum

SPECIAL_REACT_KEYS = ["total", "messages"]

class TimePeriod(Enum):
    ALL = 0
    YEAR = 1
    MONTH = 2
    WEEK = 3
    DAY = 4

def loadjson(filename):
    with open(filename, 'r') as file:
        return json.load(file)
    return None

def createcount():
    ctr = {
            "msg" : 0,
            "sticker" : 0,
            "photos" : 0,
            "share" : 0,
        }

    # "total" : counts up for each react (can be multiple per message)
    # "messages" : counts up only once for each message that gets at least one react
    ctr["reacts_received"] = Counter(total=0, messages=0)
    ctr["reacts_given"] = Counter(total=0)

    ctr["sticker_use"] = Counter()
    ctr["photo_use"] = Counter()

    return ctr

class TimeRangeCount:
    def __init__(self, timerange=None):
        self.timerange = timerange
        self.allcount = createcount()
        self.percount = defaultdict(createcount)
        if timerange != None:
            if len(timerange) != 2:
                print("! time range invalid (start, end)")
            elif self.timerange[0] > self.timerange[1]:
                print("! time range invalid (start > end)")

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

        # count for the sender
        if "sender_name" in msg:
            name = msg["sender_name"]

            if name not in self.percount:
                self.percount[name] = createcount()
            countmessage(msg, self.percount[name])

        # count for total
        countmessage(msg, self.allcount)

        # tally reactions
        countreacts(msg, self.allcount, self.percount)

class TimeDivider:
    ALL_KEY = 0

    def __init__(self, period=TimePeriod.ALL):
        self.trcounts = {}
        self.period = period
        if self.period not in TimePeriod:
            print("! invalid period")
        self.trcounts[TimeDivider.ALL_KEY] = TimeRangeCount()

    def alltime(self):
        return self.trcounts[TimeDivider.ALL_KEY]

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
            return dt - timedelta(days=dt.weekday()) # key using first day of week
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

def countmessage(msg, ctr):
    if ctr is None:
        print("no count object")
        return

    ctr["msg"] += 1

    # what kind of message is it?
    for key in ("sticker", "photos", "share"):
        if key in msg:
            ctr[key] += 1

    # track sticker usage
    if "sticker" in msg:
        sticker = "unknown"
        if "uri" in msg["sticker"]:
            sticker = msg["sticker"]["uri"]
        ctr["sticker_use"][sticker] += 1

    # track repeated image use
    if "photos" in msg:
        for phobj in msg["photos"]:
            photo = "unknown"
            if "uri" in phobj:
                photo = phobj["uri"]
            ctr["photo_use"][photo] += 1

    # TODO track shared link domains

    return

def countreacts(msg, all_ctr, p_ctr):
    if all_ctr is None or p_ctr is None:
        print("missing count object")
        return

    if "reactions" in msg:
        name = msg["sender_name"]
        
        all_ctr["reacts_received"]["messages"] += 1
        p_ctr[name]["reacts_received"]["messages"] += 1

        for react in msg["reactions"]:
            content = react["reaction"]
            actor = react["actor"]

            if actor not in p_ctr:
                p_ctr[actor] = createcount()
            
            # message poster
            p_ctr[name]["reacts_received"]["total"] += 1
            p_ctr[name]["reacts_received"][content] += 1

            # reactor
            p_ctr[actor]["reacts_given"]["total"] += 1
            p_ctr[actor]["reacts_given"][content] += 1

            # total
            all_ctr["reacts_given"]["total"] += 1
            all_ctr["reacts_given"][content] += 1
            all_ctr["reacts_received"]["total"] += 1
            all_ctr["reacts_received"][content] += 1
    return


def ratiostr(a, b):
    return str(a) + " / " + str(b) + " (" + str(round(a/b * 100, 3)) + " %)"

def printcount(ctr):
    print("stickers: " + ratiostr(ctr["sticker"], ctr["msg"]))
    printstickers(ctr, 2)
    print("photos: " + ratiostr(ctr["photos"], ctr["msg"]))
    print("links: " + ratiostr(ctr["share"], ctr["msg"]))
    print()
    return

def printreacts(ctr, total_msgs=None, most_common=2):
    print("reacts: ")
    print("received on: " + ratiostr(ctr["reacts_received"]["messages"], ctr["msg"]))
    print("received total: {} ({} / message)".format(ctr["reacts_received"]["total"], round(ctr["reacts_received"]["total"] / ctr["msg"], 3)))

    # try to show the most_common most common reacts, skipping the "total" and "message" counters
    common_received = ctr["reacts_received"].most_common()[:most_common+len(SPECIAL_REACT_KEYS)]
    print("\t{} most common received reacts:".format(most_common))

    i, displayed = 0, 0
    while i < len(common_received) and displayed < most_common:
        react = common_received[i]
        if react[0] not in SPECIAL_REACT_KEYS:
            print("\t\t{}: {}".format(getreactname(react[0]), ratiostr(react[1], ctr["reacts_received"]["total"])))
            displayed += 1
        i += 1

    # overall total provided, so this is a specific user; show this since received/given differ
    if total_msgs:
        print("given: " + ratiostr(ctr["reacts_given"]["total"], total_msgs))

        common_given = ctr["reacts_given"].most_common()[:most_common+len(SPECIAL_REACT_KEYS)]
        i, displayed = 0, 0
        print("\t{} most common given reacts:".format(most_common))
        while i < len(common_given) and displayed < most_common:
            react = common_given[i]
            if react[0] not in SPECIAL_REACT_KEYS:
                print("\t\t{}: {}".format(getreactname(react[0]), ratiostr(react[1], ctr["reacts_given"]["total"])))
                displayed += 1
            i += 1
    return

def getreactname(reactstr):
    reactbytes = bytes(reactstr, encoding='raw_unicode_escape')
    return unicodedata.name(reactbytes.decode("utf-8")[0])

def printstickers(ctr, most_common=3):
    common_stickers = ctr["sticker_use"].most_common()[:most_common]
    print("\t{} most common stickers:".format(most_common))
    for sticker in common_stickers[:most_common]:
        print("\t\t{}: {}".format(sticker[1], sticker[0]))
    return

def analyze(chat, period=TimePeriod.ALL):
    if "messages" not in chat:
        print("no messages")
        return
 
    messages = chat["messages"]

    td = TimeDivider(period=period)
    #dtcount = TimeRangeCount()
    for msg in messages:
        #dtcount.message(msg)
        td.message(msg)
   
    return td

def printanalysis(td):
    for timekey, trcount in td.trcounts.items():
        print("\n=========== chat stats for " + trcount.rangestr())
        for name, pstats in trcount.percount.items():
            print("---\nfor {}:".format(name))
            print("messages: {} / {} = {} %".format(pstats["msg"], trcount.allcount["msg"], round(pstats["msg"] / trcount.allcount["msg"] * 100, 3)))
            printcount(pstats)
            printreacts(pstats, trcount.allcount["msg"])

        print("---\ntime period totals:")
        print("messages sent: " + str(trcount.allcount["msg"]))
        printcount(trcount.allcount)
        printreacts(trcount.allcount)
        print("============ end stats for " + trcount.rangestr())
    return

def main():
    bjork = loadjson("bjork_message.json")
    td = analyze(bjork, TimePeriod.YEAR)
    printanalysis(td)
    return

if __name__ == '__main__':
    main()
