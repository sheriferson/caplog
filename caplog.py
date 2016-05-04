# -*- coding: utf-8 -*-

from datetime import datetime
import subprocess
import sys
import time

def from_unix_to_readable(unix_timestamp):
    return(datetime.fromtimestamp(unix_timestamp).strftime('%B %d %Y %H:%M'))

def add_log_message(logmessage):
    with open('cap.log', 'a') as logfile:
       logfile.write(logmessage) 
       logfile.write('\n')

    logfile.close()

# reference: http://stackoverflow.com/a/136280
def show_log_tail(n = 3):
    loglines = subprocess.check_output(["tail", "-n", str(n), "cap.log"])
    loglines = loglines.decode('utf-8').split('\n')
    for line in loglines:
        if line != '':
            logdate, logmsg = line.split(',')
            logdate = from_unix_to_readable(float(logdate))
            formatted_log = u'🚩 ' + '  ' + logdate + '  ' + logmsg
            print(formatted_log)

arguments = sys.argv

if len(arguments) > 1:
    nowtime = int(time.mktime(time.localtime()))
    arguments.pop(0)
    status = ' '.join(arguments)
    logmessage = str(nowtime) + ',' + status
    add_log_message(logmessage)
else:
    show_log_tail()


