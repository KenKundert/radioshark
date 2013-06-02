#!/usr/bin/env python

from fins import fins
from fileutils import execute, ExecuteError
from textwrap import dedent, fill
from time import sleep
from itertools import product

# Globals
audioAddrs = []
ctrlAddrs = []
pipeline = "arecord -c 2 -f S16 -r 44100 -d 10 -D %s -t raw -q | aplay -c 2 -f S16 -r 44100 -t raw"

for fin in fins.itervalues():
    audioAddrs += [fin.audioAddr]
    ctrlAddrs += [fin.ctrlAddr]

def verifAddrs(finName):
    fin = fins[finName]
    audioAddr = fin.audioAddr
    ctrlAddr = fin.ctrlAddr

    print "Using %s fin (audioAddr='%s', ctrlAddr='%s').\n" % (
        finName, fin.audioAddr, fin.ctrlAddr
    )
    print fill(dedent("""\
        This fin is about to be tested. This will reset the station on both fins.
        Do not do this if you are already recording a program on the other fin.
        You have 10 seconds to kill me to avoid changing the station.
    """))
    for i in range(9, -1, -1):
        sleep(1)
        print i
    sleep(1)

    print fill(dedent("""\
        This test sets both fins to KFOG (97.7 FM), a music station. It then
        sets the fin that is to be used to KNBR (680 AM), a sports talk station
        and then to KQED (88.5 FM), which is NPR. Each has its own distinct
        sound that should be distinguishable.  You should hear 10 seconds of
        sports talk and then 10 seconds of NPR. If you do not, then there are
        errors in the addresses and you need to fix fins.py.
    """))

    try:
        for audioAddr, ctrlAddr in product(audioAddrs, ctrlAddrs):
            for addr in ctrlAddrs:
                execute('sharkctrl -fm 97.7 %s' % addr)

        print "ctrl addr:", ctrlAddr
        print "audio addr:", audioAddr
        print "station: KNBR 680 AM"
        execute('sharkctrl -am 680 %s' % ctrlAddr)
        execute('sharkctrl -blue 0 %s' % ctrlAddr)
        execute('sharkctrl -red 1 %s' % ctrlAddr)
        execute(pipeline % audioAddr)
        print "station: KQED 88.5 FM"
        execute('sharkctrl -fm 88.5 %s' % ctrlAddr)
        execute('sharkctrl -blue 63 %s' % ctrlAddr)
        execute('sharkctrl -red 1 %s' % ctrlAddr)
        execute(pipeline % audioAddr)
        execute('sharkctrl -red 0 %s' % ctrlAddr)
        execute('sharkctrl -blue 63 %s' % ctrlAddr)
    except ExecuteError, err:
        exit(err.text)

if __name__ == "__main__":
    try:
        verifAddrs('football')
    except KeyboardInterrupt:
        execute('sharkctrl -red 0 %s' % ctrlAddr)
        execute('sharkctrl -blue 63 %s' % ctrlAddr)
        print "Killed at user request."
    except ExecuteError, err:
        exit(err.text)
