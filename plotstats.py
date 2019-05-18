#!/usr/bin/python3

# graph results of facebook messenger chat history analysis

import messages as msgs
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox, TextArea
from matplotlib.patches import Rectangle
from datetime import datetime
from random import randrange, random

STANDARD_STICKER_SIZE = 230400

def testplot(td):
    # emoji density?


    plt.figure(figsize=(6, 4))
    plt.savefig("test.png", format="png", dpi=256)
    return

def stickercosinesimilarity(td):
    mincount = 2
    ss = msgs.stickersimilarity(td.alltime(), mincount=mincount, excludeself=True)
    names = ss[0]
    mat = ss[1]
    ind = [i for i in range(len(names))]

    plt.figure(figsize=(5,4.5))
    plt.title("Sticker Use Cosine Similarity (mincount {})".format(mincount))
    ax = plt.gca()
    ax.imshow(mat)

    ax.tick_params(labelsize=5)
    ax.set_xticks(ind)
    ax.set_yticks(ind)
    ax.set_xticklabels(names)
    ax.set_yticklabels(names)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    for i in ind:
        for j in ind:
            txt = ax.text(j, i, round(mat[i][j], 3), ha="center", va="center", color="w")

    plt.savefig("stickercosinesimilarity.png", format="png", dpi=256)
    return

def randcolor(previous=[]):
    choices = ["red", "blue", "green", "yellow", "magenta", "orange", "cyan", "purple"]
    for c in previous:
        if c in choices:
            choices.remove(c)
    if len(choices) == 0:
        return (random(), random(), random(), 1)
    return choices[randrange(len(choices))]

def monthlyuse(td, countkey, usekey, num=5, width=0.37, imglabel=True, size=(9,4), labelrotate=45, labelsize=1):
    # monthly most used? exclude no-use months
    times = [dt for dt in td.getallkeys() if td.trcounts[dt].allcount[countkey] != 0]
    timelabels = [dt.strftime("%b%y") for dt in times]

    rankings = []
    for i in range(num):
        rankings.append(([], [])) #(uris, counts)

    for dt in times:
        items = td.trcounts[dt].allcount[usekey].most_common()[:num]
        for i in range(num):
            if i < len(items):
                rankings[i][0].append(items[i][0])
                rankings[i][1].append(items[i][1])
            else:
                rankings[i][0].append(None)
                rankings[i][1].append(0)
    
    plt.figure(figsize=size)
    plt.title("Monthly most-used {}".format(countkey) + "s" if countkey[-1] != 'i' else "")
    plt.ylabel("uses")
    ax = plt.gca()
    ax.tick_params(labelsize=4)

    barsets = []
    ind = [2*x for x in range(len(timelabels))]
    bases = []
    plt.xticks([x+(width * (num-1) / 2) for x in ind])

    colors = {}

    for rank in rankings:
        barsets.append(ax.bar(ind, rank[1], width))

        for ri in range(len(barsets[-1].patches)):
            rect = barsets[-1].patches[ri]
            if rank[0][ri] not in colors:
                if rank[0][ri] == "www.reddit.com":
                    colors[rank[0][ri]] = "peachpuff"
                elif rank[0][ri] == "i.redd.it":
                    colors[rank[0][ri]] = "orange"
                elif rank[0][ri] == "twitter.com":
                    colors[rank[0][ri]] = "skyblue"
                elif rank[0][ri] == "www.youtube.com":
                    colors[rank[0][ri]] = "indianred"
                elif rank[0][ri] == "www.facebook.com":
                    colors[rank[0][ri]] = "navy"
                elif rank[0][ri] == "imgur.com":
                    colors[rank[0][ri]] = "gray"
                elif rank[0][ri] == "i.imgur.com":
                    colors[rank[0][ri]] = "lightslategrey"
                elif rank[0][ri] == "clips.twitch.tv":
                    colors[rank[0][ri]] = "purple"
                else:
                    colors[rank[0][ri]] = randcolor(colors.values())
            rect.set_color(colors[rank[0][ri]])

        # save x positions of bars
        for x in ind:
            bases.append(x)

        # shift x position of next set of bars
        for i in range(len(ind)):
            ind[i] = ind[i] + width

    # show images as x-axis labels
    i = 0
    for rank in range(num):
        for pair in rankings[rank][0]:
            if pair != None:
                if imglabel:
                    addpngxlabel(pair, ax, bases[i], 0.05)
                else:
                    addtextxlabel(pair, ax, bases[i], rotate=labelrotate, size=labelsize)
            i += 1

    ax.set_xticklabels(timelabels)

    plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.2)

    plt.savefig("monthly{}use.png".format(countkey), format="png", dpi=256)
    return

