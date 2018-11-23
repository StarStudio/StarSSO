import os
import os.path

class CheckBotConfig:

    VAR_LIST = frozenset([
            ('mysql_host', "MYSQL_DATABASE_HOST", str)
            , ('mysql_port', 'MYSQL_DATABASE_PORT', int)
            , ('mysql_password', 'MYSQL_DATABASE_PASSWORD', (str, type(None)))
            , ('mysql_db', 'MYSQL_DATABASE_DB', str)
            , ('mysql_charset', 'MYSQL_DATABASE_CHARSET', str)
            , ('redis_host', 'REDIS_HOST', str)
            , ('redis_port', 'REDIS_PORT', int)
            , ('redis_prefix', 'LAN_DEV_REDIS_PROBER_IDENT_PREFIX', str)
        ])

    mysql_port = 3306
    mysql_host = 'localhost'
    mysql_user = 'root'
    mysql_password = None
    mysql_db = 'starstudio'
    mysql_charset = 'utf8'
    redis_host = 'localhost'
    redis_port = 6379
    redis_prefix = 'LANDEV_DEFAULT'

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
        for ident, cfg_ident, var_type in CheckBotConfig.VAR_LIST:
            if cfg_ident in _dict:
                if not isinstance(_dict[cfg_ident], var_type):
                    raise ValueError('Configure variable %s has wrong type %s, expecting %s' % (cfg_ident, type(_dict[cfg_ident]), var_type))
                setattr(self, ident, _dict[cfg_ident])
        
