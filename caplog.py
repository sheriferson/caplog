# -*- coding: utf-8 -*-

import argparse
import dateparser
from os.path import expanduser, isfile
import sqlite3
import subprocess
import random
import re
import sys
from termcolor import colored
import time

# reference: http://stackoverflow.com/a/4028943
home = expanduser('~')
log_file_path = home + '/caplog.db'

def add_to_the_past(past_date_term):
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
        add_log_message(past_message, past_date_timestamp)

def grep_search_logs(search_string):
    results = read_entries(log_file_path, search_term = search_string)
    return(results)

def amend_last_entry(logmessage):
    # 1. get last entry
    # 2. use the timestamp as the lookup value
    # 3. update row

    if logmessage != '':
        conn = sqlite3.connect(log_file_path)
        c = conn.cursor()
        c.execute("select * from logs order by timestamp desc limit 1")
        lastrow = c.fetchall()
        lasttime = lastrow[0][0]

        c.execute("update logs set entry=('{logentry}') where timestamp=({time})".format(logentry = logmessage, time = lasttime))
        conn.commit()
        conn.close()

def delete_last_entry():
    # connect to db
    # delete last row in table logs

    print(colored('Are you sure you want to delete the last entry? Y/n', 'red'))
    confirm_delete = input('> ')

    if confirm_delete.lower() == 'y':
        conn = sqlite3.connect(log_file_path)
        c = conn.cursor()
        c.execute('delete from logs where timestamp = (select max(timestamp) from logs);')
        conn.commit()
        conn.close()
        print(colored('Last entry deleted.', 'cyan'))

def format_log_entry(sql_row):
    formatted_entry = u'🚩 ' + '  ' + sql_row[0] + '  ' + sql_row[1]
    return(formatted_entry)

def read_entries(log_file_path, n = 0, search_term = "", random = False):
    if not isfile(log_file_path):
        print('No log file found. Creating file...')
        conn = sqlite3.connect(log_file_path)
        c = conn.cursor()
        c.execute('create table logs (timestamp TIMESTAMP, entry TEXT)')
        c.execute('create table console (log_timestamp TIMESTAMP, entry_timestamp TIMESTAMP)')
        c.execute('''create trigger logging
                after insert on logs
                begin
                    insert into console (log_timestamp, entry_timestamp) values (strftime('%s', 'now'), new.timestamp);
                end
                ;''')
        conn.commit()
        conn.close()
        print('New log file created at {logfile}'.format(logfile = log_file_path))

    else:
        try:
            conn = sqlite3.connect(log_file_path)
            c = conn.cursor()
            if n > 0:
                c.execute("select datetime(timestamp, 'unixepoch', 'localtime'), entry from logs order by timestamp desc limit {n};".format(n = n))
            elif search_term != "":
                c.execute("select datetime(timestamp, 'unixepoch', 'localtime'), entry from logs where entry like '%{searchterm}%' order by timestamp".format(searchterm = search_term))
            elif random == True:
                c.execute("select datetime(timestamp, 'unixepoch', 'localtime'), entry from logs order by Random() limit 1")
            else:
                c.execute("select datetime(timestamp, 'unixepoch', 'localtime'), entry from logs order by timestamp desc;")

            entries = c.fetchall()
            conn.close()
            return(entries)
        except:
            raise RuntimeError('A problem occurred while parsing log file. File might be empty or corrupt.')

def add_log_message(logmessage, past_time = 0):
    if logmessage != '':
        # sanitize apostrophes so I can write "I'm" and "don't" in log messages
        logmessage = logmessage.replace("'", "''")
        conn = sqlite3.connect(log_file_path)
        c = conn.cursor()
        if past_time != 0: # user provided a past time
            c.execute("insert into logs (timestamp, entry) values ({pasttime}, '{message}')".format(pasttime = past_time, message = logmessage))
        else:
            c.execute("insert into logs (timestamp, entry) values (strftime('%s', 'now'), '{message}')".format(message = logmessage))
        conn.commit()
        conn.close()

def show_count():
    conn = sqlite3.connect(log_file_path)
    c = conn.cursor()
    c.execute('select count(*) from logs')
    count = c.fetchall()
    count = count[0][0]
    return(count)

def show_random_log():
    entries = read_entries(log_file_path)
    print(format_log_entry(random.choice(entries)))

# reference: http://stackoverflow.com/a/3940137
def show_log_tail(n = 3):
    entries = read_entries(log_file_path, n)
    if type(entries) is list and len(entries) > 0:
        entries.reverse()

        for entry in entries:
            print(format_log_entry(entry))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'I am the captain. This is my log. caplog keeps short simple logs.')

    # add a mutually exclusive group
    # user can do only one of the following:
    #   -a for amend
    #   -d for delete last entry
    #   -g for grep
    #   -l for list
    #   -r for random
    group = parser.add_mutually_exclusive_group()

    # -a amend last log entry
    group.add_argument('-a', '--amend', help = 'amend last log entry',
            nargs = '+',
            action = 'store')

    # -d delete last log entry
    group.add_argument('-d', '--delete', help = 'delete last log entry',
            action = 'store_true')

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

    # -c number of entries
    group.add_argument('-c', '--count', help = 'show count of log entries',
            action = 'store_true')

    # -r show random log
    group.add_argument('-r', '--random', help = 'show a randomly chosen entry from logs',
            action = 'store_true')

    # optional log message
    parser.add_argument('logmessage', nargs = '*', type = str, help = 'The log message')

    args = parser.parse_args()

    # if user only enters $ caplog show default number of last entries
    if len(sys.argv) <= 1:
        show_log_tail(3)

    # if user specified the amend option, amend the last log entry
    elif args.amend:
        newlogmessage = ' '.join(args.amend)
        amend_last_entry(newlogmessage)

    # if user specified the delete option, delete the last log entry
    elif args.delete:
        delete_last_entry()

    # if user specified past date with the -p switch,
    # create the new date and prompt for an entry
    # if left empty, it cancels the operation
    elif args.past:
        past_date_term = ' '.join(args.past)
        add_to_the_past(past_date_term)

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

    # the -c switch will show number of entries
    elif args.count:
        print(show_count())

    # if user specified $ caplog -r or $ caplog --random, show random entry
    elif args.random:
        random_row = read_entries(log_file_path, random = True)
        print(format_log_entry(random_row[0]))

    # otherwise, log the message the user entered
    else:
        if args.logmessage:
            logmessage = ' '.join(args.logmessage).strip()
            add_log_message(logmessage)

