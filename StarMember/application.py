# -*- coding: utf-8 -*-
# author: joker sunmxt
# create at 2018-04-28 23:37:52

import os
import os.path
import logging
import uuid
import json

import uuid
import json
from jwcrypto.jwk import JWK
from jwcrypto.common import json_decode
from flask import Flask, current_app
from flaskext.mysql import MySQL
from functools import wraps
from base64 import b64encode, b64decode

from .info_api import info_api
from .sso import sso_api
from .utils import password_hash
from datetime import datetime


ADMIN_VERBS = frozenset([
    'auth', 'read_self', 'read_internal', 'read_other'
    , 'write_self', 'write_internal', 'write_other', 'read_group'
    , 'write_group', 'alter_group'
])

USER_INITIAL_ACCESS_DEFAULT = frozenset([
    'auth', 'read_self', 'read_internal', 'read_other', 'write_self'
])

APP_INITIAL_ACCESS_DEFAULT = frozenset([
    'auth', 'read_self'
])
 
  

app = Flask(__name__)

# Modules
mysql = MySQL()
mysql.init_app(app)
app.mysql = mysql

# Load configure
if 'API_CFG' in os.environ \
    and os.path.isfile(os.environ['API_CFG']):
        app.config.from_envvar('API_CFG')
else:
    print('Configure not found in environment varible API_CFG.')
    print('Use config.py')
    app.config.from_pyfile('config.py')

# Blueprints
app.register_blueprint(info_api)
app.register_blueprint(sso_api)

def make_log_time_wrapper(_function): 
    @wraps(_function)
    def time_log_wrapper(level, msg, *arg, **kwarg):
        msg = '[%s] ' % datetime.now().isoformat() + msg
        return _function(level, msg, *arg, **kwarg)
    return time_log_wrapper

def make_log_level_wrapper(_level):
    def level_wrapper_wrap(_function):
        @wraps(_function)
        def level_log_wrapper(msg, level = _level, *arg, **kwarg):
            return _function(level, msg, *arg, **kwarg)
        return level_log_wrapper
    return level_wrapper_wrap


def load_jwt_key():
    key_path = current_app.config.get('SECRET_KEY_FILE', 'jwt.pri')
    if key_path is None:
        raise RuntimeError('SECRET_KEY_FILE not configured.')
    try:
        key_io = open(key_path, 'rb')
    except FileNotFoundError as e:
        key_io = None

    if key_io is None:
        key_io = open(key_path, 'wb+') 
        key = JWK(generate='RSA', size=1024)
        pem = key.export_to_pem(private_key=True, password = None)
        key_io.write(pem)
    else:
        pem = key_io.read()
        key = JWK()
        key.import_from_pem(pem)
    key_io.close()
    os.chmod(key_path, current_app.config.get('SECRET_KEY_FILE_MODE', 0o600))
    pub_key_path = current_app.config.get('PUBLIC_KEY_FILE', None)
    if pub_key_path is not None:
        if not os.path.isfile(pub_key_path):
            try:
                pub_io = open(pub_key_path, 'wb+')
                pem = key.export_to_pem()
                pub_io.write(pem)
                pub_io.close()
            except PermissionError as e:
                pass
        os.chmod(pub_key_path, current_app.config.get('PUBLIC_KEY_FILE_MODE', 0o666))

    return key

def load_digest_salt():
    current_app.reset_admin_account = False

    salt_path = current_app.config.get('SALT_FILE', None)
    if salt_path is None:
        raise RuntimeError('SALT_FILE not configured.')
    try:
        salt_io = open(salt_path, 'rt')
    except FileNotFoundError as e:
        salt_io = None

    if salt_io is None:
        salt_io = open(salt_path, 'wt')
        salt = os.urandom(15)
        salt_text = b64encode(salt).decode('ascii')
        salt_io.write(salt_text)
        current_app.reset_admin_account = True
    else:
        salt_io = open(salt_path, 'rt')
        salt_text = salt_io.read()
    salt_io.close()
    os.chmod(salt_path, current_app.config.get('SALT_FILE_MODE', 0o600))

    return salt_text
        

