#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'linkerlin'
import sys

reload(sys)
sys.setdefaultencoding("utf-8")
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
import time
from hashlib import md5


class Counter(dict):
    'Mapping where default values are zero'

    def __missing__(self, key):
        return 0


def sqlite_cache(timeout_seconds=100, cache_none=True, ignore_args={}):
    import sqlite3

    def decorating_function(user_function,
                            len=len, iter=iter, tuple=tuple, sorted=sorted, KeyError=KeyError):
        with sqlite3.connect(u"cache.sqlite") as cache_db:
            cache_cursor = cache_db.cursor()
            cache_table = u"table_" + user_function.func_name
            #print cache_table
            cache_cursor.execute(
                u"CREATE TABLE IF NOT EXISTS " + cache_table
                + u" (key CHAR(36) PRIMARY KEY, value TEXT, update_time  timestamp);")
            cache_db.commit()
        kwd_mark = object()             # separate positional and keyword args
        lock = threading.Lock()

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            result = None
            cache_db = None
            # cache key records both positional and keyword args
            key = args
            if kwds:
                real_kwds = []
                for k in kwds:
                    if k not in ignore_args:
                        real_kwds.append((k, kwds[k]))
                key += (kwd_mark,)
                if len(real_kwds) > 0:
                    key += tuple(sorted(real_kwds))
            while cache_db is None:
                try:
                    with lock:
                        cache_db = sqlite3.connect(u"cache.sqlite")
                except sqlite3.OperationalError as ex:
                    print ex
                    time.sleep(0.05)
                # get cache entry or compute if not found
            try:
                cache_cursor = cache_db.cursor()
                key_str = str(key) # 更加宽泛的Key，只检查引用的地址，而不管内容，“浅”检查,更好的配合方法，但是可能会出现过于宽泛的问题
                key_str = md5(key_str).hexdigest() # base64.b64encode(key_str)
                #print "key_str:", key_str[:60]
                with lock:
                    cache_cursor.execute(
                        u"select * from " + cache_table
                        + u" where key = ? order by update_time desc", (key_str,))
                for record in cache_cursor:
                    dump_data = base64.b64decode(record[1])
                    result = p.loads(dump_data)
                    #print "cached:", md5(result).hexdigest()
                    break
                if result is not None:
                    with lock:
                        wrapper.hits += 1
                    print "hits", wrapper.hits, "miss", wrapper.misses, wrapper
                else:
                    result = user_function(*args, **kwds)
                    if result is None and cache_none == False:
                        return
                    value = base64.b64encode(p.dumps(result, p.HIGHEST_PROTOCOL))
                    while 1:
                        try:
                            cache_cursor.execute(u"REPLACE INTO " + cache_table + u" VALUES(?,?,?)",
                                                 (key_str, value, dt.datetime.now()))
                        except sqlite3.OperationalError as ex:
                            print ex, "retry update db."
                        else:
                            cache_db.commit()
                            with lock:
                                wrapper.misses += 1
                            break
            finally:
                if random.random() > 0.999:
                    timeout = dt.datetime.now() - dt.timedelta(seconds=timeout_seconds)
                    with lock:
                        cache_cursor.execute(u"DELETE FROM " + cache_table + u" WHERE update_time < datetime(?)",
                                             (str(timeout),))
                with lock:
                    cache_db.commit()
                    cache_db.close()
            return result

        def clear():
            with lock:
                wrapper.hits = wrapper.misses = 0

        wrapper.hits = wrapper.misses = 0
        wrapper.clear = clear
        return wrapper

    return decorating_function


