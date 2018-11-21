import yaml
import os

from jwcrypto.jwk import JWK
from jwcrypto.common import JWException
from base64 import b64encode
from os.path import isfile


def stringwise_representer(dumper, data):
    if isinstance(data, str) and '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', '%s' % data, style = '|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)
yaml.add_representer(str, stringwise_representer)


class ConfigureError(Exception):
    pass

class Config(dict):
    '''
        Base configure class.
    '''
    DEFAULT_VALUES = {
        ('token', 'key', 'storage'): 'conf'
        , ('token', 'key', 'public_permission'): 0o644
        , ('token', 'key', 'private_permission'): 0o600
        , ('token', 'config', 'auth', 'expire_timeout'): 86400
        , ('token', 'config', 'application', 'expire_timeout'): 3600

        , ('apiserver', 'password_salt', 'storage'): 'conf'
        , ('apiserver', 'password_salt', 'permission'): 0o600
        , ('apiserver', 'storage', 'host'): '127.0.0.1'
        , ('apiserver', 'storage', 'port'): 3306
        , ('apiserver', 'storage', 'user'): 'root'
        , ('apiserver', 'storage', 'password'): None
        , ('apiserver', 'storage', 'db'): 'starstudio'
        , ('apiserver', 'storage', 'charset'): 'utf8'
        , ('apiserver', 'access_control', 'register'): True
        , ('apiserver', 'access_control', 'anonymous_group_info'): False
        , ('apiserver', 'redis', 'host'): 'localhost'
        , ('apiserver', 'redis', 'port'): 6379
        , ('apiserver', 'redis', 'prefix'): 'LANDEV_DEFAULT'
        , ('apiserver', 'listen') : '0.0.0.0'
        , ('apiserver', 'port'): 10029
        , ('apiserver', 'access_control', 'user_initial_access'): ['auth', 'read_self', 'read_internal', 'read_other', 'write_self', 'read_group']
        , ('apiserver', 'access_control', 'app_initial_access'): ['auth', 'read_self']
        , ('apiserver', 'dashboard', 'url_root'): 'http://sso.local.com'

        , ('log', 'access'): 'access'
        , ('log', 'error'): 'error'
        , ('log', 'debug'): 'debug'

        , ('rpc',): '/var/run/starsso_rpc.sock'

        , ('agent', 'listen'): '0.0.0.0'
        , ('agent', 'port'): 8001
        , ('agent', 'apiserver_root'): 'http://sso.local.com'
        , ('agent', 'discover', 'track_interval'): 5
        , ('agent', 'discover', 'probe_interval'): 30
        , ('agent', 'discover', 'probe_timeout'): 30
        , ('agent', 'discover', 'interfaces'): 'wlp3s0'
    }

    def __init__(self, _raw = None):
        self._cfg = self.Load(_raw)


    def Load(self, _raw):
        '''
            Load configure.

            :params:
                
        '''
        if _raw is None or len(_raw) < 1:
            return self
        self.update(yaml.load(_raw))
        return self


    def LoadFromFile(self, _path):
        if not isfile(_path):
            os.makedirs(os.path.dirname(_path))
            open(_path, 'wt').close()
            return self

        return self.Load(open(_path, 'rt').read())

        

    def DumpToFile(self, _path):
        open(_path, 'wt').write(self.Dump())
            
        
    def Dump(self):
        '''
            Dump configure.
        '''
        
        return yaml.dump(dict(self), default_flow_style = False)

    @property
    def TokenPublicPEM(self):
        storage = self._get_default('token', 'key', 'storage', default = 'conf')
        if storage == 'conf':
            jwk_pem = self._get_default('token', 'key', 'public', default = '')
        elif storage == 'file':
            key_path = self._get_default('token', 'key', 'public', default = 'token_public.key')
            try:
                key_io = open(key_path, 'rt')
            except FileNotFoundError as e:
                raise e

            jwk_pem = key_io.read()
            key_io.close()
        else:
            raise ConfigureError('Unacceptable token key storage type: %s' % storage)
        if isinstance(jwk_pem, str):
            jwk_pem = jwk_pem.encode('ascii')
        return jwk_pem


    @TokenPublicPEM.setter
    def TokenPublicPEM(self, pem):
        if isinstance(pem, bytes):
            pem = pem.decode()
        storage = self._get_default('token', 'key', 'storage', default = 'conf')
        if storage == 'conf':
            jwk_pem = self._set_default('token', 'key', 'public', default = pem)
        elif storage == 'file':
            key_path = self._get_default('token', 'key', 'public', default = 'token_public.key')
            permission = self._get_default('token', 'key', 'public_permission', default = 0o644)
            key_io = open(key_path, 'wt')
            key_io = write(pem)
            key_io.close()
            os.chmod(key_path, permission)
        else:
            raise ConfigureError('Unacceptable token key storage type: %s' % storage)


    @property
    def TokenPrivatePEM(self):
        '''
            Load JWT Private key PEM.
        '''
        storage = self._get_default('token', 'key', 'storage', default = 'conf')
        if storage == 'conf':
            jwk_pem = self._get_default('token', 'key', 'private', default = '')
        elif storage == 'file':
            key_path = self._get_default('token', 'key', 'private', default = 'token_private.key')
            try:
                key_io = open(key_path, 'rb')
            except FileNotFoundError as e:
                raise e
            jwk_pem = key_io.read()
            key_io.close()
        else:
            raise ConfigureError('Unacceptable token key storage type: %s' % storage)
        if isinstance(jwk_pem, str):
            jwk_pem = jwk_pem.encode('ascii')
        return jwk_pem


    @TokenPrivatePEM.setter
    def TokenPrivatePEM(self, pem):
        if isinstance(pem, bytes):
            pem = pem.decode()

        storage = self._get_default('token', 'key', 'storage', default = 'conf')
        if storage == 'conf':
            jwk_pem = self._set_default('token', 'key', 'private', default = pem)
        elif storage == 'file':
            key_path = self._get_default('token', 'key', 'private', default = 'token_private.key')
            permission = self._get_default('token', 'key', 'private_permission', default = 0o600)
            key_io = open(key_path, 'wb')
            key_io = write(pem)
            key_io.close()
            os.chmod(key_path, permission)
        else:
            raise ConfigureError('Unacceptable token key storage type: %s' % storage)

    @property
    def TokenPEM(self):
        pem = self.TokenPrivatePEM
        if pem is not None and pem != '':
            return pem
        pem = self.TokenPublicPEM
        if pem is not None and pem != '':
            return pem
        return ''

    @property
    def UserInitialAccess(self):
        return self._get_default('apiserver', 'access_control', 'user_initial_access')
    

    @property
    def JWK(self):
        return self.GetJWK()

    def GetJWK(self, _auto_gen = False):
        '''
            Load Json Web Token key according to configure.

            :params:
                _auto_gen       Generate and replace wrong configure

            :return:
                jwcrypto.jwk.JWK instance.
                return None when any failure occured.
        '''
        jwk = JWK()
        pem = self.TokenPrivatePEM
        if pem is None or len(pem) < 1 :
            pem = self.TokenPublicPEM
        try:
            if isinstance(pem, bytes):
                if len(pem) < 1:
                    jwk = None
                else:
                    jwk.import_from_pem(pem)
            else:
                jwk = None
        except JWException as e:
            jwk = None

        if jwk is None and _auto_gen:
            jwk = JWK(generate = 'RSA', size = 4096)
            self.TokenPrivatePEM = jwk.export_to_pem(private_key = True, password = None)
            self.TokenPublicPEM = jwk.export_to_pem(private_key = False, password = None)
        return jwk


    def GetSalt(self, _auto_gen = False):
        '''
            Load password salt.
        '''
        storage = self._get_default('apiserver', 'password_salt', 'storage', default = 'conf')
        if storage == 'conf':
            salt_text = self._get_default('apiserver', 'password_salt', 'salt', default = '')
            if salt_text is None or salt_text is '':
                if not _auto_gen:
                    return ''
                salt = os.urandom(15)
                salt_text = b64encode(salt).decode('ascii')
                self._set_default('apiserver', 'password_salt', 'salt', default = salt_text)
        elif storage == 'file':
            salt_path = self._get_default('apiserver', 'password_salt', 'salt', default = 'account.salt')
            permission = self._get_default('apiserver', 'password_salt', 'permission', default = 0o600)
            try:
                salt_io = open(salt_path, 'rt')
            except FileNotFoundError as e:
                salt_io = None

            if salt_io is None:
                if not _auto_gen:
                    return ''
                salt_io = open(salt_path, 'wt')
                salt = os.urandom(15)
                salt_text = b64encode(salt).decode('ascii')
                salt_io.write(salt_text)
            else:
                salt_text = salt_io.read()
            salt_io.close()
            os.chmod(salt_path, permission)
        else:
            raise ConfigureError('Unacceptable storage type: %s' % storage)
        return salt_text


    def _get_default(self, *args, **kwargs):
        '''
            Get value from specified dict path.

            :example:
                _get_default('key1', 'key2', ..., 'keyN', default = 'Value')

                This call of _get_default tries to get self['key1']['key2']...['keyN'].
                If any key through the path doesn't exists, return 'Value'.
                
                The param 'defualt' is optional.
        '''
        prev = None
        this = self
        set_default = False
        for key in args:
            if key not in this:
                this[key] = {}
                set_default = True
            prev = this
            this = this.get(key)
        if set_default:
            this = kwargs.get('default', None)
            if this is None:
                this = Config.DEFAULT_VALUES.get(tuple(args), None)
            prev[key] = this
        return this

    def _set_default(self, *args, **kwargs):
        '''
            Set value to specified dict path.

            :example:
                _set_default('key1', 'key2', ..., 'keyN', default = 'Value')

                This call of _set_default set self['key1']['key2']...['keyN'] = 'Value'.
        '''
        prev = None
        this = self
        for key in args:
            if key not in this:
                this[key] = {}
            prev = this
            this = this.get(key)
        prev[args[-1]] = kwargs['default']


    @property
    def MasterWSGIConfig(self):
        self.GetJWK(_auto_gen = True)
        return {
            'ACCESS_LOG': self._get_default('log', 'access')
            , 'ERROR_LOG': self._get_default('log', 'error')
            , 'DEBUG_LOG': self._get_default('log', 'debug')
            , 'TOKEN_PEM': self.TokenPEM
            , 'SALT': self.GetSalt(_auto_gen = True)
            , 'AUTH_TOKEN_EXPIRE_DEFAULT': self._get_default('token', 'config', 'auth', 'expire_timeout')
            , 'APP_TOKEN_EXPIRE_DEFAULT': self._get_default('token', 'config', 'application', 'expire_timeout')
            , 'MYSQL_DATABASE_HOST': self._get_default('apiserver', 'storage', 'host')
            , 'MYSQL_DATABASE_PORT': self._get_default('apiserver', 'storage', 'port')
            , 'MYSQL_DATABASE_USER': self._get_default('apiserver', 'storage', 'user')
            , 'MYSQL_DATABASE_PASSWORD': self._get_default('apiserver', 'storage', 'password')
            , 'MYSQL_DATABASE_DB': self._get_default('apiserver', 'storage', 'db')
            , 'MYSQL_DATABASE_CHARSET': self._get_default('apiserver', 'storage', 'charset')
            , 'CONTROL_RPC': self._get_default('rpc')
            , 'ALLOW_REGISTER': self._get_default('apiserver', 'access_control', 'register')
            , 'ALLOW_ANONYMOUS_GROUP_INFO': self._get_default('apiserver', 'access_control', 'anonymous_group_info')
            , 'USER_INITIAL_ACCESS': self._get_default('apiserver', 'access_control', 'user_initial_access')
            , 'APP_INITIAL_ACCESS': self._get_default('apiserver', 'access_control', 'app_initial_access')
            , 'REDIS_HOST': self._get_default('apiserver', 'redis', 'host')
            , 'REDIS_PORT': self._get_default('apiserver', 'redis', 'port')
            , 'REDIS_DB': self._get_default('apiserver', 'redis', 'db')
            , 'SSO_WEB_REDIRECT_PREFIX': self._get_default('apiserver', 'dashboard', 'url_root')
            , 'SERVER_HOST': self._get_default('apiserver', 'listen')
            , 'SERVER_PORT': self._get_default('apiserver', 'port')
            , 'LAN_DEV_REDIS_PROBER_IDENT_PREFIX': self._get_default('apiserver', 'redis', 'prefix')
        }

    @property
    def AgentWSGIConfig(self):
        return {
            'SERVER_HOST': self._get_default('agent', 'listen')
            , 'SERVER_PORT': self._get_default('agent', 'port')
            , 'LAN_DEV_REGISTER_TOKEN': self._get_default('agent', 'register_token')
            , 'LAN_DEV_NETWORK_ID': self._get_default('agent', 'network_id')
            , 'LAN_DEV_APISERVER_DOMAIN': self._get_default('agent', 'apiserver_root')
            , 'LAN_DEV_LIVENESS_TRACK_INTERVAL': self._get_default('agent', 'discover', 'track_interval')
            , 'LAN_DEV_LIVENESS_PROBE_INTERVAL': self._get_default('agent', 'discover', 'probe_interval')
            , 'LAN_DEV_LIVENESS_PROBE_TIMEOUT': self._get_default('agent', 'discover', 'probe_timeout')
            , 'LAN_DEV_INTERFACE': self._get_default('agent', 'discover', 'interfaces')
            , 'TOKEN_PEM': self.TokenPEM
        }
