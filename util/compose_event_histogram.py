#!/usr/bin/python

import sys, re

def convert_word (word):
    events=[]
    for letter in word.strip():
        events.append("EV_KEY:KEY_{}".format(letter.upper()))
    events.append("EV_KEY:KEY_ENTER")
    return ",".join(events)

hist = {}
for line in sys.stdin:
    line = re.sub("[,.?!:']", "", line)
    for w in line.split(" "):
        word = w.strip().lower()
        if not word:
            continue
        if not word in hist:
            hist[word] = 1
        else:
            hist[word] +=1

for word, num in sorted([(k, v) for k, v in hist.items()], reverse=True):
    events=convert_word(word)
    print("    {}: {}".format(events, num))
    
