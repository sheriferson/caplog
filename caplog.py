# -*- coding: utf-8 -*-
# pylint: disable=no-else-return
"""
I am the captain. This is my log. caplog keeps short simple logs.
caplog.py is the main script file for caplog. It contains the parser
and various functions.
"""

import argparse
import os
import re
import shutil
import sqlite3
from subprocess import call
import sys
import tempfile
import textwrap
import time

import dateparser
import terminaltables

from termcolor import colored

# reference: http://stackoverflow.com/a/4028943
home = os.path.expanduser('~')
log_file_path = home + '/caplog.db'

def create_log_file(log_location):
    """
    This function is called internally when no log file is found.
    """
    print('No log file found. Creating file...')

    conn = sqlite3.connect(log_location)
    c = conn.cursor()
    c.execute('create table logs (timestamp TIMESTAMP, entry TEXT);')
    c.execute('create table console (log_timestamp TIMESTAMP, entry_timestamp TIMESTAMP);')
    c.execute('''create trigger logging
            after insert on logs
            begin
                insert into console (log_timestamp, entry_timestamp) values (strftime('%s', 'now'), new.timestamp);
            end
            ;''')
    conn.commit()
    conn.close()
    print('New log file created at {logfile}'.format(logfile=log_location))

def add_to_the_past(log_location, past_date_term, past_message=''):
    """
    Invoked with caplog -p 4 hours ago (example)
    add_to_the_past() will parse the date string, prompt for an entry message,
    and then pass the timestamp and message to add_log_message()
    """
    past_date = dateparser.parse(past_date_term, settings={'TIMEZONE': time.strftime('%Z')})

    if past_date is None:
        print("I couldn't parse the term you entered.")
        quit()

    past_date_timestamp = time.mktime(past_date.timetuple())

    if (past_message.strip() == ''):
        print(colored('Logging an entry dated:' + '\t' +
                      past_date.strftime('%B %d %Y %H:%M'),
                      'cyan'))
        confirmation = input(colored("\nEnter 'y' to confirm, or anything else to cancel.",
                                     'cyan'))
        if confirmation.strip() != 'y':
            print(colored('Cancelled.', 'red'))
            return(False)

        with tempfile.NamedTemporaryFile(suffix='.tmp') as temp_log_file:
            editor = '/usr/local/bin/nvim'
            call([editor, temp_log_file.name])
            with open(temp_log_file.name) as temp_input_file:
                past_message = temp_input_file.read()

    if past_message.strip() == '':
        print(colored('Cancelled.', 'red'))
        return(False)
    else:
        return(add_log_message(log_location, past_message.strip(), past_date_timestamp))

def grep_search_logs(log_location, search_string):
    """
    grep_search_logs() is invoked by caplog -g 'search term'
    It will pass this search term to read_entries()
    """
    results = read_entries(log_location, search_term=search_string)
    return results

def parse_entry_file(entry_dir_path, entry_path):
    """
    Verifies that a file is a valid caplog entry.
    If valid, parses the file into a timestamp and entry text.
    """

    full_entry_path = os.path.join(entry_dir_path, entry_path)
    logged_dir_path = os.path.join(entry_dir_path, '_logged', entry_path)
    with open(full_entry_path, 'rb') as f:
        lines = f.read().splitlines()

    # pattern that matches a timestamp of the format
    # 2017-10-22 18:33
    # Test caplog message.
    pattern = re.compile(r"^[0-9]{4}-[0-9]{1,}-[0-9]{1,}\s[0-9]{1,}:[0-9]{1,}")
    checked = pattern.match(lines[0].decode('utf-8'))

    if (checked and len(lines) > 1):
        timestamp = lines.pop(0).decode('utf-8')
        entry = ' '.join([line.decode('utf-8').strip() for line in lines])

        # check if adding the message succeeds
        # and delete the file if it does
        if (add_to_the_past(log_file_path, timestamp, entry)):
            if not os.path.exists(logged_dir_path):
                os.makedirs(logged_dir_path)
            shutil.move(full_entry_path, logged_dir_path)

def amend_last_entry(log_location, logmessage):
    """
    Invoked by `caplog -a New amended entry`
    If passed a non-empty string, it will connect to the log file
    and update the entry with the most recent timestamp.
    """
    # 1. get last entry
    # 2. use the timestamp as the lookup value
    # 3. update row

    if logmessage != '':
        conn = sqlite3.connect(log_location)
        c = conn.cursor()
        c.execute("select * from logs order by timestamp desc limit 1")
        lastrow = c.fetchall()
        lasttime = lastrow[0][0]

        c.execute("update logs set entry=('{logentry}') where timestamp=({time})"
                  .format(logentry=logmessage, time=lasttime))
        conn.commit()
        conn.close()

