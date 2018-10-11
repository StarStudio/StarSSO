from flask import Blueprint, current_app
from .list import DeviceListView
from .myself import MyDeviceView
from LANDevice import DeviceList, LANDeviceProberConfig

bind_api = Blueprint('DeviceBindAPI', __name__, url_prefix = '/v1/star/device')
bind_api.add_url_rule('/list', view_func = DeviceListView.as_view('DeviceList'))
bind_api.add_url_rule('/myself', view_func = MyDeviceView.as_view('MyselfDevice'))


@bind_api.before_app_request
def bind_api_init():
    current_app.landev_cfg = LANDeviceProberConfig()
    current_app.landev_cfg.FromDict(current_app.config)
    current_app.device_list = DeviceList(current_app.landev_cfg)
