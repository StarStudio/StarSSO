from StarMember.views import SignAPIView, param_error, api_succeed
from StarMember.aspect import post_data_type_checker, post_data_key_checker
from StarMember.utils import get_request_params
from flask import request, current_app
from .network import Network, InvalidNetworkIDError

class LANDeviceSubmit(SignAPIView):
    method = ['POST']

    def post(self, nid):
        params = get_request_params()
        print(params)
        key_checker = post_data_key_checker('devices')
        ok, err_msg = key_checker(params)
        if not ok:
            return param_error(err_msg)
        devices = params['devices']
        if not isinstance(devices, list):
            return param_error('Arg devices has wrong type.')
        
        try:
            net = Network(nid)
            net.UpdateDevices(devices)
        except (InvalidNetworkIDError, ValueError) as e:
            return param_error(str(e))

        return api_succeed()
