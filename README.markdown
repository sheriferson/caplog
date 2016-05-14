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

If used without arguments, `caplog` shows the last three entries in the log.

```text
$ caplog

🚩  May 02 2016 17:18  Its time to move caplog to a place where I can use it everywhere.
🚩  May 02 2016 17:18  And I just pushed a change to simple-statistics. Wanna keep going.
🚩  May 03 2016 21:03  Made progress on my caplog script.
```