def delete_last_entry(log_location):
    """
    Connects to log entries file and deletes last entry.
    Last entry is defined as entry with max(timestamp).
    """
    print(colored('Are you sure you want to delete the last entry? Y/n', 'red'))
    confirm_delete = input('> ')

    if confirm_delete.lower() == 'y':
        conn = sqlite3.connect(log_location)
        c = conn.cursor()
        c.execute('delete from logs where timestamp = (select max(timestamp) from logs);')
        conn.commit()
        conn.close()
        print(colored('Last entry deleted.', 'cyan'))

def find_entry_files(entry_dir_path):
    """
    Looks in the provided path and attempts to parse any files
    it finds there. It uses parse_entry_file() to validate the entries
    and log them if they pass.
    """

    files = os.listdir(entry_dir_path)
    for candidate in files:
        if candidate.endswith('.txt'):
            parse_entry_file(entry_dir_path, candidate)

def format_log_entry(sql_rows):
    """
    This is a helper function that accepts "sql rows" from read_entries
    and formats them for printing to stdout.
    """
    # sql_rows is a list of tuples, we want it to be a list of lists
    sql_rows = [list(x) for x in sql_rows]

    # add a header row then add all other rows passed to format_log_entry()
    header = [colored('time', 'cyan'), colored('entry', 'cyan')]
    full_result = [header]
    full_result.extend(sql_rows)

    # create the SingleTable object so we can get max_width
    # which we need to break up the entry texts to wrap properly
    # this logic largely comes from terminaltables example3.py:
    # https://github.com/Robpol86/terminaltables/blob/master/example3.py
    return_table = terminaltables.SingleTable(full_result)
    max_width = return_table.column_max_width(1)
    max_width = 80 if max_width > 80 else max_width

    for ii in list(range(1, len(return_table.table_data))):
        wrapped_message = '\n\n'.join(['\n'.join(textwrap.wrap(line,
                                                               max_width,
                                                               break_long_words=False, replace_whitespace=False)) for line in return_table.table_data[ii][1].splitlines() if line.strip() != ''])
        return_table.table_data[ii][1] = wrapped_message

    return return_table.table

def read_entries(log_location, n=0, search_term="", random_entry=False):
    """
    read_entries() will be invoked by any command that returns log entries:
    caplog
    caplog -r
    caplog -l n
    caplog -g 'search term'

    It connects to the log entries file and returns entries that match
    the arguments passed to caplog.py

    It also handles first-run scenario where no file exists. In that case
    it will create the empty log file.
    """
    if not os.path.isfile(log_location):
        create_log_file(log_location)
        return(None)

    else:
        try:
            conn = sqlite3.connect(log_location)
            c = conn.cursor()
            if n > 0:
                c.execute("""
                        select strftime('%Y-%m-%d %H:%M', timestamp, 'unixepoch', 'localtime')
                        , entry from logs order by timestamp desc limit {n};
                        """.format(n=n))

            elif search_term != "":
                c.execute("""
                        select strftime('%Y-%m-%d %H:%M', timestamp, 'unixepoch', 'localtime')
                        , entry from logs where entry like '%{searchterm}%'
                        order by timestamp
                        """.format(searchterm=search_term))

            elif random_entry is True:
                c.execute("""
                          select strftime('%Y-%m-%d %H:%M', timestamp, 'unixepoch', 'localtime')
                          , entry from logs order by Random() limit 1
                          """)
            else:
                c.execute("""
                          select strftime('%Y-%m-%d %H:%M', timestamp, 'unixepoch', 'localtime')
                          , entry from logs order by timestamp desc;
                          """)

            entries = c.fetchall()
            conn.close()
            return(entries)
        except:
            raise RuntimeError(("A problem occurred while parsing log file. "
                                "File might be empty or corrupt."))

def add_log_message(log_location, logmessage, past_time=0):
    """
    Invoked by `caplog My log message` or `caplog -p 4 hours ago` plus
    a message. It handles entering a log message at present time, or at a past
    time if the past_time variable contains something other than 0
    """
    if not os.path.isfile(log_location):
        create_log_file(log_location)

    if logmessage != '':
        # sanitize apostrophes so I can write "I'm" and "don't" in log messages
        logmessage = logmessage.replace("'", "''")
        conn = sqlite3.connect(log_location)
        c = conn.cursor()

        if past_time != 0: # user provided a past time
            c.execute("""
                      insert into logs (timestamp, entry)
                      values ({pasttime}, '{message}')
                      """
                      .format(pasttime=past_time, message=logmessage))
        else:
            c.execute("""
                      insert into logs (timestamp, entry)
                      values (strftime('%s', 'now'), '{message}')
                      """
                      .format(message=logmessage))

        conn.commit()
        conn.close()
        return(True)
    else:
        return(False)

