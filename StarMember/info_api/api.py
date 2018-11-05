from flask import Blueprint
from .group import GroupAPIView
from .member import MemberAPIView, MemberAccessView
#from .token import TokenAuthView
import ipdb

info_api = Blueprint("MemberAPI", __name__, url_prefix = "/v1/star")

@info_api.route('/',  methods=['GET', 'POST', 'OPTIONS'])
def ping():
    ipdb.set_trace()
    return 'StarStudio Sign System'

info_api.add_url_rule('/member', view_func=MemberAPIView.as_view('MemberAPI'))
info_api.add_url_rule('/member/<int:uid>', view_func=MemberAccessView.as_view('MemberAccessAPI'))
info_api.add_url_rule('/group', view_func=GroupAPIView.as_view('GroupAPI'))
