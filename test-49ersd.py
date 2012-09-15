#!/usr/bin/env python
# Creates a test ICS file that contains several events that record over the next
# few minutes. It then runs 49ersd.py to exercise it. This will create several
# test files in the destination directory. Once you are comfortable that every
# thing is working as expected, you should delete those files.

from __future__ import division
from datetime import datetime, timedelta
from fileutils import execute, ExecuteError
from textwrap import dedent
import sys

IcsHeader = dedent("""\
    BEGIN:VCALENDAR
    VERSION:2.0
    METHOD:PUBLISH

    X-WR-CALNAME:San Francisco 49ers Calendar (NFL)
    PRODID:-//sports.yahoo.com//San Francisco 49ers Calendar (NFL)//EN
""")
IcsBody = dedent("""\
    BEGIN:VEVENT
    DTSTART:{time}
    DTEND:20120909T232500Z
    SUMMARY:{game}
    UID:San Francisco 49ers Calendar (NFL)20120909009@sports.yahoo.com
    SEQUENCE:0
    COMMENT:Copyright 2012 (c) Yahoo!, Inc. All Rights Reserved.
    DESCRIPTION:TV: FOX
    DTSTAMP:20120909T160548Z
    END:VEVENT
""")
IcsFooter = dedent("""\
    END:VCALENDAR
""")

IcsFilename = 'test.ics'
Duration = 1 # minutes (must be integer)
Repetitions = 2

now = datetime.utcnow()
starts = []
for offset in range(Repetitions):
    startTime = now + timedelta(0, 60*Duration*(2*offset + 1))
    #starts += [startTime.astimezone(tz.timezone('UTC'))]
    starts += [startTime]
with open(IcsFilename, 'w') as icsFile:
    icsFile.write(IcsHeader)
    for start in starts:
        icsFile.write(
            IcsBody.format(
                time=start.strftime('%Y%m%dT%H%M%SZ'),
                game="test%s" % start.strftime('%M')))
    icsFile.write(IcsFooter)
try:
    execute('./49ersd.py --duration {} {}'.format(Duration/60, IcsFilename))
except ExecuteError, err:
    sys.exit(err.text)
except KeyboardInterrupt :
    exit('Killed by user')
