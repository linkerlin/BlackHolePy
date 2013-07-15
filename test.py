#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'linkerlin'
import sys
import struct
try:
    from dns import message as m
except ImportError as ex:
    print "cannot find dnspython"

from dnsserver import bytetodomain
from caches import *
import collections
import functools
from itertools import ifilterfalse
from heapq import nsmallest
from operator import itemgetter
import threading
import cPickle as p
import datetime as dt
import base64
import random
from random import choice

def testSqliteCache():
    @sqlite_cache()
    def f2(x, y):
        return 3 * x + y

    domain = range(50)
    for i in range(1000):
        r = f2(choice(domain), y=choice(domain))
    print(f2.hits, f2.misses)
    assert f2.hits>0


class R(object):
    def __init__(self, name):
        if isinstance(name, str):
            self.name = unicode(name)
        else:
            self.name = name

    def __str__(self):
        return self.name.decode("utf-8")
    def __unicode__(self):
        return self.name

    def __enter__(self):
        print "enter:",self
    def __exit__(self, exc_type, exc_val, exc_tb):
        print "exit:",self

with R("A") as a, R("B") as b: # require A then require B
    print "..."