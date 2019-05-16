#!/usr/bin/python3

# graph results of facebook messenger chat history analysis

import messages as msgs
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

def testplot(td):
    num = 15

    allt = td.alltime()
    msgs.printstickers(allt.allcount, num)
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

    bars = []
    top = [0] * len(rank)
    for i in range(len(names)):
        name = names[i]
        print("bar for " + name)
        bars.append(plt.bar(rank, personal_use[name], width=0.5, bottom=top))
        top = [top[i] + personal_use[name][i] for i in range(len(rank))]

    plt.ylabel("Uses")
    plt.title("Most common stickers ({})".format(allt.rangestr()))
    plt.xticks(rank)

    ax = plt.gca()

    for i in range(len(sticks)):
        addpngxlabel(sticks[i][0], ax, i+1, 0.05)

    plt.legend(bars, names)

    plt.show()
    plt.savefig("test.png", format="png", dpi=256)
    return
   
def alltimestickers(td, num=30):
    allt = td.alltime()

    sticks = allt.allcount["sticker_use"].most_common()[:num]

    rank = [i+1 for i in range(len(sticks))]
    count = [s[1] for s in sticks]

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.bar(rank, count)
    ax.set_ylabel("Uses")
    ax.set_title("Most common stickers ({})".format(allt.rangestr()))
    ax.set_xticks(rank)
    ax.set_xticklabels(rank)

    for i in range(len(sticks)):
        addpngxlabel(sticks[i][0], ax, i+1, 0.05)

    plt.show()
    plt.savefig("alltimestickers.png", format="png", dpi=256)
    return

def addpngxlabel(filename, ax, xcoord, scale=0.02):
    img = plt.imread(filename, format='png')
    imagebox = OffsetImage(img, zoom=scale)
    imagebox.image.axes = ax
    ab = AnnotationBbox(imagebox, (xcoord, 0), xybox=(0, -6),
                    xycoords=("data", "axes fraction"),
                    boxcoords="offset points",
                    box_alignment=(.5, 1),
                    bboxprops={"edgecolor" : "none"})
    ax.add_artist(ab)
    return

def main():
    bjork = msgs.loadjson("bjork_message.json")
    td = msgs.analyze(bjork, msgs.TimePeriod.MONTH)

    print("analysis done, plotting...")

    testplot(td)
    #alltimestickers(td)
    return

if __name__ == '__main__':
    main()
