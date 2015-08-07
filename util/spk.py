#!/usr/bin/python

import sys
import fcntl
import os
import termios
import string

from select import select
from time import time, sleep

import speechd
client = speechd.SSIPClient('me')
client.set_output_module('festival')
#print "modules",client.list_output_modules()
#print "voices",client.list_synthesis_voices()
client.set_language('en')
#client.set_synthesis_voice('cstr_upc_upm_spanish_hts')
client.set_punctuation(speechd.PunctuationMode.SOME)

def getch(timeout = 0):
    fd = sys.stdin.fileno()

    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)

    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
    if timeout:
        time_end = time() + timeout
    try:
        while 1:            
            try:
                c = sys.stdin.read(1)
                break
            except IOError: pass
            sleep(0.05)
            if timeout and time() >= time_end:
                break
    except:
        raise
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
    return c

retries = 300
text = ""
try:
    while retries:

        new_text = getch()
        if new_text in string.printable:
            sys.stdout.write(new_text)
        elif ord(new_text) in (8, 127):
            sys.stdout.write("\b \b")
            text = text[:-1]
            new_text=""
            
        if new_text:
            if ord(new_text) in (10, 13):
                new_text = "\n"
            text += new_text
            try: ready = text.index("\n")
            except ValueError: continue
            #print
            #print "habla", text
            client.speak(text[0:ready])
            text = text[ready+1:]
        sleep(0.1)
        retries -= 1
except KeyboardInterrupt:
    pass
finally:
    print("Exiting...")
    client.close()
        
