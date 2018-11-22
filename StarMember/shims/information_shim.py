from StarMember.views import SignAPIView, api_wrong_params
from StarMember.utils.device import get_real_remote_address
from StarMember.utils.param import get_request_params
from StarMember.utils.security import APIToken, ShimToken, ShimResponseToken
from jwcrypto.jws import InvalidJWSSignature
from jwcrypto.jwt import JWTExpired

from flask import current_app, request, redirect
from werkzeug.urls import url_encode

class InformationShimView(SignAPIView):
    method = ['GET']

    def get(self):
        token = request.args.get('token', None)

        if token is None:
            return api_wrong_params('Token missing.')

        try:
            token = APIToken.FromString(token)
        except (InvalidJWSSignature, JWTExpired, ValueError) as e:
            return api_wrong_params('Invalid Token.')
        if not isinstance(token, ShimToken):
            return api_wrong_params('Invalid Token type.')

        remote_addr = get_real_remote_address()
        if remote_addr == '':
            api_wrong_params('Cannot get remote address.')

        if not isinstance(token.Redirect, str) \
            or not isinstance(token.RequestID, str) \
            or not isinstance(token.QueryKey, str):
            return api_wrong_params('Invalid Request.')
        
        rtoken = ShimResponseToken(
                _request_id = token.RequestID
                , _network_id = current_app.network_id
                , _local_ip = remote_addr
                , _timeout = 10)

        rtoken.make_signed_token()
        queries = url_encode({
            token.QueryKey: rtoken.serialize()
        })

        return redirect(token.Redirect + '?' + queries)
