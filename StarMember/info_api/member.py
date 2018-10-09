from flask import request, current_app, jsonify
from StarMember.aspect import post_data_type_checker, post_data_key_checker
from StarMember.views import SignAPIView, resource_access_denied, with_application_token
from StarMember.utils import password_hash
import uuid


def remove_user(**kwargs):
    conn = current_app.mysql.connect()
    conn.begin()
    c = conn.cursor()
    try:
        if request.auth_user_id != kwargs['uid']:
            affected = c.execute('select gid from group_members where uid=%s', (request.auth_user_id,))
            if affected < 1:
                return jsonify({'code': 1422, 'msg': 'Pending user.', 'data': ''})
            my_gid = int(c.fetchall()[0][0])

            affected = c.execute('select gid from group_members where uid=%s', (kwargs['uid'],))
            if affected < 1:
                return jsonify({'code': 1422, 'msg': 'User not exists', 'data': ''})
            gid = int(c.fetchall()[0][0])

            access_grant = False
            if gid != my_gid: # Not in same group
                if 'write_other' in request.app_verbs:
                    access_grant = True
            elif 'write_internal' in request.app_verbs:
                access_grant = True

            if not access_grant:
                return resource_access_deined()

        #if 'uid' in kwargs:
            affected = c.execute('delete from auth where uid=%s', (kwargs['uid']))
            affected = c.execute('delete from group_members where uid=(%s)', (kwargs['uid'],))
            affected = c.execute('delete from user where id=(%s)', (kwargs['uid'],))
        #else:
        #    affected = c.execute('delete from user where name=(%s)', (kwargs['name'],))
            
        if affected < 1:
            return jsonify({
                'code'  :   1422
                , 'msg' :   'User not exists'
                , 'data':   ''
            })
        conn.commit()
    except Exception as e:
        # log exception here with uid
        conn.rollback()
        raise e
    finally:
        conn.close()

    return jsonify({
        'code': 0
        , 'msg': 'success'
        , 'data' : ''
    })
    
    
class MemberAccessView(SignAPIView):
    method = ['GET', 'DELETE', 'PUT']

    @with_application_token(deny_unauthorization = True)
    def get(self, uid):
        if request.auth_user_id != uid:
            if 'read_internal' not in request.app_verbs\
            and 'read_other' not in request.app_verbs:
                return resource_access_deined()
        elif 'read_self' not in request.app_verbs:
            return resource_access_deined()

        conn = current_app.mysql.connect()
        conn.begin()
        c = conn.cursor()

        my_gid = None
        try:
            affected = c.execute('select user.name, user.birthday, user.sex, user.address, user.tel, user.mail, user.access_verbs, user.id, group_members.gid from user left join group_members on user.id=group_members.uid where user.id=%s', (uid,))
            if affected < 1:
                return jsonify({'code':1422, 'msg':"User not exists.", 'data': ''})
            result = c.fetchall()[0]

            if request.auth_user_id != uid:
                affected = c.execute('select gid where uid=%s', (request.auth_user_id,))

                if affected < 1:
                    return jsonify({'code': 1422, 'msg': 'Pending user.', 'data': ''})

                access_grant = False
                if int(result[8]) != int(c.fetchall()[0][0]): # Not in same group
                    if 'read_other' in request.app_verbs:
                        access_grant = True
                elif 'read_internal' in request.app_verbs:
                    access_grant = True

                if not access_grant:
                    return resource_access_deined()

        except Exception as e:
            # log exception here with uid
            conn.rollback()
            raise e
        finally:
            conn.commit()
            conn.close()

        return jsonify({
            'code': 0
            , 'msg': 'success'
            , 'data' : {
                'name': result[0]
                , 'birthday' : result[1]
                , 'sex': result[2]
                , 'address': result[3]
                , 'tel': result[4]
                , 'mail': result[5]
                , 'access_verbs': result[6].split(' ')
                , 'id': int(result[7])
                , 'gid': int(result[8]) if result[8] is not None else None
            }
        })


    @with_application_token(deny_unauthorization = True)
    def put(self, uid):
        if request.auth_user_id != uid:
            if 'write_other' not in request.app_verbs\
            and 'write_internal' not in request.app_verbs:
                return resource_access_deined()
        elif 'write_self' in request.app_verbs:
            return resource_access_deined()
        
        
        post_data = request.form.copy()
        if len(post_data) < 1:
            return jsonify({'code': 0, 'msg': 'success', 'data': ''})

        type_checker = post_data_type_checker(name = str, birthday = str, sex = str, tel = str, mail = str)
        ok, err_msg = type_checker(post_data)
        if not ok:
            return jsonify({
                        'code': 1422
                        , 'msg': err_msg
                        , 'data': ''
            })
        conn = current_app.mysql.connect()
        conn.begin()
        c = conn.cursor()
        
        try:
            affected = c.execute('select user.name, user.birthday, user.sex, user.address, user.tel, user.mail, user.access_verbs, group_members.gid from user inner join group_members on user.id=group_members.uid where user.id=%s', (uid,))
            if affected < 1:
                return jsonify({'code': 1422, 'msg': 'User not exists.', 'data': ''})
            info = list(c.fetchall()[0])

            if request.auth_user_id != uid:
                affected = c.execute('select gid from group_members where uid=%s', (request.auth_user_id,))

                if affected < 1:
                    return jsonify({'code': 1422, 'msg': 'Pending user.', 'data': ''})

                access_grant = False
                if int(info[7]) != int(c.fetchall()[0][0]): # Not in same group
                    if 'write_other' in request.app_verbs:
                        access_grant = True
                elif 'write_internal' in request.app_verbs:
                    access_grant = True

                if not access_grant:
                    return resource_access_deined()

            update_keywords = ('name', 'birthday', 'sex', 'address', 'tel', 'mail', 'access_verbs')
            for i in range(0, len(update_keywords)):
                if update_keywords[i] in post_data:
                    info[i] = post_data[update_keywords[i]]
            
            c.execute('update user set name = %s, birthday = %s, sex = %s, address = %s, tel = %s, mail = %s, access_verbs = %s', tuple(info[:len(update_keywords)]))

        except Exception as e:
            # log exception here with uid
            conn.rollback()
            raise e
        finally:
            conn.commit()
            conn.close()

        return jsonify({'code': 0, 'msg': 'success', 'data': ''})
            

    @with_application_token(deny_unauthorization = True)
    def delete(self, uid):
        return remove_user(**{'uid': uid})
    

