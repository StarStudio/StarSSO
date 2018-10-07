from flask import Blueprint
from .login import LoginView
from .logout import LogoutView

sso_api = Blueprint('Single Sign-on', __name__, url_prefix = '/sso')

sso_api.add_url_rule('/login', view_func=LoginView.as_view('SSOLogin'))
sso_api.add_url_rule('/logout', view_func=LogoutView.as_view('SSOLogout'))

@sso_api.route('/', methods=['GET'])
def hello_sso():
    return "Starstudio SSO."
