from StarMember.views import SignAPIView, resource_access_denied, param_error, api_succeed
from StarMember.utils import get_request_params
from StarMember.aspect import post_data_type_checker, post_data_key_checker
from flask import current_app
from .token import verify_register_token, check_register_token
from .network import Network, new_network_id, InvalidNetworkIDError

# /v1/star/local_network/<id:int>/info/agent
class LANAgentInfo(SignAPIView):
    method = ['GET', 'DELETE']

# Pigeoned temporarily
class LANDeviceInfo(SignAPIView):
    method = ['GET']


# /v1/star/local_network/<str:nid>/device
class LANDeviceSubmit(SignAPIView):
    method = ['PUT', 'GET']

    def get(self, nid):
        return api_succeed('Pigeoned temporarily')

    def put(self, nid):
        pass
