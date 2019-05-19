# message-stats

Do you like data? Looking at graphs? Have you waited the several-hours needed to download your Facebook Messenger chat history and wondered why you even bothered? Oh, do I ever have the Python scripts for you.

- `messages.py` provides functions to load the chat history JSON file and count messages, words, emoji, stickers, photos, reacts, and links shared. Global totals are kept, as well as totals for each chat participant and every slice of time (length configurable). These counts themselves can be saved in JSON format. 
    - Usage as command: `./messages.py [history_json_filename] [analysis_out_filename]`

- `plotstats.py` provides functions to draw graphs based on the counts using matplotlib. 
    - Usage as command: `./plotstats.py [analysis_filename]`

depends on

- [matplotlib](https://matplotlib.org/)

- [numpy](https://www.numpy.org/)
