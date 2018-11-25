from flask import Blueprint
from .register import LANRegister
from .keepalive import LANKeepalive
from .submit import LANDeviceSubmit

net_api = Blueprint('NetworkAPI', __name__)

net_api.add_url_rule('', view_func = LANRegister.as_view('Register'))
net_api.add_url_rule('/<string:nid>/liveness', view_func = LANKeepalive.as_view('Keepalive'))
net_api.add_url_rule('/<string:nid>/device', view_func = LANDeviceSubmit.as_view('Submit'))
