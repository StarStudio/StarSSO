import os
import pymysql
import gevent
from datetime import datetime, timedelta
from LANDevice import LANDeviceProberConfig, DeviceList
from .config import CheckBotConfig
from .utils import MACToInt, IntToMAC

import ipdb

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
        config = LANDeviceProberConfig()
        cb_config = CheckBotConfig()
    
        print('Checking dog start.')
    
        if 'CHECK_BOT_CONFIG' not in os.environ:
            print("Environment variable CHECK_BOT_CONFIG not exists.")
            return None
        else:
            config.FromEnv('CHECK_BOT_CONFIG')
            cb_config.FromEnv('CHECK_BOT_CONFIG')

        self._config = cb_config
    
        self.mysql_connect = create_bundle_pymysql_connect(cb_config)
        conn = self.mysql_connect()
    
        dev_list = DeviceList(config)
        listener = dev_list.NewListener()

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
    

if __name__ == '__main__':
    CheckBot().Run()
