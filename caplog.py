# -*- coding: utf-8 -*-

import argparse
from datetime import datetime
from os.path import expanduser
import json
import subprocess
import random
import sys
import time

# reference: http://stackoverflow.com/a/4028943
home = expanduser("~")
log_file_path = home + '/cap.log'

def format_log_entry(jsonentry):
    logdate = from_unix_to_readable(jsonentry['timestamp'])
    formatted_entry = u'🚩 ' + '  ' + logdate + '  ' + jsonentry['entry']
    return(formatted_entry)


def from_unix_to_readable(unix_timestamp):
    return(datetime.fromtimestamp(unix_timestamp).strftime('%B %d %Y %H:%M'))

def read_all_entries(log_file_path):
    with open(log_file_path, 'r') as logfile:
        entries = json.load(logfile)

    return(entries)

def save_updated_entries(entries):
    with open(log_file_path, 'w') as logfile:
        json.dump(entries, logfile)

def add_log_message(nowtime, logmessage):
    if logmessage != "":
        entries = read_all_entries(log_file_path)
        entries.append({'timestamp':nowtime, 'entry':logmessage})

        save_updated_entries(entries)

# reference: http://stackoverflow.com/a/136280
def show_log_tail(n = 3):
    entries = read_all_entries(log_file_path)

    for entry in entries[n*-1:]:
        print(format_log_entry(entry))

def show_random_log():
    entries = read_all_entries(log_file_path)

    print(format_log_entry(random.choice(entries)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'I am the captain. This is my log. caplog keeps short simple logs.')

    # show last n entries
    parser.add_argument('-l', '--last', dest = 'nlogs', help = 'show last n entries, default if left empty is 3',
            nargs = '?',
            action = 'store',
            type = int)

    # show random log
    parser.add_argument("-r", "--random", help = "show a randomly chosen entry from logs",
            action = "store_true")

    # optional log message
    parser.add_argument("logmessage", nargs = '*', type = str, help = "The log message")

    args = parser.parse_args()

    # if user only enters $ caplog show default number of last entries
    if len(sys.argv) <= 1:
        show_log_tail()
    # if user specified $ caplog -r or $ caplog --random, show random entry
    elif args.random:
        show_random_log()
    # if user specified a number of last entries with $ caplog --last n, show last n logs
    elif args.nlogs:
        show_log_tail(args.nlogs)
    # otherwise, log the message the user entered
    else:
        if args.logmessage:
            nowtime = int(time.mktime(time.localtime()))
            logmessage = ' '.join(args.logmessage).strip()
            add_log_message(nowtime, logmessage)


