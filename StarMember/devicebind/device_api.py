from flask import Blueprint, current_app
from .list import DeviceListView
from .myself import MyselfDeviceView
from .bind import BindView, BindManageView
from .shims import InformationShimView

from StarMember.agent import DeviceList, LANDeviceProberConfig

bind_api = Blueprint('DeviceBindAPI', __name__, url_prefix = '/v1/star/device')
bind_api.add_url_rule('/list', view_func = DeviceListView.as_view('DeviceList'))
bind_api.add_url_rule('/myself', view_func = MyselfDeviceView.as_view('MyselfDevice'))
bind_api.add_url_rule('/mine', view_func =  BindView.as_view('Mine'))
bind_api.add_url_rule('/mine/<string:mac>', view_func = BindManageView.as_view('BindManage'))
bind_api.add_url_rule('/infomation_shim', view_func = InformationShimView.as_view('InformationShim'))



@bind_api.before_app_request
def bind_api_init():
    current_app.landev_cfg = LANDeviceProberConfig()
    current_app.landev_cfg.FromDict(current_app.config)
    current_app.device_list = DeviceList(current_app.landev_cfg)