def show_count(log_location):
    """
    caplog -c
    will run show_count(), which will return/print
    the total number of entries in caplog.db
    """
    conn = sqlite3.connect(log_location)
    c = conn.cursor()
    c.execute('select count(*) from logs')
    count = c.fetchall()
    count = count[0][0]
    return count

# reference: http://stackoverflow.com/a/3940137
def show_log_tail(log_location, n=3):
    """
    invoked by default `caplog` with default n=3 or `caplog -l 6` which changes
    n to 6. It prints the latest n log entries from the log file.
    """
    entries = read_entries(log_location, n)
    if isinstance(entries, list) and len(entries) > 0:
        entries.reverse()

        print(format_log_entry(entries))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=("I am the captain. "
                                                  "This is my log. "
                                                  "caplog keeps short simple logs."))

    # add a mutually exclusive group
    # user can do only one of the following:
    #   -a for amend
    #   -d for delete last entry
    #   -g for grep
    #   -l for list
    #   -r for random
    group = parser.add_mutually_exclusive_group()

    # -a amend last log entry
    group.add_argument('-a', '--amend',
                       help='amend last log entry',
                       nargs='+',
                       action='store')

    # -b check and add logs in batch from files
    group.add_argument('-b', '--batch',
                       help='add entries in batch from a directory',
                       nargs='*',
                       action='store')

    # -d delete last log entry
    group.add_argument('-d', '--delete',
                       help='delete last log entry',
                       action='store_true')

    # -g show resulting entries for search term
    group.add_argument('-g', '--grep',
                       help='search entries including term',
                       nargs='+',
                       action='store')

    # -l show last n entries
    group.add_argument('-l', '--last', dest='nlogs',
                       help='show last n entries, default if left empty is 3',
                       nargs='?',
                       action='store',
                       type=int)

    # -p enter log entry from and in the past
    group.add_argument('-p', '--past',
                       help='enter a log entry from the past',
                       nargs='*',
                       action='store')

    # -c number of entries
    group.add_argument('-c', '--count',
                       help='show count of log entries',
                       action='store_true')

    # -r show random log
    group.add_argument('-r', '--random',
                       help='show a randomly chosen entry from logs',
                       action='store_true')

    # optional log message
    parser.add_argument('logmessage', nargs='*', type=str, help='The log message')

    args = parser.parse_args()

    # if user only enters $ caplog show default number of last entries
    if len(sys.argv) <= 1:
        show_log_tail(log_file_path, 3)

    # if user specified the amend option, amend the last log entry
    elif args.amend:
        newlogmessage = ' '.join(args.amend)
        amend_last_entry(log_file_path, newlogmessage)

    # if user specified the batch option, check provided dir
    elif args.batch:
        entries_dir = args.batch[0]
        find_entry_files(entries_dir)

    # if user specified the delete option, delete the last log entry
    elif args.delete:
        delete_last_entry(log_file_path)

    # if user specified past date with the -p switch,
    # create the new date and prompt for an entry
    # if left empty, it cancels the operation
    elif args.past:
        joined_past_date_term = ' '.join(args.past)
        add_to_the_past(log_file_path, joined_past_date_term)

    # if user specified a number of last entries with $ caplog --last n, show last n logs
    elif args.nlogs:
        show_log_tail(log_file_path, args.nlogs)

    # if user specified $ caplog -g searchterm, show any results
    elif args.grep:
        joined_search_term = ' '.join(args.grep)
        grep_results = grep_search_logs(log_file_path, joined_search_term)

        if grep_results:
            print(format_log_entry(grep_results))

    # the -c switch will show number of entries
    elif args.count:
        print(show_count(log_file_path))

    # if user specified $ caplog -r or $ caplog --random, show random entry
    elif args.random:
        random_row = read_entries(log_file_path, random_entry=True)
        print(format_log_entry(random_row))

    # otherwise, log the message the user entered
    else:
        if args.logmessage:
            joined_message = ' '.join(args.logmessage).strip()
            add_log_message(log_file_path, joined_message)
