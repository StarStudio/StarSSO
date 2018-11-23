from flask import request, current_app, jsonify, abort
from StarMember.views import SignAPIView, with_application_token, resource_access_denied, api_succeed, api_user_pending, api_wrong_params
from StarMember.aspect import post_data_type_checker, post_data_key_checker
from StarMember.utils.network import MACToInt, IntToMAC
from StarMember.utils.param import get_request_params
from StarMember.utils.context import APIRequestContext
from pymysql.err import IntegrityError

class BindView(SignAPIView):
    method = ['GET', 'POST']

    @with_application_token(deny_unauthorization = True)
    def get(self):
        # Resume context for original bind request
        ctx = APIRequestContext()
        if ctx.ResumeFromRequest() and ctx['origin_bind_request'] is True:
            return self.bind_device(ctx)


        post_data = get_request_params()
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
                    
        except Exception as e:
            conn.rollback()
            raise e

        finally:
            conn.commit()
            conn.close()

        return api_succeed([{'uid': uid, 'mac' : list(mac_set)} for uid, mac_set in result.items()])

    def bind_device(self, ctx):
        devices = current_app.device_list.Snapshot2()
        if not ctx.Net \
           or ctx.Net.ID not in devices \
           or not ctx.MAC \
           or ctx.MAC in devices[ctx.Net.ID]:
            return api_wrong_params('Device not found.')
        
        if not ctx.LocalIP \
            or ctx.LocalIP not in devices[ctx.Net.ID][ctx.MAC]:
            return api_wrong_params('Bind another device is not allowed.')

        conn = current_app.mysql.connect()
        conn.begin()
        c = conn.cursor()
        try:
            c.execute('insert into device_bind(mac, uid) values (%s, %s)', (mac_int, request.auth_user_id))
        except IntegrityError as e:
            conn.rollback()
            return api_wrong_params('Device bound.')
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.commit()

        return api_succeed()
        

    @with_application_token(deny_unauthorization = True)
    def post(self):
        ctx = APIRequestContext()
        if not ctx.ResumeFromRequest():
            post_data = get_request_params()
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

            if not ctx.MAC:
                ctx['mac_int'] = mac_int
                ctx['origin_bind_request'] = True
                ctx.Suspend()
                return ctx.RedirectForDeviceInfo()

        return self.bind_device(ctx)


class BindManageView(SignAPIView):
    method = ['DELETE']

    @with_application_token(deny_unauthorization = True)
    def delete(self, mac):
        if len(mac) != 12:
            abort(404)
        try:
            mac_int = int(mac, 16)
        except ValueError as e:
            abort(404)

        conn = current_app.mysql.connect()
        conn.begin()
        c = conn.cursor()
        try:
            affected = c.execute('delete from device_bind where uid = %s and mac = %s', (request.auth_user_id, mac_int))
            if affected < 1:
                return api_wrong_params('Not bound or cannot unbind.')
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.commit()
            conn.close()

        return api_succeed()
