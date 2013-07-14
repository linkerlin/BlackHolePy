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


reload(sys)
sys.setdefaultencoding("utf-8")

from dnsserver import DNSServer
from random import sample


class Servers(object):
    def __init__(self):
        self.dns_servers = {}
        self.white_servers = []

    def addDNSServer(self, dns_server):
        assert isinstance(dns_server, DNSServer)
        self.dns_servers[dns_server.address()] = dns_server

    def addWhiteDNSServer(self, dns_server):
        assert isinstance(dns_server, DNSServer)
        self.white_servers.append(dns_server)

    def whiteListFirst(self, query_data):
        if len(self.white_servers):
            for s in self.white_servers:
                ret = s.checkQuery(query_data)
                if ret:
                    return ret
        return None

    def query(self, query_data):
        domain = bytetodomain(query_data[12:-4])
        qtype = struct.unpack('!h', query_data[-4:-2])[0]
        id = struct.unpack('!h', query_data[0:2])[0]
        #print "id", id
        #msg = [line for line in str(m.from_wire(query_data)).split('\n') if line.find("id", 0, -1) < 0]
        msg = query_data[4:]
        responce = self._query(tuple(msg),
                               query_data=query_data) # query_data must be written as a named argument, because of lru_cache()
        if responce:
            return responce[0:2] + query_data[0:2] + responce[4:]
        else:
            return responce

    @sqlite_cache(timeout_seconds=200000, cache_none=False, ignore_args=["query_data"])
    def _query(self, msg, query_data):
        #print msg
        ret = self.whiteListFirst(query_data)
        if ret:
            return ret
            # random select a server
        key = sample(self.dns_servers, 1)[0]
        #print key
        server = self.dns_servers[key]
        return server.query(query_data)


if __name__ == "__main__":
    ss = Servers()
    s = DNSServer("8.8.8.8")
    ss.addDNSServer(s)
