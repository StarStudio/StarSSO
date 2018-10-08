import os
import uuid
import werkzeug

from traceback import format_exc
from flask import Blueprint, current_app, make_response, request, abort, jsonify, redirect
from flask.views import MethodView
from StarMember.aspect import post_data_type_checker
from StarMember.utils import password_hash
from StarMember.utils import new_encoded_token, decode_token
from base64 import b64decode
from datetime import datetime, timedelta


class LoginView(MethodView):
    method = ['GET']

    def http_basic_auth(self):
        auth_header = request.headers.get('Authorization', None)
        if None is auth_header:
            return make_response(jsonify({'code': 1201, 'msg': 'No Authorization', 'data':''}), 403)
        splited = auth_header.split(' ')
        
        if len(splited) != 2:
            abort(400)
        method, auth_content = splited
        if method != 'Basic':
            return make_response(jsonify({'code': 1202, 'msg': 'Unsupported authorization method.', 'data': ''}), 403)

        try:
            splited = b64decode(auth_content.encode('ascii')).decode('ascii').split(':')
            if len(splited) != 2:
                return make_response(jsonify({'code': 1202, 'msg': 'Bad request', 'data': ''}), 400)
            request.auth_user, request.auth_password = splited
        except binascii.Error as e:
            return make_response(jsonify({'code': 1202, 'msg': 'Bad request', 'data': ''}), 400)
        conn = request.current_conn
        conn.begin()
        c = conn.cursor()
        try:
            affected = c.execute('select auth.secret, user.access_verbs, user.id from auth inner join user on auth.uid=user.id where auth.username=%s', (request.auth_user,))
            secret, verbs, uid = c.fetchall()[0]
            verbs = verbs.split(' ')
            require_secret = password_hash(request.auth_password)
            if require_secret != secret:
                return make_response(jsonify({'code': 1201, 'msg': 'Invali User or Password', 'data':'' }), 403)
            request.current_user_verbs = set(verbs)
            request.auth_user_id = uid
        except Exception as e:
            conn.rollback()
            raise e

        finally:
            conn.commit()

        return None


    def cookie_token_auth(self):
        token = request.cookies.get('token', None)
        if token is not None:
            valid, token_type, username, user_id, expire, verbs = decode_token(token)
            if valid and token_type == 'auth':
                request.auth_user = username
                request.current_user_verbs = verbs
                request.auth_user_id = user_id
                return True

        return False


    def dispatch_request(self):
        # Authorize
        # set request.auth_user, request.auth_password and request.current_user_verbs if user succeeds to login.
        # set request.current_conn to mysql connection
        try:
            auth_expire = current_app.config.get('AUTH_TOKEN_EXPIRE_DEFAULT', 86400)
            request.current_conn = current_app.mysql.connect()
            new_auth_token = None
            new_auth_token_expire = None
            
            if not self.cookie_token_auth():
                resp = self.http_basic_auth()
                if resp is not None:
                    return resp
                # Generate 
                new_auth_token_expire = datetime.now() + timedelta(seconds=auth_expire)
                new_auth_token = new_encoded_token(request.auth_user, 0, request.current_user_verbs, request.current_user_verbs, _expire = new_auth_token_expire, _token_type = 'auth')
                
            resp = super().dispatch_request()


            if new_auth_token:
                resp.set_cookie('token', value = new_auth_token, domain = request.environ['SERVER_NAME'], expires = new_auth_token_expire.timestamp(), path = '/sso')
 
        except Exception as e:
            expection_id = uuid.uuid4()
            exc_info = 'Exception %s: \n' % str(expection_id).replace('-', '') + format_exc()
            current_app.log_error(exc_info)
            print(exc_info)
            return make_response(jsonify({'code': 1504, 'msg': 'Server throw an exception with ID: %s' % expection_id, 'data': ''}), 500)
        finally:
            request.current_conn.close()

        return resp


    def get(self):
        args = request.args.copy()
        type_checker = post_data_type_checker(appid = int, redirectURL = str)
        ok, err_msg = type_checker(args)
        if not ok:
            return make_response('Wrong arguments submitted.')

        appid = args.get('appid', None)
        if appid is None:
            return make_response(jsonify({'code': 0, 'msg': 'succeed', 'data':''}), 200)


        redirect_url = args.get('redirectURL', None)
        app_expire = current_app.config.get('APP_TOKEN_EXPIRE_DEFAULT', 86400)

        conn = request.current_conn
        conn.begin()
        c = conn.cursor()
        try:
            affected = c.execute('select application.name, application.redirect_prefix, app_bind.access_verbs from application inner join app_bind on app_bind.appid=application.id where app_bind.appid=%s', (appid,))
            conn.commit()
            if affected < 1:
                return make_response(jsonify({'code': 1423, 'msg' : 'No such application', 'data': ''}), 200)
            name, redirect_prefix, verbs = c.fetchall()[0]

            if redirect_url is not None and redirect_url[:len(redirect_prefix)] != redirect_prefix:
                return make_response('Invalid redirect URL prefix.', 200)

            application_verbs = verbs.split(' ')
            expire = datetime.now() + timedelta(seconds=app_expire)
            app_token = new_encoded_token(request.auth_user, request.auth_user_id, application_verbs, request.current_user_verbs, _expire = expire, _token_type = 'application')

        except Exception as e:
            conn.rollback()
            raise e

        if not redirect_url: 
            return make_response(jsonify({'code': 0, 'msg': 'succeed', 'data': {'token': app_token}}), 200)

        full_redir_url = redirect_url + '?' + werkzeug.url_encode({
            'appid': appid
            , 'token': app_token
        })

        return redirect(full_redir_url, 302)
        
