import hashlib
import uuid
import json

from flask import current_app
from base64 import b64encode
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
    ACCEPTABLE_TOKEN_TYPES = frozenset(['auth', 'application'])

    TOKEN_CLASS_REGISTRY = {}

    @staticmethod
    def RegisterAPITokenClass(_class):
        if _class.REGISTER_CLASS_NAME in APIToken.TOKEN_CLASS_REGISTRY:
            raise DuplicatedTokenType('API Token Class %s already exists.' % _name)
        APIToken.TOKEN_CLASS_REGISTRY[_class.REGISTER_CLASS_NAME] = _class


    def __init__(self, _token_type, _key_getter = flask_jwt_key_getter, *args, **kwargs):
        if _token_type not in ACCEPTABLE_TOKEN_TYPES:
            raise InvalidAPITokenType('Unsupported API Token type: ' % _token_type)
        self._key_getter = _key_getter
        self._token_type = _token_type
        self._token_id = str(uuid.uuid4()).replace('-', '')
        super().__init__(*args, **kwargs)


    @property
    def IssueAt(self):
        if 'iat' not in self._claims\
            or isinstance(self._claims['iat'], int):
            return None
        return datetime.fromtimestmp(self._claims['iat'])


    def SetDefaultClaims(self):
        if 'iat' not in self._claims \
            or not isinstance(self._claims['iat'], int):
            self._claims['iat'] = int(datetime.now().timestamp())
        self._claims['usage'] = self._token_type
        self._claims['jti'] = self._token_id

        
    def make_signed_token(self):
        self.SetDefaultClaims()
        return super().make_signed_token(self._key_getter())



class ProxyToken(APIToken):
    REGISTER_CLASS_NAME = 'proxy'

    def __init__(self, _nid, _avaliable_period = 10, _request_id = None, *args, **kwargs):
        self._avaliable_period = _avaliable_period
        if not isinstance(request_id, str):
            self._request_id = _request_id
        else:
            self._request_id = str(uuid.uuid4()).replace('-', '')
        self.nid = _nid
        super().__init__(_token_type = ProxyToken.REGISTER_CLASS_NAME, *arg, **kwargs)


    def SetDefaultClaims(self):
        super().SetDefaultClaims()
        self._claims['exp'] = ((self.IssueAt + timedelta(seconds = self._avaliable_period)).timestamp())


APIToken.RegisterAPITokenClass(ProxyToken)



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


