#!/usr/bin/python

import sys

def convert_word (word):
    events=[]
    for letter in word.strip():
        events.append("EV_KEY:KEY_{}".format(letter.upper()))
    events.append("EV_KEY:KEY_ENTER")
    return ",".join(events)

for line in sys.stdin:
    num, word = line.split(" ", 1)
    events=convert_word(word)
    print("    {}: {}".format(events, 101-float(num.replace('.', ''))))
    
