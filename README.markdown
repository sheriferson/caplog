# caplog

I am the captain. This is my log.

My computer's OS has logging, why don't I?

`caplog` is a command-line script that I use to write one-line logs about anything I think is worth logging.
The entries are saved in `json` format to `~/cap.log`.

`caplog` is compatible with Python 2 & 3.

Create an alias to make things easier.

```bash
alias caplog='python3 /path/to/caplog.py'
```

Make a new log entry.

```bash
$ caplog Made progress on my caplog script.
```

Other usage:

```text
usage: caplog.py [-h] [-a AMEND [AMEND ...] | -g GREP [GREP ...] | -l [NLOGS]
                 | -p [PAST [PAST ...]] | -r]
                 [logmessage [logmessage ...]]

I am the captain. This is my log. caplog keeps short simple logs.

positional arguments:
  logmessage            The log message

optional arguments:
  -h, --help            show this help message and exit
  -a AMEND [AMEND ...], --amend AMEND [AMEND ...]
                        amend last log entry
  -g GREP [GREP ...], --grep GREP [GREP ...]
                        search entries including term
  -l [NLOGS], --last [NLOGS]
                        show last n entries, default if left empty is 3
  -p [PAST [PAST ...]], --past [PAST [PAST ...]]
                        enter a log entry from the past
  -r, --random          show a randomly chosen entry from logs
```

If used without arguments, `caplog` shows the last three entries in the log.

```text
$ caplog

🚩  May 02 2016 17:18  Its time to move caplog to a place where I can use it everywhere.
🚩  May 02 2016 17:18  And I just pushed a change to simple-statistics. Wanna keep going.
🚩  May 03 2016 21:03  Made progress on my caplog script.
```
