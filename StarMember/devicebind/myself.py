from flask import request, current_app, jsonify
from StarMember.views import SignAPIView

class MyDeviceView(SignAPIView):
    method = ['GET']

    def get(self):
        map_device = {ip: mac for mac, ips in current_app.device_list.Snapshot().items() for ip in ips}
        addr = map_device.get(request.remote_addr, None)
        
        return jsonify({
            'code': 200
            , 'msg' : 'succeed'
            , 'data' : addr
        })