def lru_cache(maxsize=100, cache_none=True, ignore_args=[]):
    '''Least-recently-used cache decorator.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    Clear the cache with f.clear().
    http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used

    '''
    maxqueue = maxsize * 10

    def decorating_function(user_function,
                            len=len, iter=iter, tuple=tuple, sorted=sorted, KeyError=KeyError):
        cache = {}                  # mapping of args to results
        queue = collections.deque() # order that keys have been used
        refcount = Counter()        # times each key is in the queue
        sentinel = object()         # marker for looping around the queue
        kwd_mark = object()         # separate positional and keyword args

        # lookup optimizations (ugly but fast)
        queue_append, queue_popleft = queue.append, queue.popleft
        queue_appendleft, queue_pop = queue.appendleft, queue.pop
        lock = threading.RLock()

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            with lock:
                # cache key records both positional and keyword args
                key = args
                if kwds:
                    real_kwds = []
                    for k in kwds:
                        if k not in ignore_args:
                            real_kwds.append((k, kwds[k]))
                    key += (kwd_mark,)
                    if len(real_kwds) > 0:
                        key += tuple(sorted(real_kwds))
                        #print "key", key

                # record recent use of this key
                queue_append(key)
                refcount[key] += 1

                # get cache entry or compute if not found
                try:
                    result = cache[key]
                    wrapper.hits += 1
                    #print "hits", wrapper.hits, "miss", wrapper.misses, wrapper
                except KeyError:
                    result = user_function(*args, **kwds)
                    if result is None and cache_none == False:
                        return
                    cache[key] = result
                    wrapper.misses += 1

                    # purge least recently used cache entry
                    if len(cache) > maxsize:
                        key = queue_popleft()
                        refcount[key] -= 1
                        while refcount[key]:
                            key = queue_popleft()
                            refcount[key] -= 1
                        if key in cache:
                            del cache[key]
                        if key in refcount:
                            refcount[key]
                finally:
                    pass

                # periodically compact the queue by eliminating duplicate keys
                # while preserving order of most recent access
                if len(queue) > maxqueue:
                    refcount.clear()
                    queue_appendleft(sentinel)
                    for key in ifilterfalse(refcount.__contains__,
                                            iter(queue_pop, sentinel)):
                        queue_appendleft(key)
                        refcount[key] = 1

            return result

        def clear():
            cache.clear()
            queue.clear()
            refcount.clear()
            wrapper.hits = wrapper.misses = 0

        wrapper.hits = wrapper.misses = 0
        wrapper.clear = clear
        return wrapper

    return decorating_function


def lfu_cache(maxsize=100):
    '''Least-frequently-used cache decorator.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    Clear the cache with f.clear().
    http://en.wikipedia.org/wiki/Least_Frequently_Used

    '''

    def decorating_function(user_function):
        cache = {}                      # mapping of args to results
        use_count = Counter()           # times each key has been accessed
        kwd_mark = object()             # separate positional and keyword args
        lock = threading.RLock()

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            with lock:
                key = args
                if kwds:
                    key += (kwd_mark,) + tuple(sorted(kwds.items()))
                use_count[key] += 1

                # get cache entry or compute if not found
                try:
                    result = cache[key]
                    wrapper.hits += 1
                except KeyError:
                    result = user_function(*args, **kwds)
                    cache[key] = result
                    wrapper.misses += 1

                    # purge least frequently used cache entry
                    if len(cache) > maxsize:
                        for key, _ in nsmallest(maxsize // 10,
                                                use_count.iteritems(),
                                                key=itemgetter(1)):
                            del cache[key], use_count[key]

            return result

        def clear():
            cache.clear()
            use_count.clear()
            wrapper.hits = wrapper.misses = 0

        wrapper.hits = wrapper.misses = 0
        wrapper.clear = clear
        return wrapper

    return decorating_function


if __name__ == '__main__':

    @lru_cache(maxsize=20, ignore_args=["y"])
    def f(x, y):
        return 3 * x + y

    domain = range(5)
    from random import choice

    for i in range(1000):
        r = f(choice(domain), y=choice(domain))

    print(f.hits, f.misses)

    @lfu_cache(maxsize=20)
    def f(x, y):
        return 3 * x + y

    domain = range(5)
    from random import choice

    for i in range(1000):
        r = f(choice(domain), choice(domain))

    print(f.hits, f.misses)

    @sqlite_cache()
    def f2(x, y):
        return 3 * x + y

    domain = range(50)
    for i in range(1000):
        r = f2(choice(domain), y=choice(domain))
    print(f2.hits, f2.misses)