def monthlystickeruse(td):
    monthlyuse(td, "sticker", "sticker_use", size=(50,5))
    return

def monthlylinkuse(td):
    monthlyuse(td, "share", "link_domains", num=5, imglabel=False, size=(20,5))
    return

def monthlyemojiuse(td):
    matplotlib.rc('font', family='DejaVu Sans')
    monthlyuse(td, "emoji", "emoji_use", num=4, imglabel=False, size=(20, 5), labelrotate=0, labelsize=2)
    return

def monthlyreactgivendensity(td):
    # exclude months before reacts existed
    times = [dt for dt in td.getallkeys() if td.trcounts[dt].allcount["reacts_received"]["total"] != 0]
    timelabels = [dt.strftime("%b%y") for dt in times]

    activity = []
    for dt in times:
        activity.append(td.trcounts[dt].allcount["msg"])

    personal_activity = {}
    personal_reacts = {}
    names = []

    for name, pcount in td.alltime().percount.items():
        names.append(name)
        personal_activity[name] = [0] * len(times)
        personal_reacts[name] = [0] * len(times)
    
    for i in range(len(times)):
        dt = times[i]
        for name in names:
            if name in td.trcounts[dt].percount:
                personal_activity[name][i] = td.trcounts[dt].percount[name]["msg"]
                personal_reacts[name][i] = td.trcounts[dt].percount[name]["reacts_given"]["total"]

    personal_density = {}
    for name in personal_reacts:
        personal_density[name] = [personal_reacts[name][i] / activity[i] for i in range(len(times))]

    plt.figure(figsize=(9, 4))
    plt.title("Reacts-given Density")
    plt.ylabel("user's reacts / all messages")
    ax = plt.gca()
    ax.tick_params(labelsize=4)

    addpersonbarstack(timelabels, names, personal_density)

    plt.savefig("monthlyreactgivendensity.png", format="png", dpi=200)
    return

def monthlyreactdensity(td):
    # exclude months before reacts existed
    times = [dt for dt in td.getallkeys() if td.trcounts[dt].allcount["reacts_received"]["total"] != 0]
    timelabels = [dt.strftime("%b%y") for dt in times]

    activity = []
    reacts = []
    for dt in times:
        activity.append(td.trcounts[dt].allcount["msg"])
        reacts.append(td.trcounts[dt].allcount["reacts_received"]["total"])

    density = [reacts[i] / activity[i] for i in range(len(activity))]

    plt.figure(figsize=(9, 4))
    plt.title("Monthly react density")
    plt.ylabel("reacts / messages")
    ax = plt.gca()
    ax.tick_params(labelsize=4)

    plt.bar(timelabels, density)

    plt.savefig("monthlyreactdensity.png", format="png", dpi=200)
    return

