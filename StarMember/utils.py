import hashlib
import uuid
import json

from base64 import b64encode
from flask import current_app
from datetime import datetime
from jwcrypto.jwt import JWT, JWTExpired
from jwcrypto.jws import InvalidJWSSignature
from jwcrypto.common import json_decode

ACCEPTABLE_TOKEN_TYPES = frozenset(['auth', 'application'])

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
    except InvalidJWSSignature or JWTExpired or ValueError as e:
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
