import uuid
import json

from datetime import datetime
from flask import current_app, jsonify, request, make_response, Response
from flask.views import MethodView
from traceback import print_exc, format_exc
from .utils import decode_token, get_request_params
from functools import wraps


def resource_access_denied():
    return make_response(jsonify({'code': 1201, 'msg': 'You have no access to this resources', 'data': ''}), 403)

def require_login(_realm = 'You are not logined.'):
    resp = make_response(jsonify({'code': 1201, 'msg': 'No Authorization', 'data': ''}), 401)
    resp.headers['WWW-Authenticate'] = 'Basic realm="%s"' % _realm
    return resp

def param_error(_msg = 'Wrong params'):
    return make_response(jsonify({'code': 1422, 'msg': _msg, 'data': ''}), 200)

def api_succeed(_data = ''):
    return jsonify({'code': 0, 'msg': 'succeed', 'data': _data})

def api_user_pending(_data = ''):
    return jsonify({'code': 0, 'msg': 'Pending user', 'data': _data})

def api_wrong_params(_error = ''):
    return jsonify({'code': 1422, 'msg': _error, 'data': ''})

#def with_access_verbs(*need_verbs):
#    combined_needs = []
#    single_needs = []
#    for needs in need_verbs:
#        if isinstance(needs, (tuple, list)):
#            combined_needs.append(needs)
#        else:
#            single_needs.append(needs)
#
#    combined_needs = tuple(combined_needs)
#    single_needs = tuple(single_needs)
#            
#    def decorate(_function):
#        @wraps(_function)
#        def decorated(*args, **kwargs):
#            app_verbs = request.app_verbs
#            for verb in single_needs:
#                if verb not in app_verbs:
#                    return resouce_access_denied()
#            for verbs in combined_needs:
#                satisfied = False
#                for verb in verbs:
#                    if verb in app_verbs:
#                        satisfied = True
#                        break
#                if not satisfied:
#                    return resource_access_denied()
#            return _function(*args, **kwargs)
#        return decorated
#    return decorate

def try_http_bearer_auth():
    auth_header = request.headers.get('Authorization', None)
    if None is auth_header:
        return False
    splited = auth_header.split(' ')

    if len(splited) != 2:
        abort(400)
    method, auth_content = splited
    if method != 'Bearer':
        return False
        # return make_response(jsonify({'code': 1202, 'msg': 'Unsupported authorization method.', 'data': ''}), 403)

    request.auth_token = auth_content
    return True
    

def try_cookie_token_auth():
    token = request.cookies.get('token', None)
    if token is None:
        return False
    request.auth_token = token
    return True


def with_application_token(deny_unauthorization = True):
    def decorate(_function):
        @wraps(_function)
        def decorated(*args, **kwargs):
            auth_err_response = None
            if not try_http_bearer_auth() and not try_cookie_token_auth():
                auth_err_response = make_response(jsonify({'code': 1201, 'msg': 'No Authorization', 'data': ''}), 403)
                if deny_unauthorization:
                    return auth_err_response
            else: 
                valid, token_type, username, user_id, expire, verbs = decode_token(request.auth_token)
                if not valid or token_type != 'application':
                    auth_err_response = make_response(jsonify({'code': 1201, 'msg': 'No Authorization', 'data': ''}), 403)
                    #auth_err_response = Response(jsonify({'code': 1201, 'msg': 'No Authorization', 'data': ''}), 401, {'WWW-Authenticate': 'Basic realm="You are not logined."'})
                    if deny_unauthorization:
                        return auth_err_response

                request.auth_user = username
                request.auth_user_id = user_id
                request.app_verbs = verbs

            request.auth_err_response = auth_err_response
            return _function(*args, **kwargs)
        return decorated
    return decorate


class SignAPIView(MethodView):

    def dispatch_request(self, *arg, **kwarg):
        try:
            log_info = {}
            log_info['method'] = request.environ['REQUEST_METHOD']
            log_info['uri'] = request.environ['PATH_INFO']
            log_info['time'] = str(datetime.now())
            request_data = get_request_params()
            if request_data:
                log_info['request_data'] = request_data

            result =  super().dispatch_request(*arg, **kwarg)
            log_info['result'] = json.loads(result.data.decode())
            current_app.access_logger.info(json.dumps(log_info))
            return result

        except Exception as e:
            exc_uuid = uuid.uuid4()
            print_exc()
            exc_info = format_exc()
            current_app.error_logger.error(exc_info + '\n Exception ID: %s' % str(exc_uuid))
            return jsonify({
                'code': 1505
                , 'msg': 'Server raises a exception with id %s' % str(uuid.uuid4())
                , 'data': ''
            })

