import re
import gevent
import weakref
import netifaces
import socket
import uuid
import requests
import os

from datetime import datetime, timedelta
from apscheduler.schedulers.gevent import GeventScheduler
from gevent.lock import Semaphore
from gevent.event import Event
from gevent.queue import Queue, Empty
from .ping import ping
from .arp import ARPRequest
from StarMember.agent.error import InterfaceNotFoundError
from StarMember.agent.utils import IPv4ToInt, IntToIPv4
from StarMember.agent.config import LANDeviceProberConfig
from traceback import print_exc

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
            Initinalize new device list publishing port.
        '''
        self._config = _config
        self._nid = None


    @property
    def NetworkID(self):
        while self._nid is None:
            try:
                io = open(self._config.network_id_file, 'rt')
            except FileNotFoundError as e:
                io = None
            
            if io is None:
                try:
                    resp = requests.post(self._config.nid_register_api, json = {"register_token": self._config.register_token})
                    result = resp.json()
                    if result['code'] == 0:
                        self._nid = result['data']['network_id']
                except requests.ConnectionError as e:
                    print_exc()

                if self._nid is None:
                    gevent.sleep(5)
                    continue

                io = open(self._config.network_id_file, 'wt')
                io.write(self._nid)
            else:
                self._nid = io.read()

            io.close()
            os.chmod(self._config.network_id_file, 0o600)

        return self._nid


    def PublishDevices(self, _devices):
        '''
            Publish new device list.

            :params:
                _devices        (ip, mac) tuple pairs for devices.
        '''
        try:
            resp = requests.post(self._config.network_api + '/%s' % self.NetworkID + '/device', allow_redirects = True, json = {
                'devices' : list(_devices)
            })
            result = resp.json()
            print('Publish result: %s' % result)
        except requests.ConnectionError as e:
            print('Publish fails with exception:')
            print_exc()
    
        

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
        self.publish_local_ip = ''
        self._device_last_alive = {} # mac -> (timestamp, ip -> tracker (Weak))
        self._alive_tracker = weakref.WeakValueDictionary() # ip -> tracker
        self._tracker_info = weakref.WeakKeyDictionary() # tracker -> mac

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
        inet_addr_info = ifce_addrs[netifaces.AF_INET]
        new_watched_addrs = set([(info['addr'], info['netmask']) for info in inet_addr_info]) 
        if inet_addr_info:
            self.publish_local_ip = inet_addr_info[0]['addr']

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

        cur_time = datetime.now()
        to_remove = [mac for mac, info in self._device_last_alive.items() \
            if cur_time > info[0] + 2 * timedelta(seconds = self._config.probe_interval)]
        for mac in to_remove:
            print('Device leave: %s' % mac)
            del self._device_last_alive[mac]

                
        device_ip_bind = {}
        for ip, mac in _alive_set:
            ip_set = device_ip_bind.get(ip, None)
            if ip_set is None:
                ip_set = set()
                device_ip_bind[mac] = ip_set
            ip_set.add(ip)

        # Start trackers
        for mac, ip_set in device_ip_bind.items():
            _, trackers = self._device_last_alive.get(mac, (None, None))
            if trackers is None:
                print('Join: %s' % mac)
                trackers = weakref.WeakValueDictionary()
                self._device_last_alive[mac] = [datetime.now(), trackers]

            for ip in ip_set:
                tracker = trackers.get(ip, None)
                if tracker is None:
                    tracker = gevent.spawn(self._device_liveness_tracker, ip)
                    trackers[ip] = tracker
                    self._alive_tracker[ip] = tracker
                    self._tracker_info[tracker] = mac
                    print('Device presents at %s' % ip)
                elif mac != self._tracker_info[tracker]:
                    self._tracker_info[tracker] = mac
        new_alive_set = set([(ip, mac) for mac, (_, trackers) in self._device_last_alive.items() for ip in trackers.keys()])
        self.publish_port.PublishDevices(new_alive_set)


    def _device_liveness_tracker(self, _ip):
        '''
            Track the state of specified online device

            :params:
                _ip         IPv4 Address string.
                _mac        MAC Address string.
        '''
        myself = self._alive_tracker.get(_ip)
        if myself is None:
            raise RuntimeError('Cannot find myself at tracker dictionary.')

        while True:
            mac = self._tracker_info.get(myself, None)
            cur_time = datetime.now()
            if mac is None:
                raise RuntimeError('Tracker is not bind with mac.')
            timestamp, _ = self._device_last_alive.get(mac, (None, None))
            if timestamp is None \
                or cur_time >= timestamp + 2 * timedelta(seconds = self._config.probe_interval):
                break
            #print('liveness probe: %s' % _ip)
            delay = ping(_ip, self._config.probe_timeout)
            #print('liveness probe result %s for %s' % (str(delay), _ip))
            if delay is not None:
                #print('Alive : %s -> %s ' % (_ip, mac))
                cur_time = datetime.now()
                self._device_last_alive[mac][0] = cur_time
            gevent.sleep(self._config.track_interval)
        print('Leave: %s' % _ip)


    def _agent_keepalive(self):
        '''
            Upload local network info.
        '''
        resp = requests.post(self._config.network_api + '/%s' % self.publish_port.NetworkID + '/liveness', json = {
            'local_ip': self.publish_local_ip
            , 'local_port': self._config.server_port
        })
        print('Keepalive : %s ' % resp.json())
        

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

        self.keepalive_job = self.sched.add_job(
                        self._agent_keepalive
                        , name = 'Keepalive.'
                        , max_instances = 1
                        , trigger = 'interval'
                        , seconds = 10)

        self.device_probe_job.modify(next_run_time = datetime.now())

        self.sched.start()
                    
        return True

