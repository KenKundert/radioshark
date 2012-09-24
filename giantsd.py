#!/bin/env python
# The program acts like a daemon that reads a CSV file that contains the Giants
# schedule. It then goes to sleep until the start of the next game. At that time
# it wakes up and records the game. At the end of the game it goes to sleep and
# waits for the next game.

# Imports {{{1
from fins import fins
import csv
import argparse
import time
import sched
from fileutils import makePath, expandPath, execute, ExecuteError, remove, mkdir
import sys, io, os

# Configuration {{{1
Station = '-am 680'
RecordingDuration = 4
AudioDirectory = '~/music/giants'
Encoder = 'ogg' # choose from 'ogg', 'mp3', 'spx'
Fin = 'baseball'
SharkAudioAddr = fins[Fin].audioAddr
SharkCtrlAddr = fins[Fin].ctrlAddr

# Read command line {{{1
clp = argparse.ArgumentParser(description="Giant's recording daemon")
clp.add_argument('csvfile', nargs=1, help="Giant's schedule as CSV file", action='store')
clp.add_argument('--duration', '-d', nargs=1, help="duration of recording in hours", action='store')
args = clp.parse_args()
if args.duration:
    RecordingDuration = float(args.duration[0])

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
                  , 'day': time.strftime("%A", tstart)
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
    recorder = ' '.join([
        'arecord'                        # audio recorder
      , '-q'                             # quiet
      , '-d {duration}'                  # recording time
      , '--max-file-time {duration}'     # recording time before switching files (must be >= recording time)
      , '-c 2'                           # input stream is 2 channels
      , '-f S16'                         # input stream is 16 bit signed
      , '-r 44100'                       # rate of input stream is 44.1kHz
      , '-D {device}'                    # audio generator
      , '-t raw'                         # output format is raw (don't use .wav, it cuts out after 3 hours and 22 minutes because of a size limit on .wav files)
    ]).format(
        duration = 3600*RecordingDuration, device = SharkAudioAddr
    )

    if Encoder == 'ogg':
        encoder = ' '.join([
            'oggenc'                     # Ogg encoder
          , '-Q'                         # quiet
          , '-r'                         # input format is raw
          , '--resample 8000'            # sample rate (8000 and 11025 are suitable choices for AM radio)
          , '--downmix'                  # convert from stereo to mono
          , '-q 0'                       # quality level (range is -1 to 10 with 10 being highest)
          , '--ignorelength'             # Allow input stream to exceed 4GB
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
          , artist = 'The Giants'
          , date = game['date']
        )
    elif Encoder == 'spx':
        # This generates files that sound a little better than the ogg files but
        # are much larger (odd because it is based on ogg and it tailored for
        # the spoken word, perhaps it is because I cannot get the -vbr option to
        # work). I am using the wideband option because it sounded
        # better and took less space than the narrowband option.
        encoder = ' '.join([
            'speexenc'
          , '-w'                    # wideband
          #, '--16bit'              # 16 bit raw input stream
          #, '--le'                 # little endian input stream
          #, '--stereo'             # stereo input stream
          , '--title "{title}"'     # title
          , '--author "{artist}"'   # artist
          , '-'                     # read from standard input
          , '{filename}'            # write to filename
        ]).format(
            filename = filename
          , title = game['desc']
          , artist = 'The Giants'
          , date = game['date']
        )
    else:
        raise AssertionError, "%s: Unknown encoder" % encoder

    pipeline = '{recorder} | {encoder}'.format(
        recorder=recorder, encoder=encoder
    )

    # assure destination directory exists
    mkdir(expandPath(AudioDirectory))

    # create a symbolic link to the latest game
    remove(latest)
    try:
        os.symlink(filename, latest)
    except (IOError, OSError), err:
        sys.exit("%s: %s." % (err.filename, err.strerror))

    try:
        # Configure the shark (set station, turn fin red to indicate recording)
        execute('sharkctrl %s %s' % (Station, SharkCtrlAddr))
        execute('sharkctrl -blue 0 %s' % SharkCtrlAddr)
        execute('sharkctrl -red 1 %s' % SharkCtrlAddr)

        # Record the game
        print 'Recording {desc} ({date}).'.format(**game)
        execute(pipeline)
        print 'Recording complete.'

        # Turn the fin back to blue to indicate not recording
        execute('sharkctrl -red 0 %s' % SharkCtrlAddr)
        execute('sharkctrl -blue 63 %s' % SharkCtrlAddr)
    except ExecuteError, err:
        sys.exit(err.text)
    announceNextGame(nextGame)

# Announce next game {{{1
def announceNextGame(nextGame):
    if nextGame:
        print 'Next up for the Giants:'
        print '    {desc}'.format(**nextGame)
        print '    {day}, {date}, {time}'.format(**nextGame)
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
    execute('sharkctrl -red 0 %s' % SharkCtrlAddr)
    execute('sharkctrl -blue 63 %s' % SharkCtrlAddr)
    print "Killed at user request."
