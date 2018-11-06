from gevent.monkey import patch_all
patch_all()

from .application import app
