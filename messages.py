#!/usr/bin/python3

# perform some analysis on a downloaded Facebook Messenger chat history json
import json, unicodedata
from collections import Counter

SPECIAL_REACT_KEYS = ["total", "messages"]

def loadfile(filename):
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
    printstickers(ctr)
    print("photos: " + ratiostr(ctr["photos"], ctr["msg"]))
    print("links: " + ratiostr(ctr["share"], ctr["msg"]))
    print()
    return

def printreacts(ctr, total_msgs=None, most_common=3):
    print("reacts: ")
    print("received on: " + ratiostr(ctr["reacts_received"]["messages"], ctr["msg"]))
    print("received total: {} ({} / message)".format(ctr["reacts_received"]["total"], round(ctr["reacts_received"]["total"] / ctr["msg"], 3)))

    # try to show the most_common most common reacts, skipping the "total" and "message" counters
    common_received = ctr["reacts_received"].most_common()[:most_common+2]
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

        common_given = ctr["reacts_given"].most_common()[:most_common+2]
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

def analyze(chat):
    if "messages" not in chat:
        print("no messages")
        return
 
    messages = chat["messages"]

    count = createcount()
    p_count = {}
    for person in chat["participants"]:
        p_count[person["name"]] = createcount()

    for msg in messages:
        # count all messages
        countmessage(msg, count)

        # count for the sender
        if "sender_name" in msg:
            name = msg["sender_name"]
            if name not in p_count:
                p_count[name] = createcount()
            countmessage(msg, p_count[name])

        # tally reactions
        countreacts(msg, count, p_count)

    for person in p_count:
        print("===========\nstats for {}:".format(person))
        print("messages: {} / {} = {} %".format(p_count[person]["msg"], count["msg"], round(p_count[person]["msg"] / count["msg"] * 100, 3)))
        printcount(p_count[person])
        printreacts(p_count[person], count["msg"])

    print("==========\nOVERALL TOTALS:")
    print("messages sent: " + str(count["msg"]))
    printcount(count)
    printreacts(count)

    return (count, p_count)

# def test():
#     bjork = loadfile("bjork_message.json")
#     return analyze(bjork)
# test()
