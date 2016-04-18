nkill
=====

Kills all processes listening on the given (tcp or tcp6) ports.

INSTALL
-------

* Clone
* sudo ln -s /path/to/nkill.py /usr/bin/nkill

USAGE
-----

Say your webserver is listening on port 8080 and refuses to stop:
    nkill 8080

Sometimes, process fork and will need to be killed many times, just run something like:
    watch -n 0 "nkill 8080"
