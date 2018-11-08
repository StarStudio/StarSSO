import gevent.monkey
gevent.monkey.patch_all()

from .discover import LANDeviceProber
from LANDevice.config import LANDeviceProberConfig

