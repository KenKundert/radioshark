#!/usr/bin/env python
# Creates a test CSV file that contains several events that record over the next
# few minutes. It then runs giantsd.py to exercise it. This will create several
# test files in the destination directory. Once you are comfortable that every
# thing is working as expected, you should delete those files.

from __future__ import division
from datetime import datetime, timedelta
from fileutils import execute, ExecuteError
import sys

CsvHeader = ','.join([
    'START_DATE',
    'START_TIME',
    'START_TIME_ET',
    'SUBJECT',
    'LOCATION',
    'DESCRIPTION',
    'END_DATE',
    'END_DATE_ET',
    'END_TIME',
    'END_TIME_ET',
    'REMINDER_OFF',
    'REMINDER_ON',
    'REMINDER_DATE',
    'REMINDER_TIME',
    'REMINDER_TIME_ET',
    'SHOWTIMEAS_FREE',
    'SHOWTIMEAS_BUSY'
]) + '\n'
CsvBody = ','.join([
    '{date}',
    '{time}',
    '07:10 PM',
    '{game}',
    'Chase Field',
    '"Local TV: CSN-BA HD -- ESPN2 ----- Local Radio: KNBR 680"',
    '04/06/12',
    '04/06/12',
    '07:10 PM',
    '10:10 PM',
    'FALSE',
    'TRUE',
    '04/06/12',
    '03:10 PM',
    '06:10 PM',
    'FREE',
    'BUSY'
]) + '\n'
CsvFilename = 'test.csv'
Duration = 1 # minutes (must be integer)
Repetitions = 2

now = datetime.now()
starts = []
for offset in range(Repetitions):
    starts += [now + timedelta(0, 60*Duration*(2*offset + 1))]
with open(CsvFilename, 'w') as csvFile:
    csvFile.write(CsvHeader)
    for start in starts:
        csvFile.write(
            CsvBody.format(
                date=start.strftime('%m/%d/%y'),
                time=start.strftime('%I:%M %p'),
                game="test%s" % start.strftime('%M')))
try:
    execute('./giantsd.py --duration {} {}'.format(Duration/60, CsvFilename))
except ExecuteError, err:
    sys.exit(err.text)
except KeyboardInterrupt :
    exit('Killed by user')
