import os
import uuid
import json

from datetime import datetime
from jwcrypto.jwt import JWT, JWTExpired
from jwcrypto.jws import InvalidJWSSignature
from jwcrypto.common import json_decode
from flask import current_app

ACCEPTABLE_TOKEN_TYPES = frozenset(['auth', 'application'])

def new_encoded_token(_user, _application_verbs, _user_verb, _token_type = 'auth', _not_before = None, _expire = None):
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
            (is_valid, token_type, username, expire_timestamp, tuple of avaliable verbs)
    '''
    key = current_app.jwt_key
    try:
        token = JWT(key = key, jwt = _encoded_token)
    except InvalidJWSSignature and JWTExpired as e:
        return False, None, None, None

    claims = json.loads(token.claims)
    username = claims.get('username', None)
    verbs = claims.get('verbs', None)
    expire = claims.get('exp', None)
    token_type = claims.get('usage', None)

    if username is None or verbs is None or token_type is None:
        return False, None, None, expire, None

    try:
        return True, token_type, username, expire, set(verbs)
    except TypeError as e:
        return False, token_type, None, None, None
