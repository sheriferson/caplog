from datetime import datetime
import sys
import time

nowtime = int(time.mktime(time.localtime()))
arguments = sys.argv

if len(arguments) > 1: arguments.pop(0)

status = ' '.join(arguments)
logmessage = str(nowtime) + ',' + status

def from_unix_to_readable(unix_timestamp):
    return(datetime.fromtimestamp(unix_timestamp).strftime('%B %d, %Y %H:%M:%S'))

with open('mylog.txt', 'a') as logfile:
   logfile.write(logmessage) 
   logfile.write('\n')

logfile.close()
