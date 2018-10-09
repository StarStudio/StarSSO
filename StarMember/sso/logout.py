import uuid

from flask import current_app, request, make_response
from flask.views import MethodView
from traceback import format_exc
from StarMember.aspect import post_data_type_checker
from StarMember.utils import decode_token


class LogoutView(MethodView):
    method = ['GET']

    def get(self):
        args = request.args.copy()
        type_checker = post_data_type_checker(redirectURL = str)
        ok, err_msg = type_checker(args)

        resp = None
        redirect_url = args.get('redirectURL', None)
        if redirect_url is not None:
            resp = redirect(redirect_url, 302)

        if not ok:
            return make_response('Wrong arguments submitted.', 400)
        
        token = request.cookies.get('token', None)
        if token is None:
            if resp is None:
                resp = make_response('You are not logined.', 200)
        else:
            valid, token_type, username, _, _, _ = decode_token(token)
            if resp is None:
                if not valid:
                        resp = make_response('Invalid login state.', 200)
                else:
                        resp = make_response('Logout.', 200)
    
            resp.set_cookie('token', expires = 0, path = '/sso')

        return resp  
        

    def dispatch_request(self):
        try:
            return super().dispatch_request()
        except Exception as e:
            expection_id = uuid.uuid4()
            exc_info = 'Exception %s: \n' % str(expection_id).replace('-', '') + format_exc()
            current_app.log_error(exc_info)
            print(exc_info)
            return make_response('Server throw an exception with ID: %s' % expection_id, 500)
