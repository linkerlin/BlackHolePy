#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'linkerlin'
import sys


reload(sys)
sys.setdefaultencoding("utf-8")

DNSS = [#('156.154.70.1', 53, ("tcp",)),
        ('8.8.8.8', 53, ("tcp",)),
        ('8.8.4.4', 53, ("tcp",)),
        #('208.67.222.222', 53, ("udp",)),


]



# a white dns server will service white list domains
WHITE_DNSS = [
    ("10.203.104.9", 53, ("udp",), ["baidu.com", "qq.com"]),
]



