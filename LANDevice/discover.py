import re
import gevent
import weakref
import netifaces
import socket
import redis
import uuid

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
    '''
        Liveness-probing fibre 
    '''
    mac = ''
    try: 
        mac = ARPRequest(_interface, _addr, _timeout * 1000)
    except socket.timeout as e:
        pass

    if mac != '':
        _queue.put((_addr, mac, True))
    else:
        _queue.put((_addr, mac, False))


class LANDevicePublish:
    
    def __init__(self, _config):
        '''
            Initialize new device list publishing port.
        '''
        self._config = _config
        self._naked_id = str(uuid.uuid4()).replace('-', '')
        self._publisher_set = _config.redis_prefix + '_landev_publishers'
        self._publish_set = _config.redis_prefix + '_publish_' + self._naked_id
        self._event_listener_set = _config.redis_prefix + '_listeners' 
        self._redis = redis.Redis(host = _config.redis_host, port = _config.redis_port)
        #self._alive_tracker = weakref.WeakValueDirectory()
        self._liveness_info = {} 
        self._init_redis_publisher_list()
        


    def _init_redis_publisher_list(self):
        '''
            Initialize all redis data structure for the simple subscriber-publisher system.
        '''
        # KEYS:
        #   1:  publisher_set
        #   2:  publish_set
        # ARGV:
        #   1:  Expire time for publish_set in seconds.
        REDIS_INIT_LUA = '''
            redis.call('sadd', KEYS[1], KEYS[2])
            redis.call('sadd', KEYS[2], '')
            redis.call('expire', KEYS[2], ARGV[1])
            return 1
        '''
        # Empty entry to keep myself alive in pushlisher set
        self._redis.eval(REDIS_INIT_LUA, 2, self._publisher_set, self._publish_set, self._config.probe_interval * 2)

        
    def PublishDevices(self, _devices):
        '''
            Publish new device list.

            :params:
                _devices    (ip, mac) tuple pairs for devices.

        '''
        devices = ['%s,%s' % (ip, mac) for ip, mac in _devices]
        # KEYS:
        #   1: publish_set 
        #   2: Expire time for publish_set in seconds.
        #   3: listener_set
        # ARGV:
        #   device information entries
        REDIS_UPDATE_LUA = '''
            redis.call('sadd', KEYS[1] .. '_new_set', unpack(ARGV))
            local joined = redis.call('sdiff', KEYS[1] .. '_new_set', KEYS[1])
            local left = redis.call('sdiff', KEYS[1], KEYS[1] .. '_new_set')
            redis.call('del', KEYS[1])
            redis.call('rename', KEYS[1] .. '_new_set', KEYS[1])
            redis.call('expire', KEYS[1], KEYS[2])

            local listeners = redis.call('smembers', KEYS[3])
            for i = 1, #listeners, 1 do
                repeat 
                    if false == redis.call('get', listeners[i] .. '_expire') then
                        redis.call('srem', KEYS[3], listeners[i])
                        break
                    end
                    if #joined > 0 then
                        for i = 1, #joined, 1 do
                            joined[i] = 'joi|' .. joined[i]
                        end
                        redis.call('rpush', listeners[i], unpack(joined))
                    end
                    if #left > 0 then
                        for i = 1, #left, 1 do
                            left[i] = 'lef|' .. left[i]
                        end
                        redis.call('rpush', listeners[i], unpack(left))
                    end
                until true
            end
            return #ARGV
        '''
        self._redis.eval(REDIS_UPDATE_LUA, 3, self._publish_set, self._config.probe_interval * 2, self._event_listener_set, *devices)



class LANDeviceProber:

    def __init__(self, _config):
        '''
            Initinalize LANDeviceProber

            :params:
                _config         LANDeviceProberConfig instance
                                Contain configures variables of prober.
        '''
        self.publish_port = LANDevicePublish(_config)
        self._config = _config
        self.sem_running = Semaphore()
        self.sem_stop = Semaphore()

        self.sem = Semaphore()
        self.watched_addrs = set()

        self.interface = _config.interface
        if self._update_address() is None:
            raise InterfaceNotFoundError("Interface %s not found." % _config.interface)
        self.sched = GeventScheduler()


    def _update_address(self):
        '''
            Update target address to probe according to newly network configures.
        '''
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
        '''
            Entrypoint of address updating procedure.
        '''
        self._update_address()


    def _update_device_list(self, _alive_set):
        '''
            Called when a new liveness-probing result generated.
        '''
        print(_alive_set)
        self.publish_port.PublishDevices(_alive_set)


    def _device_liveness_tracker(self, _ip, _mac):
        '''
            Track the state of specified online device.

            :params:
                _ip         IPv4 Address string.
                _mac        MAC Address string.
        '''
        pass
        

    def _device_probe_procedure_lead(self):
        '''
            Lead procedure of liveness probing.
            Collect probing results and refresh device information.
        '''
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
        for fibre in fibre_gen(addrs):
            fibres.add(fibre)

        gevent.wait(list(fibres))

        while not result_queue.empty():
            probed_addr, mac, is_alive = result_queue.get(block=False)
            if is_alive:
                alive_set.add((probed_addr, mac))

        for fibre in fibres:
            gevent.kill(fibre)

        self._update_device_list(alive_set)


    def Stop(self):
        '''
            Stop prober
        '''
        if not self.sem_stop.acquire(blocking = False):
            return False
        self.ifce_update_job.remove()
        self.device_probe_job.remove()
        self.ifce_update_job = None
        self.device_probe_job = None
        self.sem_running.release()
        return True
        

    def Run(self):
        '''
            Start prober and wait for exiting.
        '''
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
                        self._device_probe_procedure_lead
                        , name = 'Probe devices.'
                        , max_instances = 1
                        , trigger = 'interval'
                        , seconds = self._config.probe_interval)


        self.sched.start()
                    
        return True

