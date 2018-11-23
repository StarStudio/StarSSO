import os
import pymysql
import gevent
import yaml
import uuid
import redis

from datetime import datetime, timedelta
from StarMember.utils.network import NetworkList
from .config import CheckBotConfig
from .utils import MACToInt, IntToMAC

def create_bundle_pymysql_connect(_config):
    def connect():
        return pymysql.connect(host = _config.mysql_host
                    , user = _config.mysql_user
                    , password = _config.mysql_password
                    , db = _config.mysql_db
                    , charset = _config.mysql_charset)
    return connect


class CheckBot:

    def __init__(self):
        self.leaving_device = {}
        self.last_mac_list = set()
        self.present_users = {}

    def user_leave(self, users, conn):
        conn = self.mysql_connect()
        try:
            conn.begin()
            c = conn.cursor()
            c.executemany('insert into record(uid, chktime, result) values (%s, %s, %s)', [(user, datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), 'check out') for user in users])
        except Exception as e:
            conn.rollback()
        finally:
            conn.commit()
        for user in users:
            print('User leave: %s' % user)

        conn.close()

    def device_join(self, macs):
        if not macs:
            return

        conn = self.mysql_connect()
        try:
            conn.begin()
            c = conn.cursor()
            c.executemany('insert into device_event(mac, time, event) values (%s, %s, %s)', [(MACToInt(mac), datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S') ,'join') for mac in macs])
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.commit()

        try:
            users = set()
            conn.begin()
            c = conn.cursor()
            for mac in macs:
                c.execute('select uid from device_bind where mac = %s', (MACToInt(mac),) )
                user = c.fetchall()
                if user:
                    user = user[0][0]
                    if user not in self.present_users:
                        users.add(user)
                        mac_set = set()
                        self.present_users[user] = mac_set
                        print('User join: %s' % user)
                    else:
                        mac_set = self.present_users[user]
                    mac_set.add(mac)

                    
            c.executemany('insert into record(uid, chktime, result) values (%s, %s ,%s)', [(user, datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), 'check in') for user in users])
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.commit()

        for mac in macs:
            print('Device join: %s' % mac)
        


    def device_leave(self, macs, conn):
        if not macs:
            return
        c = conn.cursor()
        c.executemany('insert into device_event(mac, time, event) values (%s, %s, %s)', [(MACToInt(mac), datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S') ,'left') for mac in macs])
        for mac in macs:
            print('Device leave: %s' % mac)

    def device_leave_routine(self):
        while True:
            now = datetime.now()
            left_user = set()
            left_mac = set()
            for mac, time in self.leaving_device.items():
                if time + timedelta(seconds = 30) < now:
                    for user, device_set in self.present_users.items():
                        device_set.discard(mac)
                        
                        if len(device_set) == 0:
                            left_user.add(user)
                    left_mac.add(mac)

            conn = None
            if left_user or left_mac:
                conn = self.mysql_connect()

            if left_mac:
                try:
                    conn.begin()
                    self.device_leave(left_mac, conn)
                except Exception as e:
                    conn.rollback()
                    raise e
                finally:
                    conn.commit()
                for mac in left_mac:
                    del self.leaving_device[mac]

            if left_user:
                try:
                    conn.begin() 
                    self.user_leave(left_user, conn)
                except Exception as e:
                    conn.rollback()
                    raise e
                finally:
                    conn.commit()
                for user in left_user:
                    del self.present_users[user]
            
            if conn is not None:
                conn.close()
            gevent.sleep(1)


    def Run(self):
        cb_config = CheckBotConfig()
    
        print('Checking dog start.')
        bot_id = str(uuid.uuid4()).replace('-', '')
        print('Bot ID: %s' % bot_id)
    
        if 'API_CFG' not in os.environ:
            print("Environment variable API_CFG not exists.")
            return None
        else:
            #cb_config.FromEnv('API_CFG')
            cb_config.FromDict(yaml.load(open(os.environ['API_CFG']).read()))

        self._config = cb_config
    
        self.mysql_connect = create_bundle_pymysql_connect(cb_config)
        conn = self.mysql_connect()
    
        #dev_list = DeviceList(config)
        dev_list = NetworkList(_redis_host = cb_config.redis_host, _redis_port = cb_config.redis_port, _redis_prefix = cb_config.redis_prefix)

        redis_storage = redis.Redis(host = cb_config.redis_host, port = cb_config.redis_port)
        # Redis Checkbot client mutex
        # KEYS:
        #   1: _prefix
        #   2: ID`
        mutex_proc = '''
            local key=KEYS[1] .. "_checkbot_current"
            if 1 == redis.call("exists", key) then
                return false
            end
            redis.call("set", key, KEYS[2])
            redis.call("expire", key, 10)
            return true
        '''
        while not redis_storage.eval(mutex_proc, 2, cb_config.redis_prefix, bot_id):
            print('Other bot is running.')
            gevent.sleep(10)

        print('Bot Mutex acquired. Start watching.') 
        gevent.spawn(self.device_leave_routine)

        while True:
            fresh_mac_list = set(dev_list.Snapshot().keys())
            leaving = self.last_mac_list.difference(fresh_mac_list)
            joining = fresh_mac_list.difference(self.last_mac_list)

            for mac in leaving:
                if mac not in self.leaving_device:
                    self.leaving_device[mac] = datetime.now()

            join_macs = set()
            for mac in joining:
                if mac in self.leaving_device:
                    del self.leaving_device[mac]
                else:
                    join_macs.add(mac)

            if join_macs:
                self.device_join(join_macs)

            self.last_mac_list = fresh_mac_list
            gevent.sleep(1)
            redis_storage.set(cb_config.redis_prefix + '_checkbot_current', bot_id, ex = 10)
    

if __name__ == '__main__':
    CheckBot().Run()
