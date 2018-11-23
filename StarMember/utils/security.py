import hashlib
import uuid
import json

from flask import current_app
from base64 import b64encode, b64decode
from datetime import datetime, timedelta
from jwcrypto.jwt import JWT, JWTExpired
from jwcrypto.jws import InvalidJWSSignature
from jwcrypto.common import json_decode


ACCEPTABLE_TOKEN_TYPES = frozenset(['auth', 'application'])

def flask_jwt_key_getter():
    return current_app.jwt_key

    
def password_hash(_password):
    '''
        Hash password according to preloaded salt.

        :params:
            _password           password string to hash

        :return:
            base64-encoded string
    '''
    salted = hashlib.md5()
    salted.update((_password + current_app.digest_salt).encode('utf-8'))
    return b64encode(salted.digest()).decode('utf-8')


class InvalidAPITokenType(Exception):
    pass

class DuplicatedTokenType(Exception):
    pass


class APIToken(JWT):
    TOKEN_CLASS_REGISTRY = {}
    
    @staticmethod
    def RegisterAPITokenClass(_class):
        if _class.REGISTER_CLASS_NAME in APIToken.TOKEN_CLASS_REGISTRY:
            raise DuplicatedTokenType('API Token Class %s already exists.' % _name)
        APIToken.TOKEN_CLASS_REGISTRY[_class.REGISTER_CLASS_NAME] = _class

    @staticmethod
    def FromString(_raw):
        '''
            Load token from string.

            :params:
                _raw        String.

            :return:
                Load token from string.
        '''
        # Get token type and find registered class.
        try:
            claims = None
            if isinstance(_raw, str):
                parts = _raw.split('.')
                if len(parts) == 3:
                    claims = b64decode(parts[1] + '=' * (4 - (len(parts[1]) & 0x3))).decode()
                    claims = json.loads(claims)
        except json.JSONDecodeError as e:
            raise ValueError('Not a valid Token %s' % str(e))

        if claims is None or 'usage' not in claims or claims['usage'] not in APIToken.TOKEN_CLASS_REGISTRY:
            raise ValueError('Not a valid Token')
        return APIToken.TOKEN_CLASS_REGISTRY[claims['usage']](jwt = _raw)
        

    def __init__(self, _token_type = None, _timeout = None,_key_getter = flask_jwt_key_getter, **kwargs):
        if 'jwt' in kwargs:
            if 'key' not in kwargs:
                if _key_getter:
                    kwargs['key'] = flask_jwt_key_getter()

            super().__init__(**kwargs)
            return
        if _token_type not in APIToken.TOKEN_CLASS_REGISTRY:
            raise InvalidAPITokenType('Unsupported API Token type: %s' % _token_type)
        self._key_getter = _key_getter
        self._token_type = _token_type
        self._token_id = str(uuid.uuid4()).replace('-', '')
        self._issue_datetime = datetime.now()
        if 'header' not in kwargs:
            kwargs['header'] = {'alg': 'RS256', 'typ': 'JWT'}
        if 'claims' not in kwargs:
            kwargs['claims'] = {}
        else:
            if isinstance(kwargs['claims'], str):
                kwargs['claims'] = json.loads(kwargs['claims'])

        kwargs['claims'].update({
            'usage': _token_type
            , 'jti' : self._token_id
            , 'iat': int(self._issue_datetime.timestamp())
        })
        if isinstance(_timeout, int):
            kwargs['claims']['exp'] = int((self._issue_datetime + timedelta(seconds = _timeout)).timestamp())
        super().__init__(**kwargs)
            

    def make_signed_token(self):
        return super().make_signed_token(self._key_getter())

    @property
    def TokenType(self):
        if not self._claims:
            return ''
        claims = json_decode(self._claims)
        if 'usage' not in claims:
            return ''
        return claims['usage']



class ShimToken(APIToken):
    REGISTER_CLASS_NAME = 'shim'

    def __init__(self, _redirect = None, _request_id = None, _query_key = None, **kwargs):
        if 'jwt' in kwargs:
            super().__init__(**kwargs)
            if self.TokenType != ShimToken.REGISTER_CLASS_NAME:
                raise InvalidAPITokenType('Not a ShimToken.')
            return

        if 'claims' not in kwargs:
            kwargs['claims'] = {}
        
        if isinstance(kwargs['claims'], str):
            kwargs['claims'] = json.loads(kwargs['claims'])
        claims = kwargs['claims']

        if 'reqid' not in claims:
            if isinstance(_request_id, str):
                claims['reqid'] = _request_id
            else:
                claims['reqid'] = str(uuid.uuid4()).replace('-', '')

        if 'redir' not in claims:
            if isinstance(_redirect, str):
                claims['redir'] = _redirect

        if 'qk' not in claims:
            if isinstance(_query_key, str):
                claims['qk'] = _query_key
        super().__init__(_token_type = ShimToken.REGISTER_CLASS_NAME, **kwargs)


    @property
    def Redirect(self):
        claims = json_decode(self._claims)
        if 'redir' not in claims:
            return None
        return claims['redir']


    @property
    def RequestID(self):
        claims = json_decode(self._claims)
        if 'reqid' not in claims:
            return None
        return claims['reqid']


    @property
    def QueryKey(self):
        claims = json_decode(self._claims)
        if 'qk' not in claims:
            return None
        return claims['qk']



