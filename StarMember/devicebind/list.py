from flask import request, current_app, jsonify
from StarMember.views import SignAPIView, with_application_token, resource_access_denied
from StarMember.agent import LANDeviceProberConfig

class DeviceListView(SignAPIView):
    method = ['GET']

    @with_application_token(deny_unauthorization = True)
    def get(self):
        if 'read_self' not in request.app_verbs\
            and 'read_internal' not in request.app_verbs \
            and 'read_other' not in request.app_verbs:
            return resource_access_denied()

        return jsonify({
                    'code': 200
                    , 'data' : {mac: { 'IPs' : list(ips) } for mac, (nid, ips) in current_app.device_list.Snapshot().items()}
                    , 'msg' : 'succeed'
                })