def generate_logger():
    app.access_logger = logging.getLogger('access_log')
    app.access_logger.setLevel(logging.INFO)
    if 'ACCESS_LOG' in app.config:
        access_log_file_handler = logging.FileHandler(app.config['ACCESS_LOG'])
        app.access_logger.addHandler(access_log_file_handler)
        app.log_access = make_log_time_wrapper(app.access_logger.log)
        app.log_access = make_log_level_wrapper(logging.INFO)(app.log_access)

    app.error_logger = logging.getLogger('error_log')
    app.access_logger.setLevel(logging.ERROR)
    if 'ERROR_LOG' in app.config:
        error_log_file_handler = logging.FileHandler(app.config['ERROR_LOG'])
        app.error_logger.addHandler(error_log_file_handler)
        app.log_error = make_log_time_wrapper(app.error_logger.log)
        app.log_error = make_log_level_wrapper(logging.ERROR)(app.log_error)

    on_debug = app.config.get('DEBUG', False)
    app.access_logger.setLevel(logging.DEBUG)
    if on_debug:
        app.debug_logger = logging.getLogger('debug')
        if 'DEBUG_LOG' in app.config:
            debug_log_file_handler = logging.FileHandler(app.config['DEBUG_LOG'])
            app.debug_logger.addHandler(debug_log_file_handler)
            app.log_debug = make_log_time_wrapper(app.debug_logger.log)
            app.log_debug = make_log_level_wrapper(logging.DEBUG)(app.log_debug)



def init_admin_account():
    if current_app.reset_admin_account is False:
        return

    print('Administrator account will be reset due to the change of password salt.')
    current_app.access_logger.info('Administrator account will be reset due to the change of password salt.')
    default_secret = password_hash('starstudio')

    conn = current_app.mysql.connect()
    conn.begin()
    c = conn.cursor()
    try:
        c.execute('delete from auth where username=\'Admin\'')
        c.execute('delete from user where id=0')
        affected = c.execute('insert into user(id, name, sex, address, tel, mail, access_verbs) values (0, \'Administrator\', \'Unknown\', \'\', \'\', \'\', %s)', (' '.join(ADMIN_VERBS)))
        uid = c.lastrowid
        c.execute('insert into auth(uid, username, secret) values (%s, \'Admin\', %s)', (uid, default_secret))
    except Exception as e:
        conn.rollback()
        raise e

    finally:
        conn.commit()


def reset_admin_application():
    print('Reset administration application.')
    web_redirect_prefix = current_app.config.get('SSO_WEB_REDIRECT_PREFIX', None)
    if web_redirect_prefix is None:
        raise RuntimeError('SSO_WEB_REDIRECT_PREFIX not configured.')

    current_app.log_access('Reset administration application')
    conn = current_app.mysql.connect()
    conn.begin()
    c = conn.cursor()
    try:
        c.execute('delete from application where id=0')
        c.execute('insert into application(id, name, desp, redirect_prefix) values(0, \'SSO Manage\', \'Web Console to manage users and applications\', %s) ', (web_redirect_prefix,))
        c.execute('delete from app_bind where appid=0 and uid=0')
        c.execute('insert into app_bind(uid, appid, access_verbs) values (0, 0, %s)', (' '.join(ADMIN_VERBS),))
    except Exception as e:
        conn.rollback()
        raise e

    finally:
        conn.commit()


@app.before_first_request
def app_init():
    current_app.jwt_key = load_jwt_key()
    current_app.digest_salt = load_digest_salt()
    generate_logger()
    init_admin_account()
    reset_admin_application()

    if 'USER_INITIAL_ACCESS' in current_app.config:
        current_app.log_error('USER_INITIAL_ACCESS not configured. Set to (%s)' % ','.join(USER_INITIAL_ACCESS_DEFAULT))
        current_app.config['USER_INITIAL_ACCESS'] = USER_INITIAL_ACCESS_DEFAULT

    if 'APP_INITIAL_ACCESS' in current_app.config:
        current_app.log_error('APP_INITIAL_ACCESS not configured. Set to (%s)' % ','.join(APP_INITIAL_ACCESS))
        current_app.config['APP_INITIAL_ACCESS'] = APP_INITIAL_ACCESS
