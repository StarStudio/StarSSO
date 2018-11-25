from flask import Blueprint
from .login import LoginView
from .logout import LogoutView
from .key import PublicKeyView


sso_api = Blueprint('SSO', __name__)

sso_api.add_url_rule('/login', view_func=LoginView.as_view('SSOLogin'))
sso_api.add_url_rule('/logout', view_func=LogoutView.as_view('SSOLogout'))
sso_api.add_url_rule('/publickey', view_func=PublicKeyView.as_view('SSOPublicKey'))

@sso_api.route('/', methods=['GET'])
def hello_sso():
    return "Starstudio SSO."
