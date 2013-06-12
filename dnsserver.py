#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'linkerlin'
import sys
import struct
import socket
import traceback as tb
import re

reload(sys)
sys.setdefaultencoding("utf-8")

#---------------------------------------------------------------
# bytetodomain
# 03www06google02cn00 => www.google.cn
#--------------------------------------------------------------
def bytetodomain(s):
    domain = ''
    i = 0
    length = struct.unpack('!B', s[0:1])[0]

    while length != 0:
        i += 1
        domain += s[i:i + length]
        i += length
        length = struct.unpack('!B', s[i:i + 1])[0]
        if length != 0:
            domain += '.'

    return domain


class DNSServer(object):
    def __init__(self, ip, port=53, type_of_server=("tcp", "udp"), white_list=[]):
        self.white_list = white_list
        if len(self.white_list) > 0:
            self.initWhiteList()
        self.type_of_server = type_of_server
        self.ip = ip
        if type(port) == "str" or type(port) == "unicode":
            port = int(port)
        self.port = port
        self.TIMEOUT = 20
        self.ok = 0
        self.error = 0

    def initWhiteList(self):
        self.patterns = []
        for w in self.white_list:
            p = re.compile(w, re.IGNORECASE)
            self.patterns.append(p)

    def __str__(self):
        return "DNS Server @ %s:%d %s" % (self.ip, self.port, str(self.type_of_server))

    def isUDPServer(self):
        return "udp" in self.type_of_server

    def isTCPServer(self):
        return "tcp" in self.type_of_server

    def address(self):
        return (self.ip, int(self.port))

    def suppressed(self):
        self.error -= 1
        print self, "suppressed"
        return None

    def needToSuppress(self):
        return self.error > (self.ok * 10) and self.error > 10

    def checkQuery(self, query_data):
        m = None
        domain = bytetodomain(query_data[12:-4])
        for p in self.patterns:
            m = p.match(domain)
            if m: break
        if not m:
            return None
        print "white list match:",domain,self
        return self.query(query_data)

    def query(self, query_data):
        if self.needToSuppress():
            return self.suppressed()
        buffer_length = struct.pack('!h', len(query_data))
        data = None
        s = None
        try:
            if self.isTCPServer():
                #print "tcp",len(query_data)
                sendbuf = buffer_length + query_data
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(self.TIMEOUT) # set socket timeout
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                #print "connect to ", self.address()
                s.connect(self.address())
                #print "send", len(sendbuf)
                s.send(sendbuf)
                data = s.recv(2048)
                #print "data:", data
            elif self.isUDPServer():
                print "udp"
                sendbuf = query_data
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(self.TIMEOUT) # set socket timeout
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                #print type(querydata),(server, int(port))
                s.sendto(sendbuf, self.address())
                r, serv = s.recvfrom(1024)
                data = struct.pack('!h', len(r)) + r
        except Exception, e:
            self.error += 1
            print '[ERROR] QueryDNS: %s %s' % e.message, type(e)
            tb.print_stack()
        else:
            self.ok += 1
        finally:
            if s: s.close()
            return data, self

    #----------------------------------------------------
    # show dns packet information
    #----------------------------------------------------
    def showInfo(self, data, direction):
        try:
            from dns import message as m
        except ImportError:
            print "Install dnspython module will give you more response infomation."
        else:
            if direction == 0:
                print "query:\n\t", "\n\t".join(str(m.from_wire(data)).split("\n"))
                print "\n================"
            elif direction == 1:
                print "response:\n\t", "\n\t".join(str(m.from_wire(data)).split("\n"))
                print "\n================"


if __name__ == "__main__":
    s = DNSServer("8.8.8.8")
    print s