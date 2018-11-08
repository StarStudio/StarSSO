from flask import request, current_app, jsonify
from StarMember.views import SignAPIView
from StarMember.utils.device import get_real_remote_address
from StarMember.utils.context import APIRequestContext
from StarMember.views import api_succeed

import ipdb

class MyselfDeviceView(SignAPIView):
    method = ['GET']

    def get(self):
        ipdb.set_trace()
        ctx = APIRequestContext()
        if not ctx.ResumeFromRequest(): # first request.
            if not ctx.MAC: # No device MAC found.
                ctx.Suspend()
                return ctx.RedirectForDeviceInfo()
        elif not ctx.Net or not ctx.MAC or not ctx.LocalIP:
            return api_succeed({
                'code': 200
                , 'msg' : 'succeed'
                , 'data': None
            })

        
        #map_device = {ip: mac for mac, ips in current_app.device_list.Snapshot().items() for ip in ips}
        
        #map_device = {nid: {ip: mac for ip in ips} for mac, (nid, ips) in current_app.device_list.Snapshot().items()}
        #remote_addr = get_real_remote_address()
        #addr = map_device.get(remote_addr, None)
        #mac = None
        #if ctx.Net.ID in map_device:
        #    if ctx.LocalIP in map_device[ctx.Net.ID]:
        #        mac = map_device[ctx.Net.ID][ctx.LocalIP]

        return jsonify({
            'code': 200
            , 'msg' : 'succeed'
            , 'data' : ctx.MAC
        })
