#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'linkerlin'
import sys


reload(sys)
sys.setdefaultencoding("utf-8")

DNSS = [
        ('8.8.8.8', 53, {"tcp",}),
        ('8.8.4.4', 53, {"tcp",}),
        ('208.67.222.222', 53, {"tcp",}),
        ('208.67.220.220', 53, {"tcp",}),


]



# a white dns server will service white list domains
WHITE_DNSS = [
    ("61.152.248.83", 53, {"udp",}, ["baidu.com", "qq.com"]),
]



