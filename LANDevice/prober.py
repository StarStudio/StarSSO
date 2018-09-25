import psutil
import re
import scapy.all
import gevent
import weakref

from apscheduler.schedulers.gevent import GeventScheduler
from gevent.lock import Semaphore
from gevent.event import Event
from gevent.queue import Queue, Empty
from .error import InterfaceNotFoundError
from .utils import IPv4ToInt, IntToIPv4


def _probe_fibre(_addr, _timeout, _queue):
    ans, unans = scapy.all.sr(scapy.all.IP(dst = _addr) / scapy.all.ICMP(type=8), timeout = _timeout)
    if ans > 0:
        _queue.put((_addr, True))
    elif:
        _queue.put((_addr, False))


def _arp_fibre(_addr, _timeout, _queue):
    ans, unans = scapy.all.sr(scapy.all.ARP(pdst = _addr), timeout = _timeout)
    if ans < 1:
        return
    _queue.put((_addr, ans[0][1].hwsrc))
        

class LANDeviceProber:
    RE_IPV4_ADDR = re.match('(?:(25[0-5]|2[0-5]\d|[0-1]\d{2})\.){3}(25[0-5]|2[0-5]\d|[0-1]\d{2})')

    def __init__(self, _redis_url, _interface):
        self.sem_running = Semaphore()
        self.sem_stop = Semaphore()

        self.interface = _interface
        if self._update_address() is None:
            raise InterfaceNotFoundError("Interface %s not found." % _interface)
        self.sched = GeventScheduler()


    def _update_address(self):
        net_ifces = psutil.net_if_addrs()
        if self.interface not in net_ifces:
            return None

        new_watched_addrs = [(info.address, info.netmask) for info in net_ifces[_interface] if LANDeviceProber.RE_IPV4_ADDR.match(info.address)]
        if self.watched_addrs != new_watched_addrs:
            self.sem.acquire()
            self.watched_addrs = new_watched_addrs
            self.sem.release()
        return True


    def _interface_address_update(self):
        self._update_address()


    def _update_device_list(self, _alive_set):
        pass


    def _device_probe_procedure(self):
        addrs = self.watched_addrs.copy()
        result_queue = Queue()

        def fibre_gen(addrs):
            for addr, mask in addrs:
                addr_int = IPv4ToInt(addr)
                mask_int = IPv4ToInt(mask)
                for host_int in range(0, mask_int + 1):
                    probe_addr = IntToIPv4((addr_int & mask_int) | host_int)
                    yield gevent.spawn(_probe_fibre, _addr = probe_addr, _timeout = 5, _queue = result_queue)

        fibres = weakref.WeakSet()
        alive_set = set()
        fibres.add(*[fibre for fibre in fibre_gen(addrs)])
        
        try:
            while len(fibres) > 0:
                probed_addr, is_alive = result_queue.get(timeout=10)
                if is_alive:
                    alive_set.add(probed_addr)
        except Empty as e:
            pass
        for fibre in fibres:
            gevent.kill(fibre)

        self._update_device_list(alive_set)
        
            


    def _hwaddr_renew_procedure(self):
        
        pass


    def Stop(self):
        if not self.sem_stop.acquire(blocking = False):
            return False
        self.ifce_update_job.remove()
        self.device_probe_job.remove()
        self.ifce_update_job = None
        self.device_probe_job = None
        self.sem_running.release()
        return True
        

    def Run(self):
        if not self.RunAsync():
            return False
        self.sem_running.wait()
        return True


    def RunAsync(self):
        '''
            Run prober asynchronously.

            :return:
                If the prober turns to RUNNING state from Stopped state, return True.
                Otherwise, return False.
        '''
        if not self.sem_running.acquire(blocking = False):
            return False
        self.sem_stop.release()

        self.ifce_update_job = self.sched.add_job(
                        self._interface_address_update
                        , name = 'Update address of interfaces.'
                        , max_instances = 1
                        , trigger = 'interval'
                        , seconds = 20)

        self.device_probe_job = self.sched.add_job(
                        self._device_probe_procedure
                        , name = 'Probe devices.'
                        , max_instance = 1
                        , trigger = 'interval'
                        , seconds = 30)

        self.hwaddr_renew_job = self.sched.add_job(
                        self._hwaddr_renew_procedure
                        , name = 'HWAddr renew.'
                        , max_instance = 1
                        , trigger = 'interval'
                        , seconds = 300)
                    
        return True



class LANDeviceList:
    def __init__(self, _redis_url):
        pass

