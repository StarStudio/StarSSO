import gevent.monkey
from .discover import LANDeviceProber
from LANDevice.config import LANDeviceProberConfig

gevent.monkey.patch_all()
