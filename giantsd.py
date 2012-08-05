#!/bin/env python
# The program acts like a daemon that reads a CSV file that contains the Giants
# schedule. It then goes to sleep until the start of the next game. At that time
# it wakes up and records the game. At the end of the game it goes to sleep and
# waits for the next game.

# Globals {{{1
AudioDirectory = '~/music/giants'
RecordingDuration = 4
Encoder = 'ogg' # choose from 'ogg' and 'mp3'
SharkAddress = 'hw:2,0'
# Use arecord -l to determine address.
# First number is card number, second is device number.


# Imports {{{1
import csv
import argparse
import time
import sched
from fileutils import makePath, expandPath, execute, ExecuteError, remove
import sys, io, os

# Read command line {{{1
clp = argparse.ArgumentParser(description="Giant's schedule translator")
clp.add_argument('csvfile', nargs=1, help="Giant's schedule as CSV file", action='store')
args = clp.parse_args()

# Read CSV file {{{1
games = []
try:
    with open(args.csvfile[0]) as csvFile:
        schedule = csv.DictReader(csvFile)
        try:
            for game in schedule:
                startDate = game['START_DATE']
                startTime = game['START_TIME']
                description = game['SUBJECT']
                media = game['DESCRIPTION']
                tstart = time.strptime(
                    '%s;%s' % (startDate, startTime)
                  , '%m/%d/%y;%I:%M %p'
                )
                start = time.mktime(tstart)
                now = int(time.time())
                if start < now:
                    continue
                month, day, year = startDate.split('/')
                games += [{
                    'desc': description
                  , 'start': int(start)
                  , 'filename': '{year}{month}{day}-{desc}'.format(
                        desc = description.replace(' ', '-')
                      , year = year, month = month, day = day
                    )
                  , 'date': time.strftime("%0d %B %Y", tstart)
                  , 'time': startTime
                  , 'media': media
                }]
        except csv.Error, err:
            sys.exit('%s,%d: %s' % (filename, reader.line_num, err))
except IOError, err:
    sys.exit('%s: %s.' % (err.filename, err.strerror))

# Record a game {{{1
def record(game, nextGame):
    filename = makePath(
        expandPath(AudioDirectory)
      , '.'.join([game['filename'], Encoder])
    )
    latest =  makePath(expandPath(AudioDirectory), 'latest.ogg')
    # build the commands
    recorder = 'arecord -q -d {duration} -c 2 -f S16 -r 44100 -D {device}'.format(
        duration = 1.1829*3600*RecordingDuration, device = SharkAddress
        # for reasons I do not understand arecord always records less time than
        # I ask for. The factor of 1.1829 compensates for this.
    )

    if Encoder == 'ogg':
        encoder = ' '.join([
            'oggenc'
          , '-Q'                         # quiet
          , '--resample 8000'            # sample rate (8000 and 11025 are suitable choices for AM radio)
          , '--downmix'                  # convert from stereo to mono
          , '-q 0'                       # quality level (range is -1 to 10 with 10 being highest)
          , '-o {filename}'              # output file name
          , '--title "{title} ({date})"' # title
          , '--album "{title}"'          # album
          , '--artist "{artist}"'        # artist
          , '--date "{date}"'            # date
          , '-'                          # read from standard input
        ]).format(
            filename = filename
          , title = game['desc']
          , artist = 'The Giants'
          , date = game['date']
        )
    elif Encoder == 'mp3':
        # Still not happy with the lame options. The ones below provide a
        # reasonable filesize, but the recording sounds very tinny, removing the
        # results in a nice sounding recording, but the files are a factor of
        # two too large.
        encoder = ' '.join([
            'lame'
          , '--quiet'               # quiet
          , '--resample 8'          # resample to rate
          , '-V3'                   # ???
          , '--vbr-new'             # ???
          , '-q0'                   # quality level
          , '-B16'                  # maximum bit rate
          , '--lowpass 15.4'        # apply lowpass filter
          , '--athaa-sensitivity 1' # ???
          , '--tt "{title}"'        # title
          , '--ta "{artist}"'       # artist
          , '-'                     # read from standard input
          , '{filename}'            # write to filename
        ]).format(
            filename = filename
          , title = game['desc']
          , artist = 'Giants'
          , date = game['date']
        )
    else:
        raise AssertionError, "%s: Unknown encoder" % encoder

    pipeline = '{recorder} | {encoder}'.format(
        recorder=recorder, encoder=encoder
    )

    # create a symbolic link to the latest game
    remove(latest)
    os.symlink(filename, latest)

    try:
        # Turn the fin red to indicate recording
        execute('sharkctrl -blue 0')
        execute('sharkctrl -red 1')

        # Record the game
        print 'Recording {desc} ({date}).'.format(**game)
        execute(pipeline)
        print 'Recording complete.'

        # Turn the fin back to blue to indicate not recording
        execute('sharkctrl -red 0')
        execute('sharkctrl -blue 63')
    except ExecuteError, err:
        sys.exit(err.text)
    announceNextGame(nextGame)

# Announce next game {{{1
def announceNextGame(nextGame):
    if nextGame:
        print 'Next up:'
        print '    {desc}'.format(**nextGame)
        print '    {date}, {time}'.format(**nextGame)
        if nextGame['media']:
            print '    {media}'.format(**nextGame)
    else:
        print 'No more games scheduled.'

# Schedule all of the games {{{1
scheduler = sched.scheduler(time.time, time.sleep)
nextGame = None
for game in reversed(games):
    scheduler.enterabs(game['start'], 1, record, (game,nextGame))
    nextGame = game

announceNextGame(nextGame)
try:
    scheduler.run()
except KeyboardInterrupt:
    execute('sharkctrl -red 0')
    execute('sharkctrl -blue 63')
    print "Killed at user request."
