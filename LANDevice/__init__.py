import gevent.monkey

gevent.monkey.patch_all(thread = False)
