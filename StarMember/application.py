# -*- coding: utf-8 -*-
# author: joker sunmxt
# create at 2018-04-28 23:37:52

import os
import logging
import uuid
import json

import uuid
import json
from .info_api import info_api
from flask import Flask, current_app
from flaskext.mysql import MySQL
from functools import wraps

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
    

@app.before_first_request
def app_init():
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

