from flask import request, current_app, jsonify
from StarMember.views import SignAPIView
from StarMember.utils import get_real_remote_address

class MyselfDeviceView(SignAPIView):
    method = ['GET']

    def get(self):
        map_device = {ip: mac for mac, ips in current_app.device_list.Snapshot().items() for ip in ips}
        remote_addr = get_real_remote_address()
        addr = map_device.get(remote_addr, None)
        
        return jsonify({
            'code': 200
            , 'msg' : 'succeed'
            , 'data' : addr
        })
