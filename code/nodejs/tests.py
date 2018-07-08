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
except:
	from urllib.request import urlopen

import decimal


def ioload(size, cnt):
	proc = subprocess.Popen(["dd", "if=/dev/urandom", "of=/tmp/ioload.log", "bs=%s" % size, "count=%s" % cnt, "conv=fdatasync", "oflag=dsync"], stderr=subprocess.PIPE)
	out, err = proc.communicate()
	buf = err.split("\n")[-2].split(",")
	t, s = buf[-2], buf[-1]
	t = t.split(" ")[1]
	s = s.split(" ")[1]
	return "%s,%s" % (t,s)

def ioload_test():
	bufs = []
	for i in xrange(5):
		buf = ioload()
		bufs.append(buf)
	return ";".join(bufs)


def network_test(port_offset, server_ip):
	port = 5000 + port_offset
	sp = subprocess.Popen(["./iperf3", "-c", server_ip, "-p", str(port), "-l", "-t", "1", "-Z", "-J"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = sp.communicate()
	_d = json.loads(out)["end"]
	sender = _d["streams"][0]["sender"]
	bps = str(sender["bits_per_second"])
	maxr = str(sender["max_rtt"])
	minr = str(sender["min_rtt"])
	meanr = str(sender["mean_rtt"])
	return ",".join([bps, meanr, minr, maxr])

def cpu_test(n):
	st = time.time() * 1000
	r = 1
	for i in range(1, n + 1):
		r *= i
	ed = time.time() * 1000
	return fstr(float(ed) - float(st))

def cpu_rand_test(n):
	s = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
	st = time.time() * 1000
	for i in range(1, n + 1):
		idx = [random.choice(s) for v in xrange(32)]
	ed = time.time() * 1000
	return fstr(float(ed) - float(st))	

def read_perf():
	proc = subprocess.Popen(["dd", "if=/tmp/tmp", "of=/dev/null", "bs=100M", "count=1000"], stderr=subprocess.PIPE)
	out, err = proc.communicate()
	buf = err.split("\n")[-2].split(",")
	t, s = buf[-2], buf[-1]
	t = t.split(" ")[1]
	s = s.split(" ")[1]
	return "%s,%s" % (t,s)

def read_test():
	bufs = []
	for i in xrange(10):
		buf = read_perf()
		bufs.append(buf)
	return ";".join(bufs)
