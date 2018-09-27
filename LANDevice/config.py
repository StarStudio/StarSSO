import os
import os.path

class LANDeviceProberConfig:

    VAR_LIST = frozenset([
            ('probe_timeout', 'LAN_DEV_LIVENESS_PROBE_TIMEOUT', int)
            , ('probe_interval', 'LAN_DEV_LIVENESS_PROBE_INTERVAL', int)
            , ('redis', 'REDIS_URL', str)
            , ('interface', "LAN_DEV_INTERFACE", str)
        ])

    probe_timeout = 5
    probe_interval = 30
    redis = ''
    interface = ''

    def FromEnv(self, _env):
        if _env not in os.environ:
            raise ValueError('Environment variable %s not exists' % _env)
        return self.FromFile(os.environ[_env])


    def FromFile(self, _path):
        config_context = {}
        exec(compile(open(_path, 'rt').read(), os.path.basename(_path), 'exec'), config_context)
        return self.FromDict(config_context)


    def FromDict(self, _dict):
        for ident, cfg_ident, var_type in LANDeviceProberConfig.VAR_LIST:
            if cfg_ident in _dict:
                if type(_dict[cfg_ident]) is not var_type:
                    raise ValueError('Configure variable %s has wrong type %s, expecting %s' % (cfg_ident, type(_dict[cfg_ident]), var_type.__name__))
                setattr(self, ident, _dict[cfg_ident])
        
