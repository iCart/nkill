#!/usr/bin/python3

"""
Kills all processes listening on the given (tcp or tcp6) ports.

Written with great help from this article:
 http://voorloopnul.com/blog/a-python-netstat-in-less-than-100-lines-of-code/
"""

import os
import re
import glob
import sys
from signal import SIGKILL

PROC_TCP = "/proc/net/tcp"
PROC_TCP6 = "/proc/net/tcp6"

LISTEN_STATE = '0A'


def _load(infile):
    """ Read the table of tcp connections & remove header  """
    with open(infile, 'r') as f:
        content = f.readlines()
        content.pop(0)
    return content


def _hex2dec(s):
    return str(int(s, 16))


def _ip(s):
    ip = [(_hex2dec(s[6:8])), (_hex2dec(s[4:6])), (_hex2dec(s[2:4])), (_hex2dec(s[0:2]))]
    return '.'.join(ip)


def _remove_empty(array):
    return [x for x in array if x != '']


def _convert_ip_port(array):
    host, port = array.split(':')
    return _ip(host), _hex2dec(port)


def netstat(ports_to_kill):
    # Not using yield from for python2 compatibility
    yield from stat_tcp(ports_to_kill, PROC_TCP)
    yield from stat_tcp(ports_to_kill, PROC_TCP6)


# noinspection PyBroadException
def stat_tcp(ports_to_kill, tcpfile):
    content = _load(tcpfile)
    result = []
    for line in content:
        # The '_' are all fields we don't care about
        tcp_id, local_address, _, st, _, _, _, uid, timeout, inode, *_ = line.split()

        l_host, l_port = _convert_ip_port(local_address)

        if st != LISTEN_STATE or l_port not in ports_to_kill:
            continue

        pid = _get_pid_of_inode(inode)  # Get pid prom inode.
        try:  # try read the process name.
            exe = os.readlink('/proc/' + pid + '/exe')
        except Exception as e:
            exe = None

        yield [tcp_id, l_host, l_port, st, uid, pid, exe]


def _get_pid_of_inode(inode):
    '''
    To retrieve the process pid, check every running process and look for one using
    the given inode.
    '''
    for item in glob.glob('/proc/[0-9]*/fd/[0-9]*'):
        try:
            if re.search(inode, os.readlink(item)):
                return item.split('/')[2]
        except:
            pass
    return None


def kill_ports(ports_to_kill):
    killed = False
    for tcp_id, l_host, l_port, st, uid, pid, exe in netstat(ports_to_kill):
        if l_port in ports_to_kill:
            os.kill(int(pid), SIGKILL)
            print('Killed %s (pid %s) listening on port %s' % (exe, pid, l_port))
            killed = True

    if not killed:
        print('Found no process listening on port(s) %s' % ' '.join(ports_to_kill))


if __name__ == '__main__':

    if len(sys.argv) <= 1:
        print('I need a list of ports to kill')
        exit()

    if os.geteuid() != 0:
        print("Warning: you are not running this script as root, expect some things to not work")

    kill_ports(sys.argv[1:])
