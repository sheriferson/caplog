# -*- coding: utf-8 -*-

import argparse
import dateparser
from datetime import datetime
from os.path import expanduser, isfile
import json
import subprocess
import random
import re
import sys
from termcolor import colored
import time

# reference: http://stackoverflow.com/a/4028943
home = expanduser('~')
log_file_path = home + '/cap.log'

def grep_search_logs(search_string):
    entries = read_all_entries(log_file_path)

    results = filter(lambda entry:re.search(search_string, entry['entry']), entries)
    return(results)

def amend_last_entry(logmessage):
    entries = read_all_entries(log_file_path)

    entry = entries.pop(-1)
    entries.append({'timestamp':entry['timestamp'], 'entry':logmessage})

    save_updated_entries(entries)

def format_log_entry(jsonentry):
    logdate = from_unix_to_readable(jsonentry['timestamp'])
    formatted_entry = u'🚩 ' + '  ' + logdate + '  ' + jsonentry['entry']
    return(formatted_entry)

def from_unix_to_readable(unix_timestamp):
    return(datetime.fromtimestamp(unix_timestamp).strftime('%B %d %Y %H:%M'))

def read_all_entries(log_file_path):
    if not isfile(log_file_path):
        raise IOError('Log file not found.')

    try:
        with open(log_file_path, 'r') as logfile:
            entries = json.load(logfile)

        return(entries)
    except:
        raise RuntimeError('A problem occurred while parsing log file. File might be empty or corrupt.')

def save_updated_entries(entries):
    with open(log_file_path, 'w') as logfile:
        json.dump(entries, logfile)

def add_log_message(nowtime, logmessage, from_the_past = False):
    if logmessage != '':
        entries = read_all_entries(log_file_path)
        entries.append({'timestamp':nowtime, 'entry':logmessage})

        # if this is a log entry with a past date,
        # make sure you sort entries before saving them
        if from_the_past:
            # reference: http://stackoverflow.com/a/12039764
            entries.sort(key = lambda x: x['timestamp'])

        save_updated_entries(entries)

# reference: http://stackoverflow.com/a/136280
def show_log_tail(n = 3):
    entries = read_all_entries(log_file_path)

    for entry in entries[n*-1:]:
        print(format_log_entry(entry))

def show_random_log():
    entries = read_all_entries(log_file_path)

    print(format_log_entry(random.choice(entries)))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'I am the captain. This is my log. caplog keeps short simple logs.')

    # add a mutually exclusive group
    # user can do only one of the following:
    #   -a for amend
    #   -g for grep
    #   -l for list
    #   -r for random
    group = parser.add_mutually_exclusive_group()

    # -a amend last log entry
    group.add_argument('-a', '--amend', help = 'amend last log entry',
            nargs = '+',
            action = 'store')

    # -g show resulting entries for search term
    group.add_argument('-g', '--grep', help = 'search entries including term',
            nargs = '+',
            action = 'store')

    # -l show last n entries
    group.add_argument('-l', '--last', dest = 'nlogs', help = 'show last n entries, default if left empty is 3',
            nargs = '?',
            action = 'store',
            type = int)

    # -p enter log entry from and in the past
    group.add_argument('-p', '--past', help = 'enter a log entry from the past',
            nargs = '*',
            action = 'store')

    # -r show random log
    group.add_argument('-r', '--random', help = 'show a randomly chosen entry from logs',
            action = 'store_true')

    # optional log message
    parser.add_argument('logmessage', nargs = '*', type = str, help = 'The log message')

    args = parser.parse_args()

    # if user only enters $ caplog show default number of last entries
    if len(sys.argv) <= 1:
        show_log_tail()

    # if user specified the amend option, amend the last log entry
    elif args.amend:
        newlogmessage = ' '.join(args.amend)
        amend_last_entry(newlogmessage)

    # if user specified past date with the -p switch,
    # create the new date and prompt for an entry
    # if left empty, it cancels the operation
    elif args.past:
        past_date_term = ' '.join(args.past)
        past_date = dateparser.parse(past_date_term, settings = {'TIMEZONE': time.strftime('%Z')})

        if past_date is None:
            print("I couldn't parse the term you entered.")
            quit()

        past_date_timestamp = time.mktime(past_date.timetuple())

        print(colored('Logging an entry dated:' + '\t' +
                past_date.strftime('%B %d %Y %H:%M') + '\n' +
                'Leave empty to cancel.',
                'cyan'))
        past_message = input('> ')

        if past_message.strip() == '':
            print(colored('Cancelled.', 'red'))
        else:
            add_log_message(past_date_timestamp, past_message, from_the_past = True)

    # if user specified a number of last entries with $ caplog --last n, show last n logs
    elif args.nlogs:
        show_log_tail(args.nlogs)

    # if user specified $ caplog -g searchterm, show any results
    elif args.grep:
        search_term = ' '.join(args.grep)
        results = grep_search_logs(search_term)

        if results:
            for result in results:
                print(format_log_entry(result))

    # if user specified $ caplog -r or $ caplog --random, show random entry
    elif args.random:
        show_random_log()
    # otherwise, log the message the user entered
    else:
        if args.logmessage:
            nowtime = int(time.mktime(time.localtime()))
            logmessage = ' '.join(args.logmessage).strip()
            add_log_message(nowtime, logmessage)

