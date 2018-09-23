import uuid
import json
import uuid
import json
from datetime import datetime
from flask import current_app, jsonify, request
from flask.views import MethodView
from traceback import print_exc, format_exc

class SignAPIView(MethodView):
    def dispatch_request(self, *arg, **kwarg):
        try:
            log_info = {}
            log_info['method'] = request.environ['REQUEST_METHOD']
            log_info['uri'] = request.environ['PATH_INFO']
            log_info['time'] = str(datetime.now())
            if len(request.form) > 0:
                log_info['form'] = request.form.copy()
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

