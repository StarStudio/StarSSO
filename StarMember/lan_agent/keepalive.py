from StarMember.views import SignAPIView, param_error, api_succeed
from StarMember.utils import get_request_params, get_real_remote_address
from StarMember.aspect import post_data_type_checker, post_data_key_checker
from .network import Network, InvalidNetworkIDError
from flask import request, current_app

class LANKeepalive(SignAPIView):
    method = ['POST']

    def post(self, nid):
        params = get_request_params()
        type_checker = post_data_type_checker(local_ip = str)
        key_checker = post_data_key_checker('local_ip')
        ok, err_msg = key_checker(params)
        if not ok:
            return param_error(err_msg)
        ok, err_msg = type_checker(params)
        if not ok:
            return param_error(err_msg)


        try:
            net = Network(nid)
            net.LocalAgentIP = params['local_ip']
            remote_addr = get_real_remote_address()
            if remote_addr is None:
                current_app.log_error('Cannot get remote address. nid=%s, local_ip=%s' % (nid, params['local_ip']))
                remote_addr = ''
            net.PublishIP = remote_addr
        except InvalidNetworkIDError as e:
            return param_error(str(e))

        return api_succeed()
        

