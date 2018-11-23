import re
import uuid

from flask import current_app

TOKEN_RE = re.compile('^[a-f0-9]{32}$')

def token_to_redis_key(_token):
    '''
        Map token to redis key.

        :params:
            _token          Token to map.
        :return:
            Key string.
    '''
    #print(current_app.config['LAN_DEV_REDIS_PROBER_IDENT_PREFIX'] + '_reg_token_' + _token)
    return current_app.config['LAN_DEV_REDIS_PROBER_IDENT_PREFIX'] + '_reg_token_' + _token

def new_register_token():
    '''
        Allocate new register token.

        :return:
            Token string with length of 32 in character A-Z and 0-9.
            Like: e711230222eb453f93c72d4db2ea0ea3
    '''
    return str(uuid.uuid4()).replace('-', '')


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
    if not check_register_token(_token):
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
    current_app.redis_store.set(token_to_redis_key(_token), 1, ex = _timeout)

def remove_token(_token):
    '''
        Remove register token.

        :token:
            _token          Token to remove.
    '''
    if not check_register_token(_token):
        return
    current_app.redis_store.delete(token_to_redis_key(_token))


def get_avaliable_token():
    '''
        Get avaliable tokens.

        :return: 
            A list of tokens.
    '''
    prefix = current_app.config['LAN_DEV_REDIS_PROBER_IDENT_PREFIX'] + '_reg_token_'
    raw = current_app.redis_store.keys(prefix + '*')
    return [raw_item.decode().replace(prefix, '') for raw_item in raw]

