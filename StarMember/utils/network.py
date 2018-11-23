import re
import uuid
import redis

from StarMember.agent.utils import IPv4ToInt
from flask import current_app

ID_FMT_RE = re.compile('^[a-f0-9]{32}$')


def lazy_redis_store_getter():
    return current_app.redis_store

class InvalidNetworkIDError(Exception):
    pass


class Network:

    @staticmethod
    def FromIP(_ip, _redis_storage_getter = lazy_redis_store_getter):
        '''
            Find the Network the that IP belong to.

            :params:
                _ip         IP.

            :return:
                return Network instance if Network of the IP is known.
                Otherwise, return None.
        '''
        redis_storage = _redis_storage_getter()
        if redis_storage is None:
            raise RuntimeError('Cannot access to redis.')
        nid = redis_storage.get(current_app.config['LAN_DEV_REDIS_PROBER_IDENT_PREFIX'] + '_gateway_map_' + _ip.replace('.', '_'))
        if nid:
            nid = nid.decode('utf8')
        if nid is None or not check_network_id(nid):
            return None
        return Network(nid)
     
   
    def __init__(self, _id, _register = False, _redis_getter = lazy_redis_store_getter):
        '''
            Open Network for information.
        '''
        self._redis = _redis_getter()
        if not check_network_id(_id):
            raise InvalidNetworkIDError('Wrong network ID format.')

        self._id = _id
        if not self.Verify(_raise_exception = not _register):
            if not self.InitNetworkInfo():
                raise RuntimeError('Cannot register network.')


    def InitNetworkInfo(self):
        '''
            Initialize Network Info.
        '''
        self._redis.hmset(self._redis_info_key, {
            'AgentLocalIP': ''
            , 'NetworkPublishIP': ''
            , 'ID': self._id
            , 'AgentLocalPort': 80
        })
        return self.Verify(_raise_exception = False)

    @property
    def PublishIP(self):
        return self._redis.hget(self._redis_info_key, 'NetworkPublishIP')

    @PublishIP.setter
    def PublishIP(self, _ip):
        self._redis.hset(self._redis_info_key, 'NetworkPublishIP', _ip)
        self._redis.set(self._redis_gateway_map_prefix + '_' + _ip.replace('.', '_'), self._id)

    @property
    def _redis_info_key(self):
        return current_app.config['LAN_DEV_REDIS_PROBER_IDENT_PREFIX'] + '_local_network_' + self._id + '_info'

    @property
    def _redis_gateway_map_prefix(self):
        return current_app.config['LAN_DEV_REDIS_PROBER_IDENT_PREFIX'] + '_gateway_map'

    @property
    def _redis_publish_set_key(self):
        return current_app.config['LAN_DEV_REDIS_PROBER_IDENT_PREFIX'] + '_publish_' + self._id

    @property
    def _redis_publisher_set_key(self):
        return current_app.config['LAN_DEV_REDIS_PROBER_IDENT_PREFIX'] + '_landev_publishers'

    @property
    def _redis_publish_listener_key(self):
        return current_app.config['LAN_DEV_REDIS_PROBER_IDENT_PREFIX'] + '_listeners'

    @property
    def LocalAgentIP(self):
        return self._redis.hget(self._redis_info_key, 'AgentLocalIP').decode('utf8')

    @property
    def ProbeInterval(self):
        return current_app.config.get('LAN_DEV_LIVENESS_PROBE_INTERVAL', 30)

    @LocalAgentIP.setter
    def LocalAgentIP(self, _IP):
        self._redis.hset(self._redis_info_key, 'AgentLocalIP', _IP)

    @property
    def LocalAgentPort(self):
        raw = self._redis.hget(self._redis_info_key, 'AgentLocalPort')
        if raw is None:
            return None
        return int(raw.decode())

    @LocalAgentPort.setter
    def LocalAgentPort(self, _port):
        if not isinstance(_port, int):
            raise ValueError('Port should be an integar.')
        self._redis.hset(self._redis_info_key, 'AgentLocalPort', _port)

    @property
    def ID(self):
        return self._id

    def Verify(self, _raise_exception = False):
        '''
            Check whether ID specified Network is registered.

            :return:
                True or False
        '''
        exists = self._redis.exists(self._redis_info_key)
        if exists < 1:
            if _raise_exception:
                raise InvalidNetworkIDError('Network unregistered.')
            return False 

        return True

    def _register_publish_set(self):
        '''
            Initialize all redis data structure for the simple subscriber-publisher system.
        '''
        REDIS_INIT_LUA = '''
            redis.call('sadd', KEYS[1], KEYS[2])
            redis.call('sadd', KEYS[2], '')
            redis.call('expire', KEYS[2], ARGV[1])
            return 1
        '''
        self._redis.eval(REDIS_INIT_LUA, 2, self._redis_publisher_set_key, self._redis_publish_set_key, self.ProbeInterval * 2)
        
        

    def UpdateDevices(self, _devices):
        '''
            Update device list and publish device events.
        '''
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

        for item in _devices:
            if not isinstance(item, (tuple, list)) \
               or len(item) != 2 \
               or not isinstance(item[0], str) \
               or not isinstance(item[1], str) :
                raise ValueError('Devices list is wrongly formated.')
        self._register_publish_set()
        devices = [('%s,%s,' + self._id) % (ip, mac) for ip, mac in _devices]

        self._redis.eval(REDIS_UPDATE_LUA, 3, self._redis_publish_set_key, self.ProbeInterval * 2, self._redis_publish_listener_key, *devices)
        


    def Unregister(self):
        '''
            Unregister network.
        '''
        pass

