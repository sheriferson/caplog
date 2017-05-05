"""
backup_db.py connects to caplog.db and create a backup json file
of all entries in ~/Documents
"""
import json
from os.path import expanduser
import sqlite3
from termcolor import colored

# reference: http://stackoverflow.com/a/4028943
home = expanduser('~')
log_file_path = home + '/caplog.db'
backup_file_path = home + '/Documents/caplog_backup.json'

def backup_caplog():
    """
    backup_caplog() will attempt to connect to the sqlite3
    db file that contains all log entries and save those
    entries to ~/Documents/caplog_backup.json
    """
    try:
        conn = sqlite3.connect(log_file_path)
        c = conn.cursor()

        c.execute('select * from logs order by timestamp')

        entries = c.fetchall()
        conn.close()

        with open(backup_file_path, 'w') as backup_file:
            json.dump(entries, backup_file)

        n = len(entries)

        print(colored('Backed up {n} entries to {backuppath}.'\
                .format(n=n, backuppath=backup_file_path), 'cyan'))

    except:
        raise RuntimeError('A problem occurred while backing up caplog.db.')

if __name__ == '__main__':
    backup_caplog()
