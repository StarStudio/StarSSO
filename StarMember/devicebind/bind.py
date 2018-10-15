from flask import request, current_app, jsonify
from StarMember.views import SignAPIView, with_application_token, resource_access_denied, api_succeed, api_user_pending, api_wrong_params
from StarMember.aspect import post_data_type_checker, post_data_key_checker
from StarMember.utils import MACToInt, IntToMAC
from pymysql.err import IntegrityError

class BindView(SignAPIView):
    method = ['GET', 'POST']

    @with_application_token(deny_unauthorization = True)
    def get(self):

        post_data = request.form.copy()
        type_checker = post_data_type_checker(uid = int, gid = int)
        ok, err_msg = type_checker(post_data)
        if not ok:
            return api_wrong_params(err_msg)

        if 'uid' in post_data:
            if request.auth_user_id != post_data['uid']:
                if 'read_internal' not in request.app_verbs \
                and 'read_other' not in request.app_verbs:
                    return api_succeed([])
            elif 'read_self' not in request.app_verbs:
                return api_succeed([])

        
        conn = current_app.mysql.connect()
        conn.begin()
        c = conn.cursor()
        try:
            result = {}
            affected = c.execute('select mac, uid from device_bind')
            binds = c.fetchall()
            if affected:
                affected = c.execute('select gid from group_members where uid = %s', (request.auth_user_id,))
                if affected < 1:
                    return api_user_pending()
                my_gid = int(c.fetchall()[0][0])

                affected = c.execute('select uid from group_members where gid != %s', (my_gid,))
                others_uid = set([x[0] for x in c.fetchall()])
                affected = c.execute('select uid from group_members where gid = %s', (my_gid,))
                internal_uid = set([x[0] for x in c.fetchall()])

                for mac, uid in binds:
                    if uid not in result:
                        mac_set = set()
                        result[uid] = mac_set
                    else:
                        mac_set = result[uid]
                    mac_set.add(IntToMAC(mac))
                
                if 'read_other' not in request.app_verbs:
                    for uid in others_uid:
                        del result[uid]

                if 'read_internal' not in request.app_verbs:
                    if 'read_self' not in request.app_verbs:
                        for uid in internal_uid:
                            del result[uid]
                    else:
                        result = {request.auth_user_id: result[request.auth_user_id]} if request.auth_user_id in result else {}
            #if 'uid' in post_data:
            #    if request.auth_user_id != post_data['uid']:
            #        affected = c.execute('select gid from group_members where uid = %s', (request.auth_user_id,))
            #        if affected < 1:
            #            return api_user_pending()
            #        my_gid = int(c.fetchall()[0][0])
            #        
            #        affected = c.execute('select gid from group_members where uid = %s', (post_data['uid']))
            #        if affected < 1:
            #            return api_user_pending()
            #        gid = int(c.fetchall()[0][0])
            #        if my_gid != gid:
            #            if 'read_other' not in request.app_verbs:
            #                return api_succeed([])
            #        elif 'read_internal' not in request.app_verbs:
            #            return api_succeed([])
            #        
            #    if 'gid' in post_data:
            #        affected = c.execute('select device_bind.mac, device_bind.uid from device_bind inner join group_members on device_bind.uid=group_members.uid where device_bind.uid = %s and group_members.gid = %s', (post_data['uid'], post_data['gid']))
            #    else:
            #        affected = c.execute('select mac, uid from device_bind where uid = %s', (post_data['uid'], ))
            #        
            #    mac_rows = c.fetchall()
            #else:
            #    affected = c.execute('select gid from group_members where uid = %s', (request.auth_user_id,))
            #    if affected < 1:
            #        return api_user_pending()
            #    my_gid = int(c.fetchall()[0][0])
            #    
            #    if 'gid' in post_data:
            #        if post_data['gid'] != my_gid:
            #            if 'read_other' not in request.app_verbs:
            #                return api_succeed([])
            #        elif 'read_internal' not in request.app_verbs:
            #            return api_succeed([])
            #        
            #        affected = c.execute('select mac, uid from device_bind where uid in (select uid from group_members where gid = %s)', (post_data['gid'],))
            #        mac_rows = c.fetchall()
            #    else:
            #        affected = c.execute('select mac, uid from device_bind')
                    
        except Exception as e:
            conn.rollback()
            raise e

        finally:
            conn.commit()
            conn.close()

        return api_succeed([{'uid': uid, 'mac' : list(mac_set)} for uid, mac_set in result.items()])


    @with_application_token(deny_unauthorization = True)
    def post(self):
        post_data = request.form.copy()
        type_checker = post_data_type_checker(mac = str)
        key_checker = post_data_key_checker('mac')
        ok, msg = type_checker(post_data)
        if not ok:
            return api_wrong_params(msg)
        ok, msg = key_checker(post_data)
        if not ok:
            return api_wrong_params(msg)

        try:
            mac_int = MACToInt(post_data['mac'])
        except ValueError as e:
            return api_wrong_params(str(e))

        device_lists = {MACToInt(mac): { 'IPs' : list(ips) } for mac, ips in current_app.device_list.Snapshot().items()}
        print(current_app.device_list.Snapshot().items())
        if mac_int not in device_lists:
            return api_wrong_params('Device not found.')
        if request.remote_addr not in device_lists[mac_int]:
            return api_wrong_params('Bind another device is not allowed.')

        conn = current_app.mysql.connect()
        conn.begin()
        c = conn.cursor()
        try:
            c.execute('insert into device_bind(mac, uid) values (%s, %s)', (mac_int, request.auth_user_id))
        except IntegrityError as e:
            conn.rollback()
            return api_wrong_params('Device already binded.')
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.commit()

        return api_succeed()
