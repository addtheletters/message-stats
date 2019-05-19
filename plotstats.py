#!./venv/bin/python3

# graph results of facebook messenger chat history analysis

import messages as msgs
import sys, unicodedata
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.offsetbox import OffsetImage, AnnotationBbox, TextArea
from matplotlib.patches import Rectangle
from datetime import datetime
from random import randrange, random

#from spellchecker import SpellChecker
#SPELLCHECKER = SpellChecker(distance=1)

STANDARD_STICKER_SIZE = 230400
DIAG_LABEL_FONT_SIZE = 4

COLOR_CHOICES = ["red", "blue", "green", "magenta", "orange", "cyan", "purple"]
DOMAIN_COLORS = {
    "www.reddit.com":"orange",
    "i.redd.it":"peachpuff",
    "twitter.com":"skyblue",
    "www.youtube.com":"indianred",
    "www.facebook.com":"navy",
    "imgur.com":"gray",
    "i.imgur.com":"lightslategrey",
    "clips.twitch.tv":"purple",
}

#print(fm.findSystemFonts(fontpaths=None, fontext='ttf'))
EMOJI_FONT_FILE = "/mnt/c/Windows/Fonts/seguiemj.ttf"
emoji_font = fm.FontProperties(fname=EMOJI_FONT_FILE, size=DIAG_LABEL_FONT_SIZE)


def test_plot(td):
    plt.figure(figsize=(6, 4))
    plt.savefig("test.png", format="png", dpi=256)
    return

# places random stickers, chosen at probabilities respecting their all-time usage
def sticker_spam(td, xsize=4, ysize=3, times=1500):
    plt.figure(figsize=(xsize, ysize))
    plt.title("uh stickers I guess")

    xv = [i for i in range(xsize)]
    yv = [i for i in range(ysize)]

    stickers = td.alltime().allcount["sticker_use"].most_common()
    stktotal = td.alltime().allcount["sticker"]

    def randsticker(stkrs):
        choice = randrange(0, stktotal-1)
        ind = 0
        while choice >= 0 and ind < len(stkrs):
            if choice < stkrs[ind][1]:
                return stkrs[ind][0]
            choice -= stkrs[ind][1]
            ind += 1
        return stkrs[ind-1][0]

    i = 0
    while i < times:
        rx = random()
        ry = random() + 0.15
        add_png_xlabel(randsticker(stickers), plt.gca(), rx, scale=0.06, ycoord=ry)
        i += 1

    plt.savefig("stickerspam.png", format="png", dpi=256)
    return

def sticker_similarity(td, mincount=2):
    ss = msgs.sticker_similarity(td.alltime(), mincount=mincount, excludeself=True)
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

# choose a random color from choices, or generate a random one. don't repeat a choice
def randcolor(previous=[]):
    choices = COLOR_CHOICES[:]
    for c in previous:
        if c in choices:
            choices.remove(c)
    if len(choices) == 0:
        return (random(), random(), random(), 1)
    return choices[randrange(len(choices))]

# reject if name is too short
def minlength_filter(minlength):
    return (lambda x : (len(x[0]) >= minlength), "min-length {}".format(minlength))

# # reject if word is spelled correctly
# def spelling_filter():
#     return (lambda x : len(SPELLCHECKER.known([x[0]])) != 1, "misspelled")