APIToken.RegisterAPITokenClass(ShimToken)


class ShimResponseToken(APIToken):
    REGISTER_CLASS_NAME = 'shimr'

    def __init__(self, _request_id = None, _network_id = None, _local_ip = None, **kwargs):
        if 'jwt' in kwargs:
            super().__init__(**kwargs)
            if self.TokenType != ShimResponseToken.REGISTER_CLASS_NAME:
                raise InvalidAPITokenType('Not a ShimToken.')
            return

        if 'claims' not in kwargs:
            kwargs['claims'] = {}

        if isinstance(kwargs['claims'], str):
            kwargs['claims'] = json.loads(kwargs['claims'])

        claims = kwargs['claims']
        if 'reqid' not in claims:
            if isinstance(_request_id, str):
                claims['reqid'] = _request_id

        if 'nid' not in claims:
            if isinstance(_network_id, str):
                claims['nid'] = _network_id

        if 'local' not in claims:
            if isinstance(_local_ip, str):
                claims['local'] = _local_ip

        super().__init__(_token_type = ShimResponseToken.REGISTER_CLASS_NAME, **kwargs)

    @property
    def RequestID(self):
        claims = json_decode(self._claims)
        if 'reqid' not in claims:
            return None
        return claims['reqid']

    @property
    def NetworkID(self):
        claims = json_decode(self._claims)
        if 'nid' not in claims:
            return None
        return claims['nid']

    @property
    def LocalIP(self):
        claims = json_decode(self._claims)
        if 'local' not in claims:
            return None
        return claims['local']


APIToken.RegisterAPITokenClass(ShimResponseToken)

def new_token(_json = {}, _key_getter = flask_jwt_key_getter, _available_period = None):
    '''
        Create an new Json Web Token with specified data.

        :params:
            _json               JSON-Serializable python object.
            _available_period   Avaliable period in seconds.
    '''
    

def new_encoded_token(_user, _user_id, _application_verbs, _user_verb, _token_type = 'auth', _not_before = None, _expire = None):
    '''
        Create an new Json Web Token with minimal access verbs and user infomation.

        :params:
            _user                           Username
            _application_verbs              Verbs owned by specfied application
            _user_verbs                     Verbs owned by user.
            _not_before         [Optional]  Time after which the token is avaliable.
                                            The type of _not_before can be datetime.datetime 
                                            or an timestamp (an integer)

        :return:
            Signed and Encoded Json Web Token in str.
    '''
    if _token_type not in ACCEPTABLE_TOKEN_TYPES:
        raise ValueError('No such token type: %s' % _token_type)

    _application_verbs = set(_application_verbs)
    _user_verb = set(_user_verb)
    target_verbs = _application_verbs.intersection(_user_verb)
    jwk = current_app.jwt_key

    claims = {
        'iat': int(datetime.now().timestamp())
        , 'jti': str(uuid.uuid4()).replace('-', '')
        , 'username': _user
        , 'user_id' : _user_id
        , 'verbs': list(_application_verbs)
        , 'usage' : _token_type
    }

    if _not_before is not None:
        if isinstance(_not_before, datetime):
            _not_before = int(_not_before.timestamp())
        claims['nbf'] = int(_not_before)
    if _expire is not None:
        if isinstance(_expire, datetime):
            _expire = int(_expire.timestamp())
        claims['exp'] = int(_expire)

    token = JWT(
            header={'alg': 'RS256', 'typ': 'JWT'}
            , claims = claims
        )

    token.make_signed_token(jwk)
    return token.serialize()


def decode_token(_encoded_token):
    '''
        Verify and extract information from Json Web Token.

        :params:
            _encoded_token      Encoded Json Web Token.

        :return:
            (is_valid, token_type, username, user_id, expire_timestamp, tuple of avaliable verbs)
    '''
    key = current_app.jwt_key
    try:
        token = JWT(key = key, jwt = _encoded_token)
    except (InvalidJWSSignature, JWTExpired, ValueError) as e:
        return False, None, None, None, None, None

    claims = json.loads(token.claims)
    username = claims.get('username', None)
    verbs = claims.get('verbs', None)
    expire = claims.get('exp', None)
    token_type = claims.get('usage', None)
    user_id = claims.get('user_id', None)

    if username is None or verbs is None or token_type is None:
        return False, None, None, None, None, None

    try:
        return True, token_type, username, user_id, expire, set(verbs)
    except TypeError as e:
        return False, None, None, None, None, None