def monthlyactivity(td):
    # by-time-period distribution
    # assume months?

    times = td.getallkeys()
    timelabels = [dt.strftime("%b%y") for dt in times]
    # activity = []
    # for dt in times:
    #     activity.append(td.trcounts[dt].allcount["msg"])

    names = []
    personal_activity = {}
    for name, pcount in td.alltime().percount.items():
        names.append(name)
        personal_activity[name] = [0] * len(timelabels)
    
    for i in range(len(times)):
        dt = times[i]
        for name in names:
            personal_activity[name][i] = td.trcounts[dt].percount[name]["msg"]

    plt.figure(figsize=(9, 4))
    plt.title("Monthly activity")
    plt.ylabel("messages sent")
    ax = plt.gca()
    ax.tick_params(labelsize=4)

    addpersonbarstack(timelabels, names, personal_activity)
    #plt.bar(timelabels, activity)

    plt.savefig("monthlyactivity.png", format="png", dpi=200)
    return

def alltimestickers(td):
    num = 15

    allt = td.alltime()
    #msgs.printstickers(allt.allcount, num)
    sticks = allt.allcount["sticker_use"].most_common()[:num]

    rank = [i+1 for i in range(len(sticks))]
    stickfiles = [s[0] for s in sticks]
    names = []
    personal_use = {}
    for name, pcount in allt.percount.items():
        names.append(name)
        personal_use[name] = [0] * len(stickfiles)
        for i in range(len(stickfiles)):
            personal_use[name][i] = pcount["sticker_use"][stickfiles[i]]

    addpersonbarstack(rank, names, personal_use)

    plt.ylabel("Uses")
    plt.title("Most common stickers ({})".format(allt.rangestr()))
    plt.xticks(rank)

    # show stickers as x-axis labels
    ax = plt.gca()
    for i in range(len(sticks)):
        addpngxlabel(sticks[i][0], ax, i+1, 0.05)

    plt.savefig("alltimestickers.png", format="png", dpi=256)
    return

def addpngxlabel(filename, ax, xcoord, scale=0.02):
    img = plt.imread(filename, format='png')
    # scale large stickers to roughly match the standard
    dim = (img.size + img[0].size) / 2
    if dim > STANDARD_STICKER_SIZE:
        scale = scale * (STANDARD_STICKER_SIZE / dim)
    imagebox = OffsetImage(img, zoom=scale)
    imagebox.image.axes = ax
    ab = AnnotationBbox(imagebox, (xcoord, 0), xybox=(0, -16),
                    xycoords=("data", "axes fraction"),
                    boxcoords="offset points",
                    box_alignment=(.5, 1),
                    bboxprops={"edgecolor":"none", "alpha":0})
    ax.add_artist(ab)
    return

def addtextxlabel(txt, ax, xcoord, rotate=45, size=1):
    textbox = TextArea(txt, textprops={
        "fontsize":3*size,
        "rotation":rotate,
        "ha":"right",
        "rotation_mode":"anchor",
        "fontstretch":"ultra-condensed"
        })
    ab = AnnotationBbox(textbox, (xcoord, 0), xybox=(0, -15),
                    xycoords=("data", "axes fraction"),
                    boxcoords="offset points",
                    box_alignment=(0, 0),
                    bboxprops={"edgecolor":"none", "alpha":0})
    ax.add_artist(ab)
    return

def addpersonbarstack(xitems, names, personal, width=0.5):
    bars = []
    top = [0] * len(xitems)
    for i in range(len(names)):
        name = names[i]
        bars.append(plt.bar(xitems, personal[name], width=width, bottom=top))
        top = [top[i] + personal[name][i] for i in range(len(xitems))]
    plt.legend(bars, names, fontsize="small")

def main():
    #bjork = msgs.loadjson("bjork_message.json")
    #td = msgs.analyze(bjork, msgs.TimePeriod.MONTH)
    td = msgs.loadjson("bjork_analysis.json")

    print("analysis loaded, plotting...")

    #testplot(td)
    #stickercosinesimilarity(td)
    #monthlyreactgivendensity(td)
    #monthlystickeruse(td)
    #monthlylinkuse(td)
    #monthlyemojiuse(td)
    #monthlyactivity(td)
    #alltimestickers(td)
    return

if __name__ == '__main__':
    main()
