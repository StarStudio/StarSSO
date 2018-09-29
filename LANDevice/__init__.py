import gevent.monkey
from .discover import LANDeviceProber
from .config import LANDeviceProberConfig
from .port import DeviceList

gevent.monkey.patch_all(thread = False)
