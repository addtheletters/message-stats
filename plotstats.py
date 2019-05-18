#!/usr/bin/python3

# graph results of facebook messenger chat history analysis

import messages as msgs
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from datetime import datetime

STANDARD_SIZE = 230400

def testplot(td):
    plt.savefig("test.png", format="png", dpi=256)
    return

def monthlystickeruse(td):
    num = 5
    width = 0.37
    # monthly most used stickers? exclude no-sticker months
    times = [dt for dt in td.getallkeys() if td.trcounts[dt].allcount["sticker"] != 0]
    timelabels = [dt.strftime("%b%y") for dt in times]

    rankings = []
    for i in range(num):
        rankings.append(([], [])) #(uris, counts)

    for dt in times:
        stickers = td.trcounts[dt].allcount["sticker_use"].most_common()[:num]
        for i in range(num):
            if i < len(stickers):
                rankings[i][0].append(stickers[i][0])
                rankings[i][1].append(stickers[i][1])
            else:
                rankings[i][0].append(None)
                rankings[i][1].append(0)
    
    plt.figure(figsize=(50,5))
    plt.title("Monthly most-used stickers")
    plt.ylabel("uses")
    ax = plt.gca()
    ax.tick_params(labelsize=4)

    barsets = []
    ind = [2*x for x in range(len(timelabels))]
    bases = []
    plt.xticks([x+(width * (num-1) / 2) for x in ind])

    for rank in rankings:
        barsets.append(ax.bar(ind, rank[1], width))

        # save x positions of bars
        for x in ind:
            bases.append(x)

        # shift x position of next set of bars
        for i in range(len(ind)):
            ind[i] = ind[i] + width

    # show stickers as x-axis labels
    ax = plt.gca()
    i = 0
    for rank in range(num):
        for pair in rankings[rank][0]:
            if pair != None:
                addpngxlabel(pair, ax, bases[i], 0.05)
            i += 1
    ax.set_xticklabels(timelabels)

    plt.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.2)

    plt.savefig("monthlystickeruse.png", format="png", dpi=256)
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
    dim = (img.size + img[0].size) / 2
    if dim > 230400:
        scale = scale * (230400 / dim)
    imagebox = OffsetImage(img, zoom=scale)
    imagebox.image.axes = ax
    ab = AnnotationBbox(imagebox, (xcoord, 0), xybox=(0, -16),
                    xycoords=("data", "axes fraction"),
                    boxcoords="offset points",
                    box_alignment=(.5, 1),
                    bboxprops={"edgecolor" : "none"})
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
    monthlystickeruse(td)
    #alltimestickers(td)
    #monthlyactivity(td)
    return

if __name__ == '__main__':
    main()
