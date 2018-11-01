from StarMember.views import SignAPIView, param_error, api_succeed
from StarMember.utils import get_request_params
from StarMember.aspect import post_data_type_checker, post_data_key_checker
from .network import Network, InvalidNetworkIDError, new_network_id

class LANRegister(SignAPIView):
    method = ['POST']

    def get(self):
        params = get_request_params()
        type_checker = post_data_type_checker(register_token = str)
        key_checker = post_data_key_checker('register_token')

        ok, err_msg = key_checker(params)
        if not ok:
            return param_error(err_msg)
        ok, err_msg = type_checker(params)
        if not ok:
            return param_error(err_msg)

        if not check_register_token(params['register_token']):
            return param_error('Wrong register token format.')
        if not verify_register_token(params['register_token']):
            return param_error('Invalid register token.')

        nid = new_network_id()
        net = Network(nid, _register = True)
        net.Verify(_raise_exception = True)
        return api_succeed({ 'network_id' : nid })
