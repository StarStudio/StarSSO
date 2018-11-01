import re
import uuid
from flask import current_app

ID_FMT_RE = re.compile('^[a-f0-9]{32}$')

def lazy_redis_store_getter():
    return current_app.redis_store

class InvalidNetworkIDError(Exception):
    pass


class Network:
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
        })
        return self.Verify(_raise_exception = False)

    @property
    def PublishIP(self):
        return self._redis.hget(self._redis_info_key, 'NetworkPublishIP')

    @PublishIP.setter
    def PublishIP(self, _ip):
        return self._redis.hset(self._redis_info_key, 'NetworkPublishIP', _ip)

    @property
    def _redis_info_key(self):
        return current_app.config['LAN_DEV_REDIS_PROBER_IDENT_PREFIX'] + '_local_network_' + self._id + '_info'

    @property
    def LocalAgentIP(self):
        return self._redis.hget(self._redis_info_key, 'AgentLocalIP')


    @LocalAgentIP.setter
    def LocalAgentIP(self, _IP):
        self._redis.hset(self._redis_info_key, 'AgentLocalIP', _IP)


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


    def UpdateDevices(self, _devices):
        '''
            Update device list and publish device events.
        '''
        for item in _devices:
            if not isinstance(item, (tuple, list)) \
               or len(item) != 2 \
               or not isinstance(item[0], str) \
               or not isinstance(item[1], str) :
                raise ValueError('_devices wrongly formated.')
        pass


    def Unregister(self):
        '''
            Unregister network.
        '''
        pass


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
