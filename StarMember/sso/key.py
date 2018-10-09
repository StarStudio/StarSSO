from flask import current_app, make_response, request, jsonify
from flask.views import MethodView

class PublicKeyView(MethodView):
    method = ['GET']

    def get(self):
        return jsonify({
            'code': 0
            , 'data' : {
                'pem': current_app.jwt_key.export_to_pem().decode('ascii')
            }
            , 'msg': 'succeed.'
        })