def by_period_use(td, countkey, usekey, usefilter=None, num=5, width=0.37, imglabel=False, size=(9,4), showemoji=False, outliermark=300):
    periodstr = td.period.describe()

    # most used in each time period; exclude no-use time ranges
    times = [dt for dt in td.getallkeys() if td.trcounts[dt].allcount[countkey] != 0]
    timelabels = [dt.strftime(td.period.formats()) for dt in times]

    rankings = []
    for i in range(num):
        rankings.append(([], [])) #(uris, counts)

    outliers = []

    for dt in times:
        items = td.trcounts[dt].allcount[usekey].most_common()
        if usefilter:
            items = list(filter(usefilter[0], items))
        items = items[:num]

        for i in range(num):
            if i < len(items):
                rankings[i][0].append(items[i][0])
                rankings[i][1].append(items[i][1])
                if rankings[i][1][-1] > outliermark:
                    outliers.append((items[i][0], times.index(dt), items[i][1]))
                    rankings[i][1][-1] = outliermark
            else:
                rankings[i][0].append(None)
                rankings[i][1].append(0)
    
    plt.figure(figsize=size)
    plt.title("{} most-used {}".format(periodstr.capitalize(), countkey) 
        + ("s" if countkey[-1] not in "is" else "") 
        + ((" (" + usefilter[1] + ")") if usefilter else ""))
    plt.ylabel("uses")
    ax = plt.gca()
    ax.tick_params(labelsize=3)

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
                if rank[0][ri] in DOMAIN_COLORS.keys():
                    colors[rank[0][ri]] = DOMAIN_COLORS[rank[0][ri]]
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
        for dti in range(len(rankings[rank][0])):
            pair = rankings[rank][0][dti]
            if pair != None:
                if imglabel:
                    add_png_xlabel(pair, ax, bases[i], 0.05)
                else:
                    text = pair
                    if showemoji:
                        if len(pair) == 1 or len(pair) == 2:
                            try:
                                text = unicodedata.name(pair[0])
                                if len(pair) == 2:
                                    l2 = unicodedata.name(pair[1])
                                    text = text + " + " + l2[-1]
                            except ValueError as e:
                                text = "unknown (" + repr(bytes(pair, encoding="utf-8")) + ")"
                            text = text + " > " + pair
                    for outlier in outliers:
                        if pair == outlier[0] and dti == outlier[1]:
                            text = "(outlier {} > {}) ".format(outlier[2], outliermark) + text
                            break
                    if showemoji:
                        add_text_xlabel(text, ax, bases[i], rotate=45, fontprops=emoji_font)
                    else:
                        add_text_xlabel(text, ax, bases[i], rotate=45)
            i += 1

    ax.set_xticklabels(timelabels)

    plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.20)

    plt.savefig("{}{}use.png".format(periodstr, countkey), format="png", dpi=256)
    return

def sticker_use(td):
    by_period_use(td, "sticker", "sticker_use", imglabel=True, size=(50,5))
    return

def link_use(td):
    by_period_use(td, "share", "share_use", num=3, imglabel=False, size=(40,5))
    return

def emoji_use(td):
    matplotlib.rc('font', family='DejaVu Sans')
    by_period_use(td, "emoji", "emoji_use", num=3, imglabel=False, size=(40,5), showemoji=True)
    return

def words_use(td):
    by_period_use(td, "words", "words_use", num=5, usefilter=minlength_filter(5), size=(15, 5), outliermark=2200, showemoji=True)
    return

def personal_reacts_given_density(td):
    # exclude periods before reacts existed
    times = [dt for dt in td.getallkeys() if td.trcounts[dt].allcount["reacts_received_total"] != 0]
    timelabels = [dt.strftime(td.period.formats()) for dt in times]

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
                personal_reacts[name][i] = td.trcounts[dt].percount[name]["reacts_given"]

    personal_density = {}
    for name in personal_reacts:
        personal_density[name] = [personal_reacts[name][i] / activity[i] for i in range(len(times))]

    plt.figure(figsize=(9, 4))
    plt.title("Reacts-given Density")
    plt.ylabel("user's reacts / all messages")
    ax = plt.gca()
    ax.tick_params(labelsize=4)

    add_bar_stack(timelabels, names, personal_density)

    plt.savefig("{}reactgivendensity.png".format(td.period.describe()), format="png", dpi=200)
    return

def reacts_received_density(td):
    # exclude periods before reacts existed
    times = [dt for dt in td.getallkeys() if td.trcounts[dt].allcount["reacts_received_total"] != 0]
    timelabels = [dt.strftime(td.period.formats()) for dt in times]

    activity = []
    reacts = []
    for dt in times:
        activity.append(td.trcounts[dt].allcount["msg"])
        reacts.append(td.trcounts[dt].allcount["reacts_received_total"])

    density = [reacts[i] / activity[i] for i in range(len(activity))]

    plt.figure(figsize=(9, 4))
    plt.title("{} react density".format(td.period.describe().capitalize()))
    plt.ylabel("reacts / messages")
    ax = plt.gca()
    ax.tick_params(labelsize=4)

    plt.bar(timelabels, density)

    plt.savefig("{}reactdensity.png".format(td.period.describe()), format="png", dpi=200)
    return

