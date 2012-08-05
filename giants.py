#!/bin/env python
# Reads a csv file that contains the Giants schedule and converts it to a
# scheduling file for the Windows RadioShark application. This program creates
# Schedule.ini, which should be moved to:
#     c:\Documents and Settings\Administrator\Application Data\GriffinTechnology\RadioSHARK

# Globals {{{1
AudioDirectory = r'C:\Documents and Settings\Administrator\Desktop\audio'

# Imports {{{1
import time
import csv
import argparse
from textwrap import dedent
import sys, io

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
                start = time.mktime(
                    time.strptime(
                        '%s;%s' % (startDate, startTime)
                      , '%m/%d/%y;%I:%M %p'
                    )
                )
                now = int(time.time())
                if start < now:
                    continue
                month, day, year = startDate.split('/')
                games += [{
                    'desc': description
                  , 'start': int(start)
                  , 'duration': 240
                  , 'filename': '{year}{month}{day}-{desc}'.format(
                        desc = description.replace(' ', '-')
                      , year = year, month = month, day = day
                    )
                }]
        except csv.Error, err:
            sys.exit('%s,%d: %s' % (filename, reader.line_num, err))
except IOError, err:
    sys.exit('%s: %s.' % (err.filename, err.strerror))

# Write out Schedule.ini {{{1
try:
    with io.open('Schedule.ini', 'w', newline='\r\n') as output:
        for game in reversed(games):
            game['dir'] = AudioDirectory
            output.write(
                ur'SchedEvent: ("{desc}", {start}, -1, {duration}, 1, 0, AM, 680, 0, 1, " 64 kbps, 44 kHz, stereo CBR", 0, 3, "{dir}\{filename}.wma")'.format(**game) + '\n'
            )
        output.write(dedent(u'''\
            WindowPosition: ( 50, 50, 100, 100)
            RecWindowPosition: ( 54, 397, 608, 679)
            DrawerOpen: 1
            TimeShiftRecord: 1
            LargeGUI: 0
            ColumnWidths: (200, 100, 65, 150, 48, 38, 60, 200)
        '''))
except IOError, err:
    sys.exit('%s: %s.' % (err.filename, err.strerror))
