import re
#import scapy.all
import gevent
import weakref
import ipdb
import netifaces
import socket

from datetime import datetime
from apscheduler.schedulers.gevent import GeventScheduler
from gevent.lock import Semaphore
from gevent.event import Event
from gevent.queue import Queue, Empty
from .error import InterfaceNotFoundError
from .utils import IPv4ToInt, IntToIPv4
from .config import LANDeviceProberConfig
from .arp import ARPRequest

def _probe_fibre(_addr, _interface, _timeout, _queue):
    #ans, unans = scapy.all.sr(scapy.all.IP(dst = _addr) / scapy.all.ICMP(type=8), timeout = _timeout, verbose = False)
    #ans, unans = scapy.all.sr(scapy.all.ARP(pdst = _addr, hwdst="ff:ff:ff:ff:ff:ff"), timeout = _timeout, verbose = False)
    #if len(ans) > 0:
    #    _queue.put((_addr, True))
    #else:
    #    _queue.put((_addr, False))
    mac = ''
    try: 
        mac = ARPRequest(_interface, _addr, _timeout * 1000)
    except socket.timeout as e:
        pass

    if mac != '':
        _queue.put((_addr, mac, True))
    else:
        _queue.put((_addr, mac, False))


class LANDeviceProber:

    def __init__(self, _config):
        self.sem_running = Semaphore()
        self.sem_stop = Semaphore()

        self.sem = Semaphore()
        self.watched_addrs = set()

        self.interface = _config.interface
        if self._update_address() is None:
            raise InterfaceNotFoundError("Interface %s not found." % _config.interface)
        self.sched = GeventScheduler()


    def _update_address(self):
        try:
            ifce_addrs = netifaces.ifaddresses(self.interface)
        except ValueError as e:
            return None
        new_watched_addrs = set([(info['addr'], info['netmask']) for info in ifce_addrs[netifaces.AF_INET]]) 
        if self.watched_addrs != new_watched_addrs:
            self.sem.acquire()
            self.watched_addrs = new_watched_addrs
            self.sem.release()
        return True


    def _interface_address_update(self):
        self._update_address()


    def _update_device_list(self, _alive_set):
        print(_alive_set)


    def _device_probe_procedure(self):
        addrs = self.watched_addrs.copy()
        result_queue = Queue()

        def fibre_gen(addrs):
            for addr, mask in addrs:
                addr_int = IPv4ToInt(addr)
                mask_int = IPv4ToInt(mask)
                for host_int in range(0, (mask_int ^ 0xFFFFFFFF) + 1):
                    probe_addr = IntToIPv4((addr_int & mask_int) | host_int)
                    yield gevent.spawn(_probe_fibre, _addr = probe_addr, _timeout = 5, _queue = result_queue, _interface = self.interface)
                    

        fibres = weakref.WeakSet()
        alive_set = set()
        print('start fibres.')
        for fibre in fibre_gen(addrs):
            fibres.add(fibre)
        print('fibres started.')

        gevent.wait(list(fibres))

        while not result_queue.empty():
            probed_addr, _, is_alive = result_queue.get(block=False)
            if is_alive:
                alive_set.add(probed_addr)

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
                        , max_instances = 1
                        , trigger = 'interval'
                        , seconds = 30)

        self.hwaddr_renew_job = self.sched.add_job(
                        self._hwaddr_renew_procedure
                        , name = 'HWAddr renew.'
                        , max_instances = 1
                        , trigger = 'interval'
                        , seconds = 300)

        self.sched.start()
                    
        return True



class LANDeviceList:
    def __init__(self, _redis_url):
        pass

