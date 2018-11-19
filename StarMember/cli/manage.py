#! /bin/python

import click
import sys
import os
import yaml
from tempfile import NamedTemporaryFile

sys.path.append(os.getcwd())

from StarMember.config import Config, ConfigureError
from StarMember.wsgi import WSGIAppFactory
from StarMember.utils.security import password_hash
from flask import current_app


def load_configure(config_path):
    return Config(open(config_path, 'rt').read())

def load_wsgi_app(_config, _mode = os.environ.get('STARSSO_SERVER_MODE', 'APIServer')):
    config_map = load_configure(_config)
    tmp_wrapper = NamedTemporaryFile('wt')
    io = tmp_wrapper.file
    if _mode == 'APIServer':
        io.write(yaml.dump(config_map.MasterWSGIConfig))
    elif _mode == 'Agent':
        io.write(yaml.dump(config_map.AgentWSGIConfig))
    io.flush()
    os.environ['API_CFG'] = tmp_wrapper.name
    app = WSGIAppFactory(_mode).Build()
    if app is None:
        return None
    app._temp_config_wrapper = tmp_wrapper
    return app
 

@click.group()
def Manage():
    pass


# Account Management
@Manage.group()
def account():
    pass


@account.command('reset-admin', help = 'Reset administrator account.')
@click.option('-c', '--config', help = 'Use specfied configure file.', default = '/etc/starsso/apiserver.yml', type = str, show_default = True)
@click.option('--persist-conf/--no-persist-conf', help = 'If save changes to original configure file.', default = False)
def reset_admin_account(config, persist_conf):
    try:
        app = load_wsgi_app(config)
    except ConfigureError as e:
        click.echo(e)
        return 1

    with app.app_context():
        INITIAL_PASS = 'starstudio'
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
    click.echo('Administrator account reset to initial state. Initial password: %s' % INITIAL_PASS)
 
   
# Application Management
@Manage.group()
def application():
    pass

@application.command('reset-admin', help = 'Reset administrator account.')
@click.option('-c', '--config', help = 'Use specfied configure file.', default = '/etc/starsso/apiserver.yml', type = str, show_default = True)
@click.option('--persist-conf/--no-persist-conf', help = 'If save changes to original configure file.', default = False)
def reset_admin_application(config, persist_conf):
    try:
        app = load_wsgi_app(config)
    except ConfigureError as e:
        click.echo(e)
        return 1

    
    with app.app_context():
        web_redirect_prefix = current_app.config.get('SSO_WEB_REDIRECT_PREFIX', None)
        if web_redirect_prefix is None:
            raise RuntimeError('SSO_WEB_REDIRECT_PREFIX not configured.')

        current_app.log_access('Administration application reset.')
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
    click.echo('Administration application reset.')


# Network Management
@Manage.group()
def network():
    pass

@network.group('token')
def network_token():
    pass

@network_token.command('list')
def list_network_token():
    print('token list')

Manage()
