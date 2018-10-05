from flask import request, current_app, jsonify
from StarMember.aspect import post_data_type_checker, post_data_key_checker
from StarMember.views import SignAPIView
import uuid

def remove_user(**kwargs):
    conn = current_app.mysql.connect()
    conn.begin()
    c = conn.cursor()
    try:
        if 'uid' in kwargs:
            affected = c.execute('delete from user where id=(%s)', (kwargs['uid'],))
        else:
            affected = c.execute('delete from user where name=(%s)', (kwargs['name'],))
            
        if affected < 1:
            return jsonify({
                'code'  :   1422
                , 'msg' :   'user not exists'
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
    method = ['GET', 'DELETE', 'POST']

    def get(self, uid):
        conn = current_app.mysql.connect()
        conn.begin()
        c = conn.cursor()
        try:
            affected = c.execute('select user.name, user.birthday, user.sex, user.address, user.tel, user.mail, user.access_verbs, user.id, group_members.gid from user left join group_members on user.id=group_members.uid where user.id=%s', (uid,))
            if affected < 1:
                conn.commit()
                return {'code':1422, 'msg':"User not exists.", 'data': ''}

            result = c.fetchall()[0]
        except Exception as e:
            # log exception here with uid
            conn.rollback()
            raise e
        finally:
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
            

    def post(self, uid):
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
            affected = c.execute('select name, birthday, sex, address, tel, mail, access_verbs from user where id=%s', (uid,))
            if affected < 1:
                conn.commit()
                return jsonify({'code': 1422, 'msg': 'User not exists.', 'data': ''})
            info = list(c.fetchall()[0])

            update_keywords = ('name', 'birthday', 'sex', 'address', 'tel', 'mail', 'access_verbs')
            for i in range(0, len(update_keywords)):
                if update_keywords[i] in post_data:
                    info[i] = post_data[update_keywords[i]]
            
            c.execute('update user set name = %s, birthday = %s, sex = %s, address = %s, tel = %s, mail = %s, access_verbs = %s', tuple(info))
            conn.commit()
        except Exception as e:
            # log exception here with uid
            conn.rollback()
            raise e
        finally:
            conn.close()

        return jsonify({'code': 0, 'msg': 'success', 'data': ''})
            

    def delete(self, uid):
        return remove_user(**{'uid': uid})
    

class MemberAPIView(SignAPIView):
    methods = ['POST', 'DELETE', 'GET']

    def dispatch_request(self):
        return super().dispatch_request()

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
            } for item in results]    
        })
            
    def post(self):
        post_data = request.form.copy()

        type_checker = post_data_type_checker(name = str, gid = int, sex = str, tel = str, mail = str)
        key_checker = post_data_key_checker('name', 'gid', 'sex', 'tel', 'mail')

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
        request.post_data = post_data


        conn = current_app.mysql.connect()
        conn.begin()
        c = conn.cursor()
        try:
            c.execute('select name from work_group where (id = %s)', (request.post_data['gid']))
            
            result = c.fetchall()
            if result:
                c.execute('insert into user(name, sex, tel, mail) values(%s, %s, %s, %s)', (request.post_data['name'], request.post_data['sex'], request.post_data['tel'], request.post_data['mail']))
                uid = c.lastrowid
                c.execute('insert into group_members(gid, uid) values (%s, %s)', (request.post_data['gid'], uid))
                conn.commit()
            else:
                return jsonify({
                    'code': 1423
                    , 'msg': 'group %d not exists' % request.post_data['gid']
                    , 'data' :''
                })

        except Exception as e:
            # log exception here with uid
            conn.rollback()
            raise e

        finally:
            conn.close()

        return jsonify({
            'code': 0
            , 'msg': 'success'
            , 'data' : {
                'uid': uid
            }
        })


    def delete(self):
        post_data = request.form.copy()
        type_checker = post_data_type_checker(name = str, uid = str)
        key_checker = post_data_key_checker(('name', 'uid'))

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