class NetworkList:
    def __init__(self, _redis_host, _redis_port, _redis_prefix):
        '''
            New Network list interface instance.
        '''
        self._prefix = _redis_prefix
        self._redis = redis.Redis(
                host = _redis_host
                , port = _redis_port)


    def Snapshot(self):
        '''
            Create a snapshot of device list. (OLD)

            :return:
                A dict with MAC key and a set of IPv4 address as value.
                {
                    'AA:BB:CC:DD:EE:FF': ('af8fb2c15d3249c5b5d9dd9e7e48f51e' ,set(['1.2.3.4', '5.6.7.8', ...]))
                    , ...
                }
        '''
        # KEYS:
        #   1: publish_set 
        REDIS_GET_LUA = '''
            local publishes = redis.call('smembers', KEYS[1])
            if false == publishes or #publishes == 0 then
                return {}
            end

            local final_devices = {}
            for i = 1, #publishes, 1 do 
                repeat
                    local devices = redis.call('smembers', publishes[i])
                    if false == devices or #devices == 0 then
                        redis.call('srem', KEYS[1], publishes[i])
                        break
                    end
                    for j = 1, #devices, 1 do
                        repeat
                            if devices[j] == '' then
                                break
                            end
                            table.insert(final_devices, devices[j])
                        until true
                    end
                until true
            end
            return final_devices
        '''
        devices = {}
        publish_list = self._redis.eval(REDIS_GET_LUA, 1, self._prefix + '_landev_publishers')
        for raw_item in publish_list:
            splited = raw_item.decode('ascii').split(',')
            if len(splited) != 3:
                print('Wrong publish format: %s' % raw_item)
                continue
            ip, mac, nid = splited
            if mac not in devices:
                ip_set = set()
                devices[mac] = (nid, ip_set)
            else:
                _, ip_set = devices[mac]
            ip_set.add(ip)
        return devices

    def Snapshot2(self):
        '''
            Create a snapshot of device list

            :return:
                {
                    'af8fb2c15d3249c5b5d9dd9e7e48f51e': {
                        'AA:BB:CC:DD:EE:FF': set(['1.2.3.4', '5.6.7.8'])
                        , ...
                    }
                    , ...
                }
        '''
        # KEYS:
        #   1: publish_set 
        REDIS_GET_LUA = '''
            local publishes = redis.call('smembers', KEYS[1])
            if false == publishes or #publishes == 0 then
                return {}
            end

            local final_devices = {}
            for i = 1, #publishes, 1 do 
                repeat
                    local devices = redis.call('smembers', publishes[i])
                    if false == devices or #devices == 0 then
                        redis.call('srem', KEYS[1], publishes[i])
                        break
                    end
                    for j = 1, #devices, 1 do
                        repeat
                            if devices[j] == '' then
                                break
                            end
                            table.insert(final_devices, devices[j])
                        until true
                    end
                until true
            end
            return final_devices
        '''
        devices = {}

        publish_list = self._redis.eval(REDIS_GET_LUA, 1, self._prefix + '_landev_publishers')
        for raw_item in publish_list:
            splited = raw_item.decode('ascii').split(',')
            if len(splited) != 3:
                print('Wrong publish format: %s' % raw_item)
                continue
            ip, mac, nid = splited

            if nid not in devices:
                devices[nid] = {}
            net = devices[nid]
            if mac not in net:
                net[mac] = set()
            ips = net[mac]
            ips.add(ip)

        return devices


def new_network_id():
    '''
        Create new network ID.

        :return:
            ID string with length of 32 in character A-Z and 0-9.
            Like: e711230222eb453f93c72d4db2ea0ea3
    '''
    return str(uuid.uuid4()).replace('-', '')


def check_network_id(_id):
    '''
        Check network ID format.

        :return:
            True or False
    '''
    return ID_FMT_RE.match(_id) is not None


RE_MAC_PATTEN = re.compile('^(?:[0-9a-fA-F]{2}:){5}(?:[0-9a-fA-F]{2})$')

def MACToInt(_mac):
    '''
        Convert MAC address to int
    '''
    if not RE_MAC_PATTEN.match(_mac):
        raise ValueError('Invalid MAC format.')

    return int(_mac.replace(':', ''), 16)

def IntToMAC(_mac):
    '''
        Convert int to MAC address
    '''
    if _mac > 0xFFFFFFFFFFFF:
        return ValueError('MAC integer is too big.')
    digits = list('%012x' % _mac)
    return ':'.join([digits[i] + digits[i+1] for i in range(0, len(digits), 2)])
