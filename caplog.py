# -*- coding: utf-8 -*-

from datetime import datetime
from os.path import expanduser
import subprocess
import sys
import time

# reference: http://stackoverflow.com/a/4028943
home = expanduser("~")
log_file_path = home + '/cap.log'

def from_unix_to_readable(unix_timestamp):
    return(datetime.fromtimestamp(unix_timestamp).strftime('%B %d %Y %H:%M'))

def add_log_message(logmessage):
    with open(log_file_path) as logfile:
       logfile.write(logmessage) 
       logfile.write('\n')

    logfile.close()

# reference: http://stackoverflow.com/a/136280
def show_log_tail(n = 3):
    loglines = subprocess.check_output(["tail", "-n", str(n), log_file_path])
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