def activity(td): # by-time-period distribution
    times = td.getallkeys()
    timelabels = [dt.strftime(td.period.formats()) for dt in times]

    names = []
    personal_activity = {}
    for name, pcount in td.alltime().percount.items():
        names.append(name)
        personal_activity[name] = [0] * len(timelabels)
    
    for i in range(len(times)):
        dt = times[i]
        for name in names:
            if name in td.trcounts[dt].percount:
                personal_activity[name][i] = td.trcounts[dt].percount[name]["msg"]
            else:
                personal_activity[name][i] = 0

    plt.figure(figsize=(9, 4))
    plt.title("{} activity".format(td.period.describe().capitalize()))
    plt.ylabel("messages sent")
    ax = plt.gca()
    ax.tick_params(labelsize=4)

    add_bar_stack(timelabels, names, personal_activity)

    plt.savefig("{}activity.png".format(td.period.describe()), format="png", dpi=200)
    return

def all_time_stickers(td, num=15):
    allt = td.alltime()
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

    plt.figure(figsize=(9, 4))
    plt.ylabel("Uses")
    plt.title("Most common stickers ({})".format(allt.rangestr()))
    plt.xticks(rank)

    add_bar_stack(rank, names, personal_use)

    # show stickers as x-axis labels
    ax = plt.gca()
    for i in range(len(stickfiles)):
        add_png_xlabel(stickfiles[i], ax, i+1, scale=0.05)

    plt.savefig("alltimestickers.png", format="png", dpi=256)
    return

def add_png_xlabel(filename, ax, xcoord, scale=0.02, ycoord=0):
    img = plt.imread(filename, format='png')
    # scale large stickers to roughly match the standard
    dim = (img.size + img[0].size) / 2
    if dim > STANDARD_STICKER_SIZE:
        scale = scale * (STANDARD_STICKER_SIZE / dim)
    imagebox = OffsetImage(img, zoom=scale)
    imagebox.image.axes = ax
    ab = AnnotationBbox(imagebox, (xcoord, ycoord), xybox=(0, -16),
                    xycoords=("data", "axes fraction"),
                    boxcoords="offset points",
                    box_alignment=(.5, 1),
                    bboxprops={"edgecolor":"none", "alpha":0})
    ax.add_artist(ab)
    return

def add_text_xlabel(txt, ax, xcoord, rotate=45, yoffset=-15, fontprops=fm.FontProperties(size=DIAG_LABEL_FONT_SIZE)):
    textbox = TextArea(txt, textprops={
        #"fontsize":size,
        "FontProperties":fontprops,
        "rotation":rotate,
        "ha":"right",
        "rotation_mode":"anchor",
        "fontstretch":"ultra-condensed"
        })
    ab = AnnotationBbox(textbox, (xcoord, 0), xybox=(0, yoffset),
                    xycoords=("data", "axes fraction"),
                    boxcoords="offset points",
                    box_alignment=(0, 0),
                    bboxprops={"edgecolor":"none", "alpha":0})
    ax.add_artist(ab)
    return

def add_bar_stack(xitems, names, personal, width=0.5):
    bars = []
    top = [0] * len(xitems)
    for i in range(len(names)):
        name = names[i]
        bars.append(plt.bar(xitems, personal[name], width=width, bottom=top))
        top = [top[j] + personal[name][j] for j in range(len(xitems))]
    plt.legend(bars, names, fontsize="small")

def main():
    analysisfile = sys.argv[1] if len(sys.argv) > 1 else msgs.TEST_SAVE

    print("loading analysis from {}".format(analysisfile))
    td = msgs.loadjson(analysisfile)

    print("analysis loaded, plotting...")

    test_plot(td)
    #sticker_spam(td)
    #sticker_similarity(td)
    #personal_reacts_given_density(td)
    #reacts_received_density(td)
    sticker_use(td)
    #link_use(td)
    #emoji_use(td)
    #words_use(td)
    #activity(td)
    #all_time_stickers(td)

    print("done plotting.")

    return

if __name__ == '__main__':
    main()
