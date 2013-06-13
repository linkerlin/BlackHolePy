#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'linkerlin'
import sys
import struct
import threading
import SocketServer
import optparse
try:
    from dns import message as m
except ImportError as ex:
    print "cannot find dnspython"
try:
    from gevent import monkey
    monkey.patch_all()
except ImportError as ex:
    print "cannot find gevent"

import config
from dnsserver import DNSServer
from servers import Servers


reload(sys)
sys.setdefaultencoding("utf-8")

from dnsserver import bytetodomain


class DNSProxy(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    SocketServer.ThreadingMixIn.daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address=("0.0.0.0", 53), VERBOSE=2):
        self.VERBOSE = VERBOSE
        print "listening at:", address
        SELF = self

        class ProxyHandle(SocketServer.BaseRequestHandler):
            # Ctrl-C will cleanly kill all spawned threads
            daemon_threads = True
            # much faster rebinding
            allow_reuse_address = True

            def handle(self):
                data = self.request[0]
                socket = self.request[1]
                addr = self.client_address
                DNSProxy.transfer(SELF, data, addr, socket)

        SocketServer.UDPServer.__init__(self, address, ProxyHandle)

    def loadConfig(self, config):
        self.DNSS = config.DNSS
        self.servers = Servers()
        for s in self.DNSS:
            assert len(s) == 3
            ip, port, type_of_server = s
            self.servers.addDNSServer(DNSServer(ip, port, type_of_server, self.VERBOSE))
        self.WHITE_DNSS = config.WHITE_DNSS
        for ws in self.WHITE_DNSS:
            assert len(ws) == 4
            ip, port, type_of_server, white_list = ws
            self.servers.addWhiteDNSServer(DNSServer(ip, port, type_of_server, self.VERBOSE, white_list))


    def transfer(self, query_data, addr, server):
        if not query_data: return
        domain = bytetodomain(query_data[12:-4])
        qtype = struct.unpack('!h', query_data[-4:-2])[0]
        print 'domain:%s, qtype:%x, thread:%d' % \
              (domain, qtype, threading.activeCount())
        sys.stdout.flush()
        response = None
        for i in range(9):
            response = self.servers.query(query_data)
            if response:
                # udp dns packet no length
                server.sendto(response[2:], addr)
                break
        if response is None:
            print "[ERROR] Tried 9 times and failed to resolve %s" % domain
        return


if __name__ == '__main__':
    print '>> Please wait program init....'
    print '>> Init finished!'
    print '>> Now you can set dns server to 127.0.0.1'

    parser = optparse.OptionParser()
    parser.add_option("-v", dest="verbose", default="0", help="Verbosity level, 0-2, default is 0")
    options, _ = parser.parse_args()

    proxy = DNSProxy(VERBOSE=options.verbose)
    proxy.loadConfig(config)

    proxy.serve_forever()
    proxy.shutdown()