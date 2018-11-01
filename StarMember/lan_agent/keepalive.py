from StarMember.views import SignAPIView, param_error, api_succeed
from StarMember.utils import get_request_params
from StarMember.aspect import post_data_type_checker, post_data_key_checker
from .network import Network, InvalidNetworkIDError

class LANKeepalive(SignAPIView):
    method = ['POST']

    def post(self, nid):
        params = get_request_params()
        type_checker = post_data_type_checker(local_ip = str)
        key_checker = post_data_key_checker('devices')
        ok, err_msg = key_checker(params)
        if not ok:
            return param_error(err_msg)
        ok, err_msg = type_checker(params)
        if not ok:
            return param_error(err_msg)

        try:
            net = Network(nid)
            net.LocalAgentIP = params['local_ip']
        except InvalidNetworkIDError as e:
            return param_error(str(e))

        return api_succeed()
        

