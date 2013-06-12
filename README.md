BlackHolePy
===========

BlackHolePy是一个迷你型的DNS（代理）服务器。
它的主要特色：
1) 支持TCP DNS并支持白名单，从而在防止DNS污染的同时支持了内部私有域名解析。
2) 内置了Cache, 带给你飞一般的感觉。尤其是访问国外网站的时候。
如果你的企业或组织在内部架设了自己的DNS Server，那么可以配置 config.py 里面的 WHITE_DNSS 。


运行需求
===========
Python 2.7 或者 PyPy 2.0.2
如果能安装 GEvent 和 dnspython 那就最好了。不装也能跑。
安装GEvent以后，BlackHolePy运行在单线程模式，快捷并节约系统资源。
在 PyPy 2.0.2 下测试通过。但是PyPy的coroutine暂时还没有支持。

运行
===========
sudo python dnsproxy.py

然后把你的DNS服务器配置到 127.0.0.1 即可。

感谢
===========
本项目是基于以下两个项目的思路，重新编写的。
https://github.com/henices/Tcp-DNS-proxy
https://github.com/code4craft/blackhole
在此感谢这两个项目的作者！




