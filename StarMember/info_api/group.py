from flask import request, current_app, jsonify
from StarMember.aspect import post_data_type_checker, post_data_key_checker
from StarMember.views import SignAPIView, resource_access_denied, with_application_token
import uuid

class GroupAPIView(SignAPIView):
    methods = ['POST', 'DELETE', 'GET']

    @with_application_token(deny_unauthorization = True)
    def post(self):
        if 'alter_group' not in request.app_verbs:
            return resource_access_denied()
            
        post_data = request.form.copy()
        type_checker = post_data_type_checker(name = str, desp = str)
        key_checker = post_data_key_checker('name', 'desp')

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
            c.execute('insert into work_group(name, desp) values (%s, %s)', (request.post_data['name'], request.post_data['desp']))
            gid = c.lastrowid
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
            return jsonify({
                    'code': 1505
                    , 'msg': 'Server raises a exception with id %s' % str(uuid.uuid4())
                    , 'data': ''
            })
        finally:
            conn.close()

        return jsonify({
            'code': 0
            , 'msg' : 'success'
            , 'data' : {'gid': gid}
        })


    @with_application_token(deny_unauthorization = True)
    def delete(self):
        if 'alter_group' not in request.app_verbs:
            return resource_access_denied()

        post_data = request.form.copy()
        key_checker = post_data_key_checker('gid')
        type_checker = post_data_type_checker(gid = str)

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
            affected = c.execute('select uid from group_members where (gid=%s)', (request.post_data['gid'][0],))
            if affected > 0:
                return jsonify({
                    'code': 1301
                    , 'msg': 'Group not empty.'
                    , 'data' : ''
                })
            affected = c.execute('delete from work_group where (id=%s)', (request.post_data['gid'][0],))
            if affected < 1:
                return jsonify({
                    'code': 1422
                    , 'msg': 'GID %s invalid. Group not exists.' % request.post_data['gid'][0]
                    , 'data' : ''
                })
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
            return jsonify({
                    'code': 1505
                    , 'msg': 'Server raises a exception with id %s' % str(uuid.uuid4())
                    , 'data': ''
            })

        finally:
            conn.close() 

        return jsonify({
            'code': 0
            , 'msg' : 'success'
            , 'data' : ''
        })

    
    @with_application_token(deny_unauthorization = False)
    def get(self):
        if current_app.config['ALLOW_ANONYMOUS_GROUP_INFO'] is not True:
            if request.auth_err_response is not None:
                return request.auth_err_response
            if 'read_group' not in request.app_verbs:
                return resource_access_denied()

        post_data = request.form.copy()
        key_checker = post_data_key_checker()
        ok, err_msg = key_checker(post_data)
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
            c.execute('select name, id, desp from work_group')
            results = c.fetchall()
        except Exception as e:
            conn.rollback()
            raise e
            return jsonify({
                'code': 1505
                , 'msg': 'Server raises a exception with id %s' % str(uuid.uuid4())
                , 'data': ''
            })

        finally:
            conn.close()

        return jsonify({
            'code': 0
            , 'msg': 'success'
            , 'data' : [
                {
                    'name' : name
                    , 'gid' : gid
                    , 'desp' : desp
                } for name, gid, desp in results
            ]
        })
