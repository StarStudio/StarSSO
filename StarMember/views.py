import uuid
import json
#import requests

from datetime import datetime
from flask import current_app, jsonify, request, make_response, Response, redirect
from flask.views import MethodView
from werkzeug.urls import url_encode
from traceback import print_exc, format_exc
from .utils.param import get_request_params
from .utils.security import decode_token
from .utils.device import get_real_remote_address
from .utils.network import Network
from functools import wraps
from struct import pack, unpack


def resource_access_denied(_msg = 'You have no access to this resources'):
    return make_response(jsonify({'code': 1201, 'msg': _msg, 'data': ''}), 403)

def param_error(_msg = 'Wrong params'):
    return make_response(jsonify({'code': 1422, 'msg': _msg, 'data': ''}), 200)

def api_succeed(_data = ''):
    return jsonify({'code': 0, 'msg': 'succeed', 'data': _data})

def api_user_pending(_data = ''):
    return jsonify({'code': 0, 'msg': 'Pending user', 'data': _data})

def api_wrong_params(_error = ''):
    return jsonify({'code': 1422, 'msg': _error, 'data': ''})

def api_not_avaliable(_msg = 'Not avaliable.'):
    return jsonify({'code': 1402, 'msg': _msg, 'data': ''})

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


#def with_device_information(deny_illegal_device = True, _proxy_ident_args_name = 'pagent', _proxy_token_args_name = 'ptoken'):
#    def encapsulate_data(_addition, _origin):
#        return pack('Lss', len(_origin), _origin, _addition)
#
#    def unencapsulate_data(_raw):
#        origin_len = unpack('L', _raw[0:4])
#        if origin_len > len(_raw) - 4:
#            return None, None, 'Check not passed.'
#        return _raw[4: 4 + origin_len], _raw[4 + origin_len:], None
#
#    def as_apiserver(_function, *args, **kwargs):
#        remote_addr = get_real_remote_address()
#        net = None
#        if remote_addr != '':
#            net = Network.FromIP(remote_addr)
#        else:
#            if deny_illegal_device:
#                return resource_access_denied()
#            return None
#
#        # Device doesn't belong to any registered local network.
#        if net is None:
#            if deny_illegal_device:
#                return resource_access_denied()
#            else:
#                return None
#        # Set device information property for view func.
#        request.from_net = net
#
#        # Check whether a proxied request.
#        proxyed = request.args.get(_proxy_ident_args_name, None)
#        if proxyed is not None: # proxied.
#            if proxyed != 1:
#                abort(400)
#            addition, origin, msg = unencapsulate_data(request.data)
#            if msg is not None:
#                return param_error('Proxy data corrupted: %s' % msg)
#            request.data = origin # Restore data.
#            return _function(*args, **kwargs)
#
#        # Redirect: require request by local agent.
#        redir_token = ProxyToken(_nid = Network.LocalAgentIP).make_signed_token()
#        new_args = request.args.copy()
#        new_args[_proxy_token_args_name] = redir_token
#        new_args[_proxy_ident_args_name] = request.url_root # Proxy to
#        redir_url = 'http://' + net.PublishIP + request.environ['PATH_INFO'] + '?' + url_encode(new_args)
#
#        return redirect(redir_url)
#        
#
#    def as_agent(_function, *args, **kwargs):
#        remote_addr = get_real_remote_address()
#        if remote_addr == '':
#            return resource_access_denied()
#
#        token = request.args.get(_proxy_token_args_name, None)
#        if token is None:
#            return param_error('Proxy token missing.')
#        proxy_to = request.args.get(_proxy_ident_args_name, None)
#        if token is None:
#            return param_error('Proxy-to URL root missing.')
#
#        proxy_metadata = json.dumps({
#            'token': token
#            , 'proxy_for': remote_addr
#        })
#        enp_data = encapsulate_data(proxy_metadata, request.data)
#        ori_args = request.args.copy()
#        
#        queries = url_encode({
#            _proxy_ident_args_name: 1
#        })
#        url = proxy_to + request.environ['PATH_INFO'] + '?' + url_encode({ _proxy_ident_args_name: 1})
#        req = requests.Request(request.environ['REQUEST_METHOD'], headers = request.headers, data = enp_data)
#        resp = requests.Session().send(req)
#        headers = resp.headers.copy()
#        headers['Access-Control-Allow-Credentials'] = True
#        headers['Access-Control-Allow-Origin'] = proxy_to
#        return make_response((resp.content, resp.status_code, resp.headers))
#
#
#    def decorate(_function):
#        @warps(_function)
#        def decorated(*args, **kwargs):
#            server_mode = current_app.config['SERVER_MODE']
#            if server_mode == 'APIServer':
#                return as_apiserver(_function, *args, **kwargs)
#            elif server_mode == 'Agent':
#                return as_agent(_function, *args, **kwargs)
#            else:
#                return RuntimeError('Unknown Server Mode. Check configure please.')
            
            


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
            try:
                log_info['result'] = json.loads(result.data.decode())
            except json.JSONDecodeError as e:
                log_info['result'] = result.data.decode()

            current_app.access_logger.info(json.dumps(log_info))
            return result

        except Exception as e:
            exc_uuid = uuid.uuid4()
            print_exc()
            exc_info = format_exc()
            current_app.error_logger.error(exc_info + '\n Exception ID: %s' % str(exc_uuid))
            return jsonify({
                'code': 1505
                , 'msg': 'Server raises a exception with id %s' % str(exc_uuid)
                , 'data': ''
            })

