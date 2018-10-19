import os
import os.path

class LANDeviceProberConfig:

    VAR_LIST = frozenset([
            ('probe_timeout', 'LAN_DEV_LIVENESS_PROBE_TIMEOUT', int)
            , ('probe_interval', 'LAN_DEV_LIVENESS_PROBE_INTERVAL', int)
            , ('redis_host', 'LAN_DEV_REDIS_HOST', str)
            , ('redis_port', 'LAN_DEV_REDIS_PORT', int)
            , ('interface', "LAN_DEV_INTERFACE", str)
            , ('redis_prefix', "LAN_DEV_REDIS_PROBER_IDENT_PREFIX", str)
            , ('track_interval', 'LAN_DEV_LIVENESS_TRACK_INTERVAL', int)
        ])

    probe_timeout = 5
    probe_interval = 30
    track_interval = 5
    redis_host = 'localhost'
    redis_port = 6379
    redis_prefix = '123'
    interface = ''

    def FromEnv(self, _env):
        '''
            Load configures from file whose path is specified by Environment Variable _env.

            :params:
                _env        Environment variable name.
        '''
        if _env not in os.environ:
            raise ValueError('Environment variable %s not exists' % _env)
        return self.FromFile(os.environ[_env])


    def FromFile(self, _path):
        '''
            Load configures from file.

            :params:
                _path       File path.
        '''
        config_context = {}
        exec(compile(open(_path, 'rt').read(), os.path.basename(_path), 'exec'), config_context)
        return self.FromDict(config_context)


    def FromDict(self, _dict):
        '''
            Load configure from python dict.

            :params:
                _dict       Dict.
        '''
        for ident, cfg_ident, var_type in LANDeviceProberConfig.VAR_LIST:
            if cfg_ident in _dict:
                if type(_dict[cfg_ident]) is not var_type:
                    raise ValueError('Configure variable %s has wrong type %s, expecting %s' % (cfg_ident, type(_dict[cfg_ident]), var_type.__name__))
                setattr(self, ident, _dict[cfg_ident])
        
