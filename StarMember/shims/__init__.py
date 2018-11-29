from flask import Blueprint, current_app
from .information_shim import InformationShimView
from StarMember.agent import DeviceList, LANDeviceProberConfig

shim_api = Blueprint('Shims', __name__)

shim_api.add_url_rule('/information', view_func = InformationShimView.as_view('Information'))


#@shim_api.before_app_request
#def load_device_list_port():
#    current_app.landev_cfg = LANDeviceProberConfig()
#    current_app.landev_cfg.FromDict(current_app.config)
#    current_app.device_list = DeviceList(current_app.landev_cfg)


