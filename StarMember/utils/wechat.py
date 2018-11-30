import requests

from flask import current_app
from .application import ApplicationMetadata
from StarMember.config import ConfigureError


def session_from_code(_code, _appid):
    '''
        Get wechat session from code.

        :params:
            _code       Wechat code.
            _appid      AppID in authserver.

        :return:
            (session_key, (openid, union_id), (errcode, err_msg)) or (None, None, None)

        :raises:
            ConfigureError      If WECHAT_CODE2SESSION_API not configured correctly.
    '''
    meta = ApplicationMetadata.FromApplicationID(_appid)
    we_appid = meta._get_default('wechat', 'appid', default = None)
    we_appsecret = meta._get_default('wechat', 'app_secret', default = None)
    if we_appid is None or we_appsecret is None:
        return (None, None, None)

    c2s_api = current_app.config.get('WECHAT_CODE2SESSION_API', None)
    if c2s_api is None:
        raise ConfigureError('Wrong configure value to WECHAT_CODE2SESSION_API: %s' % str(c2s_api))
    resp = requests.get(c2s_api, params = {
            'appid': we_appid
            , 'secret': we_appsecret
            , 'grant_type': 'authorization_code'
            , 'jd_code' : _code
        })

    try:
        resp_json = resp.json()
    except ValueError as e:
        return (None, None, None)

    return (resp_json.get('session_key', None), (resp_json.get('unionid', None), resp_json.get('openid', None))
            , (resp_json.get('errcode', None), resp_json.get('errmsg', None)))
