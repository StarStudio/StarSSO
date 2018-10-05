import hashlib
from base64 import b64encode
from flask import current_app

def password_hash(_password):
    '''
        Hash password according to preloaded salt.

        :params:
            _password           password string to hash

        :return:
            base64-encoded string
    '''
    salted = hashlib.md5()
    salted.update((_password + current_app.password_salt).encode('utf-8'))
    return b64encode(salted.digest)
