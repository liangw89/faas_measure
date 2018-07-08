#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import json
import time
import os
import sys
import socket
import random
import uuid
import subprocess

try:
    import urllib2
    from urllib2 import urlopen
except BaseException:
    from urllib.request import urlopen

import decimal


def fstr(f):
    """
    Convert a float number to string
    """

    ctx = decimal.Context()
    ctx.prec = 20
    d1 = ctx.create_decimal(repr(f))
    return format(d1, 'f')


def ioload(size, cnt):
    """ One round of IO throughput test """

    proc = subprocess.Popen(["dd",
                             "if=/dev/urandom",
                             "of=/tmp/ioload.log",
                             "bs=%s" % size,
                             "count=%s" % cnt,
                             "conv=fdatasync",
                             "oflag=dsync"],
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()
    buf = err.split("\n")[-2].split(",")
    t, s = buf[-2], buf[-1]
    t = t.split(" ")[1]
    # s = s.split(" ")[1]
    return "%s,%s" % (t, s)


def ioload_test(rd, size, cnt):
    """
    IO throughput test using dd
    Args:
            rd: no. of rounds
            size: the size of data to write each time
            cnt: the times to write in each round
            (see doc of dd)
    Return:
            IO throughput, total time spent (round 1);
            ...; IO throughput, total time spent (round N)
    """
    bufs = []
    for i in xrange(rd):
        buf = ioload(size, cnt)
        bufs.append(buf)
    return ";".join(bufs)


def network_test(server_ip, port):
    """
    Network throughput test using iperf

    Args:
            port_offset: the offset of the port number;
            server_ip: the IP of the iperf server

    Return:
            throughput in bits, mean rtt, min rtt, max rtt
            (see doc of iperf)
    """
    sp = subprocess.Popen(["./iperf3",
                           "-c",
                           server_ip,
                           "-p",
                           str(port),
                           "-l",
                           "-t",
                           "1",
                           "-Z",
                           "-J"],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    out, err = sp.communicate()
    _d = json.loads(out)["end"]
    sender = _d["streams"][0]["sender"]
    bps = str(sender["bits_per_second"])
    maxr = str(sender["max_rtt"])
    minr = str(sender["min_rtt"])
    meanr = str(sender["mean_rtt"])
    return ",".join([bps, meanr, minr, maxr])


def cpu_test(n):
    """
    CPU test: calculate N!

    Args: N

    Return:
            the time for calculating N!
    """
    st = time.time() * 1000
    r = 1
    for i in range(1, n + 1):
        r *= i
    ed = time.time() * 1000
    return fstr(float(ed) - float(st))


def cpu_util_test(n):
    """
    CPU utilization test. Recording N timestamps continuously

    Args: N

    Return:
            The timestamps recorded. Only return unique timestamps
    """
    i = 0
    res = {}
    while i < n:
        res[time.time() * 1000] = 0
        i += 1
    res = sorted(res.keys())
    res = ";".join([fstr(v) for v in res])
    return res


def cpu_rand_test(n):
    s = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    st = time.time() * 1000
    for i in range(1, n + 1):
        idx = [random.choice(s) for v in xrange(32)]
    ed = time.time() * 1000
    return fstr(float(ed) - float(st))

# def read_perf():
# 	proc = subprocess.Popen(["dd", "if=/tmp/tmp", "of=/dev/null", "bs=100M", "count=1000"], stderr=subprocess.PIPE)
# 	out, err = proc.communicate()
# 	buf = err.split("\n")[-2].split(",")
# 	t, s = buf[-2], buf[-1]
# 	t = t.split(" ")[1]
# 	s = s.split(" ")[1]
# 	return "%s,%s" % (t,s)

# def read_test():
# 	bufs = []
# 	for i in xrange(10):
# 		buf = read_perf()
# 		bufs.append(buf)
# 	return ";".join(bufs)