class MemberAPIView(SignAPIView):
    methods = ['POST', 'DELETE', 'GET']

    @with_application_token(deny_unauthorization = True)
    def get(self):
        post_data = request.form.copy() 
        type_checker = post_data_type_checker(uid = int, gid = int)
        ok, err_msg = type_checker(post_data)
        if not ok:
            return jsonify({
                        'code': 1422
                        , 'msg': err_msg
                        , 'data': ''
            })
        request.post_data = post_data

        conn = current_app.mysql.connect()
        conn.begin()
       
        c = conn.cursor()
        try:
            affected = c.execute('select gid from group_members where uid=%s', (request.auth_user_id,))
            if affected < 1:
                return jsonify({'code': 1422, 'msg': 'Pending user.', 'data': ''})
            my_gid = int(c.fetchall()[0][0])

            if 'gid' in request.post_data:
                if 'uid' in request.post_data:
                    c.execute('select user.name, user.birthday, user.sex, user.address, user.tel, user.mail, user.access_verbs, group_members.uid, group_members.gid from group_members inner join user on user.id=group_members.uid where (group_members.gid=%s and group_members.uid=%s)', (request.post_data['gid'], request.post_data['uid']))
                else:
                    c.execute('select user.name, user.birthday, user.sex, user.address, user.tel, user.mail, user.access_verbs, group_members.uid, group_members.gid from group_members inner join user on user.id=group_members.uid where group_members.gid=%s', (request.post_data['gid'],))
                    
            else:
                if 'uid' in request.post_data:
                    c.execute('select user.name, user.birthday, user.sex, user.address, user.tel, user.mail, user.access_verbs, user.id, group_members.gid from user left join group_members on group_members.uid=user.id where user.id=%s', (request.post_data['uid'],))
                else:
                    c.execute('select user.name, user.birthday, user.sex, user.address, user.tel, user.mail, user.access_verbs, user.id, group_members.gid from user left join group_members on group_members.uid=user.id')

            results = c.fetchall()
            conn.commit()
        except Exception as e:
            # log exception here with uid
            conn.rollback()
            raise e
        finally:
            conn.close()


        filtered = []
        for item in results:
            if int(item[7]) == request.auth_user_id:
                if 'read_self' not in request.app_verbs:
                    continue
            elif int(item[8]) == my_gid:
                if 'read_internal' not in request.app_verbs:
                    continue
            elif 'read_other' not in request.app_verbs:
                continue
            filtered.append(item)
            
        return jsonify({
            'code': 0
            , 'msg': 'success'
            , 'data' : [{
                'name': item[0]
                , 'birthday' : item[1]
                , 'sex': item[2]
                , 'address': item[3]
                , 'tel': item[4]
                , 'mail': item[5]
                , 'access_verbs': item[6]
                , 'uid': int(item[7])
                , 'gid': int(item[8]) if item[8] is not None else None
            } for item in filtered]    
        })


    @with_application_token(deny_unauthorization = False)
    def post(self):
        post_data = request.form.copy()

        type_checker = post_data_type_checker(username = str, password = str, name = str, gid = int, sex = str, tel = str, mail = str)
        key_checker = post_data_key_checker('username', 'password', 'name', 'gid', 'sex', 'tel', 'mail')

        ok, err_msg = key_checker(post_data)
        if not ok:
            return jsonify({
                        'code': 1422
                        , 'msg': err_msg
                        , 'data': ''
            })
        ok, err_msg = type_checker(post_data)
        if not ok:
            return jsonify({
                    'code': 1422
                    , 'msg': err_msg
                    , 'data': ''
            })

        if len(post_data['password']) < 6:
            return jsonify({'code': 1422, 'msg': 'Password too short', 'data':''})
        if len(post_data['username']) < 6:
            return jsonify({'code': 1422, 'msg': 'Username too short', 'data': ''})
        

        request.post_data = post_data

        allow_anonymous = current_app.config.get('ALLOW_REGISTER', False)
        conn = current_app.mysql.connect()
        conn.begin()
        c = conn.cursor()
        try:
            if not allow_anonymous:
                if request.auth_err_response is not None:
                    return request.auth_err_response

                affected = c.execute('select gid from group_members where uid=%s', (request.auth_user_id,))
                if affected < 1:
                    return jsonify({'code': 1422, 'msg': 'Pending user.', 'data': ''})
                my_gid = int(c.fetchall()[0][0])

                if my_gid != request.post_data['gid']:
                    if 'write_internal' not in request.app_verbs:
                        return resource_access_deined()
                elif 'write_other' not in request.app_verbs:
                    return resource_access_deined()

            affected = c.execute('select count(*) from work_group where (id = %s)', (request.post_data['gid']))
            if affected < 1:
                return jsonify({
                    'code': 1423
                    , 'msg': 'group %d not exists' % request.post_data['gid']
                    , 'data' :''
                })
            if request.post_data['gid'] == 1:
                return jsonify({
                    'code': 1423
                    , 'msg': 'Cannot join this group.'
                    , 'data' :''
                })

            affected = c.execute('select count(username) from auth where username=%s', (post_data['username'],))
            if affected < 1:
                return jsonify({
                    'code': 1423
                    , 'msg': 'Username already exists.'
                    , 'data' : ''
                })
                
            c.execute('insert into user(name, sex, tel, mail, access_verbs) values(%s, %s, %s, %s, %s)', (request.post_data['name'], request.post_data['sex'], request.post_data['tel'], request.post_data['mail'], ' '.join(current_app.config['USER_INITIAL_ACCESS'])))
            uid = c.lastrowid
            c.execute('insert into group_members(gid, uid) values (%s, %s)', (request.post_data['gid'], uid))
            c.execute('insert into auth(uid, username, secret) values (%s, %s, %s)', (uid, post_data['username'], password_hash(post_data['password'])))

        except Exception as e:
            # log exception here with uid
            conn.rollback()
            raise e

        finally:
            conn.commit()
            conn.close()

        return jsonify({
            'code': 0
            , 'msg': 'success'
            , 'data' : {
                'uid': uid
            }
        })


    @with_application_token(deny_unauthorization = True)
    def delete(self):
        post_data = request.form.copy()
        #type_checker = post_data_type_checker(name = str, uid = str)
        #key_checker = post_data_key_checker(('name', 'uid'))
        type_checker = post_data_type_checker(uid = str)
        key_checker = post_data_key_checker('uid')

        ok, err_msg = key_checker(post_data)
        if not ok:
            return jsonify({
                    'code': 1422
                    , 'msg': err_msg
                    , 'data': ''
            })
        ok, err_msg = type_checker(post_data)
        if not ok:
            return jsonify({
                    'code': 1422
                    , 'msg': err_msg
                    , 'data': ''
            })

        return remove_user(**post_data)
