#
#   LANDevice Port to read device list and watch device event
#

import redis
import uuid

from .config import LANDeviceProberConfig

class DeviceList:
    def __init__(self, _config):
        '''
            Create a Device list Port with specified configure.
        '''
        self._config = _config
        self._redis = redis.Redis(host = _config.redis_host, port = _config.redis_port)
        

    def Snapshot(self):
        '''
            Create a snapshot of device list.

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
        publish_list = self._redis.eval(REDIS_GET_LUA, 1, self._config.redis_prefix + '_landev_publishers')
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
        

    def NewListener(self):
        '''
            Create New Device Event listener.
        '''
        return DeviceListener(self._config)



class DeviceListener:
    MAP_EVENT = {
        'joi': 'join'
        , 'lef' : 'left'
    }

    def __init__(self, _config):
        '''
            Create new device event listener

            :params:
                _config         LANDeviceProberConfig instance.
        '''
        self._config = _config
        self._redis = redis.Redis(host = _config.redis_host, port = _config.redis_port)
        self._listener_id = str(uuid.uuid4()).replace('-', '')


    def Register(self):
        '''
            Register listener to redis.
        '''
        # KEYS:
        #   1: redis_prefix 
        #   2: listener_name
        REDIS_REG_LUA = '''
            redis.call('sadd', KEYS[1] .. '_listeners', KEYS[1] .. '_' .. KEYS[2])
            redis.call('set',  KEYS[1] .. '_' .. KEYS[2] .. '_expire', 1, 'EX', '60')
            return 1
        '''
        self._redis.eval(REDIS_REG_LUA, 2, self._config.redis_prefix, self._listener_id)


    def Watch(self):
        '''
            Watch for a new event.

            :return:
                event, ip, mac
                event can be 'join' or 'left'
        '''

        ip, mac = None, None
        while True:
            self.Register()
            event = self._redis.blpop(self._config.redis_prefix + '_' + self._listener_id, '30')
            if event != None:
                event = event[1].decode('ascii')
                evt = DeviceListener.MAP_EVENT.get(event[:3], None)
                if evt is None:
                    continue
                splited = event[4:].split(',')
                if len(splited) != 3:
                    continue
                ip, mac, nid = splited
                break
        return evt, ip, mac, nid
