# message-stats

Do you like data? Looking at graphs? Have you waited the several-hours needed to download your Facebook Messenger chat history and wondered why you even bothered? Oh, do I ever have the scripts for you.

- `messages.py` provides functions to load the chat history JSON file and count messages, words, emoji, stickers, photos, reacts, and links shared. Global totals are kept, as well as totals for each chat participant and for each section of a specified time period. These counts themselves can be saved in JSON format.

- `plotstats.py` provides functions to draw graphs based on the counts using matplotlib. 

depends on

- [matplotlib](https://matplotlib.org/)

- [numpy](https://www.numpy.org/)
