import re
import uuid

from flask import current_app

TOKEN_RE = re.compile('[a-f0-9]')

def token_to_redis_key(_token):
    '''
        Map token to redis key.

        :params:
            _token          Token to map.
        :return:
            Key string.
    '''
    return current_app.config['LAN_DEV_PREFIX'] + '_reg_token_' + _token

def new_register_token():
    '''
        Allocate new register token.

        :return:
            Token string with length of 32 in character A-Z and 0-9.
            Like: e711230222eb453f93c72d4db2ea0ea3
    '''
    return hex(uuid.uuid4()).replace('-', '')


def check_register_token(_token):
    '''
        Check if register token has right format.

        :params:
            _token          Token to check.

        :return:
            True or False
    '''
    return TOKEN_RE.match(_token) is not None


def verify_register_token(_token):
    '''
        Verify register token.

        :params:
            _token          Token to verify.

        :return:
            True or False
    '''
    if check_register_token(_token):
        return False

    exist = current_app.redis_store.get(token_to_redis_key(_token))
    if exist is not None:
        return True
    return False


def append_new_token(_token, _timeout = 86400):
    '''
        Append or Update register token.

        :params:
            _token          Token to append/update

    '''
    current_app.redis_store.set(token_to_redis_key, 1, ex = _timeout)
