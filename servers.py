#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'linkerlin'
import sys

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
        ret = self.whiteListFirst(query_data)
        if ret:
            return ret
        # random select a server
        key = sample(self.dns_servers, 1)[0]
        print key
        server = self.dns_servers[key]
        return server.query(query_data)


if __name__ == "__main__":
    ss = Servers()
    s = DNSServer("8.8.8.8")
    ss.addDNSServer(s)
