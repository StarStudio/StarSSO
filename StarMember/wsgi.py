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
import yaml
from jwcrypto.jwk import JWK
from jwcrypto.common import json_decode
from flask import Flask, current_app, make_response
from flaskext.mysql import MySQL
from flask_redis import FlaskRedis
from functools import wraps
from base64 import b64encode, b64decode

from .info_api import info_api
from .devicebind import bind_api
from .sso import sso_api
from .lan_agent import net_api
from .shims import shim_api
from .utils.security import password_hash
from .config import ConfigureError
from datetime import datetime


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


class WSGIAppFactory:
    AVALIABLE_SERVER_MODE = frozenset(['APIServer', 'Agent'])

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


    def __init__(self, _mode):
        if _mode not in WSGIAppFactory.AVALIABLE_SERVER_MODE:
            raise ValueError('Invalid Server Mode')
        self._mode = _mode
        self._app = None

    def _generate_logger(self):
        app = self._app
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


    def _load_jwt_key(self):
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


    def load_network_id(self):
        #nid_path = current_app.config.get('LAN_DEV_NETWORK_ID_FILE', None)
        #if nid_path is None:
        #    raise RuntimeError('LAN_DEV_NETWORK_ID_FILE not configured.')
        #while True:
        #    try:
        #        nid_io = open(nid_path, 'rt')
        #        break
        #    except FileNotFoundError as e:
        #        print('Network ID File not present: %s' % nid_path)
        #        print('Wait for 10 seconds.')
        #    time.sleep(10)
        #network_id = nid_io.read()
        #nid_io.close()
        #return network_id
        return current_app.config.get('LAN_DEV_NETWORK_ID', 'Unknown')

    def _init_admin_account(self):
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
            c.execute('delete from group_members where uid=1')
            c.execute('delete from check_status where uid=1')
            c.execute('delete from record where uid=1')
            c.execute('delete from device_bind where uid=1')
            c.execute('delete from user where id=1')
            affected = c.execute('insert into user(id, name, sex, address, tel, mail, access_verbs) values (1, \'Administrator\', \'Unknown\', \'\', \'\', \'\', %s)', (' '.join(WSGIAppFactory.ADMIN_VERBS)))
            uid = c.lastrowid
            c.execute('insert into auth(uid, username, secret) values (%s, \'Admin\', %s)', (uid, default_secret))
            affected = c.execute('select id from work_group where id=1')
            
            if affected < 1:
                c.execute('insert into work_group(id, name, desp) values(1, \'Admin\', \'Administrator Group\')')
            c.execute('insert into group_members (uid, gid) values (1, 1)')
        except Exception as e:
            conn.rollback()
            raise e
    
        finally:
            conn.commit()
    
    
    def _reset_admin_application(self):
        print('Reset administration application.')
        web_redirect_prefix = current_app.config.get('SSO_WEB_REDIRECT_PREFIX', None)
        if web_redirect_prefix is None:
            raise RuntimeError('SSO_WEB_REDIRECT_PREFIX not configured.')
    
        current_app.log_access('Reset administration application')
        conn = current_app.mysql.connect()
        conn.begin()
        c = conn.cursor()
        try:
            c.execute('delete from application where id=1')
            c.execute('insert into application(id, name, desp, redirect_prefix) values(1, \'SSO Manage\', \'Web Console to manage users and applications\', %s) ', (web_redirect_prefix,))
            c.execute('delete from app_bind where appid=1 and uid=1')
            c.execute('insert into app_bind(uid, appid, access_verbs) values (1, 1, %s)', (' '.join(WSGIAppFactory.ADMIN_VERBS),))
        except Exception as e:
            conn.rollback()
            raise e
    
        finally:
            conn.commit()



    def _load_common_components(self):
        app = self._app
        # Load configure
        if 'API_CFG' in os.environ \
            and os.path.isfile(os.environ['API_CFG']):
                conf_path = os.environ.get('API_CFG')
        else:
            print('Configure not found in environment varible API_CFG.')
            print('Use config.py')
            conf_path = 'config.py'
        conf_dict = yaml.load(open(conf_path, 'rt').read())
        if conf_dict is None:
            raise ConfigureError('Cannot load configure: %s' % conf_path)
            
        app.config.from_mapping(conf_dict)
        
        app.config['SERVER_MODE'] = self._mode
        app.reset_admin_account = False

        redis_url = app.config.get('REDIS_URL', None)
        if redis_url is None:
            redis_url = 'redis://'
            redis_host = app.config.get('REDIS_HOST', '127.0.0.1')
            redis_port = app.config.get('REDIS_PORT', 6379)
            if isinstance(redis_port, int):
                redis_port = int(redis_port)
                app.config['REDIS_PORT'] = redis_port
            redis_db = app.config.get('REDIS_DB')
            redis_url = 'redis://%s:%s/%s' % (redis_host, redis_port, redis_db)
            app.config['REDIS_URL'] = redis_url

        # Load common blueprints
        app.register_blueprint(shim_api)

        # Logger
        self._generate_logger()

        # Preprocess 
        def load_jwt_key():
            current_app.jwt_key = self._load_jwt_key()

        app.before_first_request(load_jwt_key)


    def _load_apiserver_components(self):
        app = self._app

        user_initial_access = app.config.get('USER_INITIAL_ACCESS', None)
        if user_initial_access is None:
            app.log_error('USER_INITIAL_ACCESS not configured. Set to (%s)' % ','.join(WSGIAppFactory.USER_INITIAL_ACCESS_DEFAULT))
            app.config['USER_INITIAL_ACCESS'] = WSGIAppFactory.USER_INITIAL_ACCESS_DEFAULT

        app_initial_access = app.config['APP_INITIAL_ACCESS']
        if app_initial_access is None:
            app.log_error('APP_INITIAL_ACCESS not configured. Set to (%s)' % ','.join(WSGIAppFactory.APP_INITIAL_ACCESS))
            app.config['APP_INITIAL_ACCESS'] = WSGIAppFactory.APP_INITIAL_ACCESS

        redis_storage = FlaskRedis()
        redis_storage.init_app(app)
        app.redis_store = redis_storage
        mysql = MySQL()
        mysql.init_app(app)
        app.mysql = mysql

        # Blueprint
        app.register_blueprint(info_api)
        app.register_blueprint(sso_api)
        app.register_blueprint(bind_api)
        app.register_blueprint(net_api)

        # Preprocess
        app.digest_salt = app.config['SALT']
        #def init_admin():
            #self._init_admin_account()
            #self._reset_admin_application()
        #app.before_first_request(init_admin)


    def _load_agent_components(self):
        app = self._app
        def load_network_id():
            current_app.network_id = self.load_network_id()
        app.before_first_request(load_network_id)


    def Build(self):
        if self._app:
            return self._app

        app = Flask(__name__)
        self._app = app
        self._load_common_components()

        if self._mode == 'APIServer':
            self._load_apiserver_components()
        elif self._mode == 'Agent':
            self._load_agent_components()

        return app