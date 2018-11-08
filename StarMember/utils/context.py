import json
import re
import uuid

from .network import Network
from .device import get_real_remote_address
from .security import ShimToken, ShimResponseToken

from flask import request, current_app, redirect
from StarMember.views import resource_access_denied
from werkzeug.urls import url_encode
from jwcrypto.jwt import JWT, JWTExpired
from jwcrypto.jws import InvalidJWSSignature


ID_RE = re.compile('^[a-f0-9]{32}$')
SHIM_REDIRECT_PATH = '/v1/star/device/information_shim'

def default_redis_getter():
    return current_app.redis_store

def default_redis_prefix_getter():
    return current_app.config['LAN_DEV_REDIS_PROBER_IDENT_PREFIX']

class APIRequestContext(dict):
    def __init__(self, _context_id_query_key = 'rctx', _id = None, _timeout = 10, _redis_getter = default_redis_getter, _redis_prefix_getter = default_redis_prefix_getter):

        self._context_id_query_key = _context_id_query_key
        self._redis_getter = _redis_getter
        self._redis_prefix_getter = _redis_prefix_getter
        self._timeout = _timeout

        self._id = _id
        self._mac = None
        self._net = None
        self._local_ip = None
        self._public_ip = None

    
    def Suspend(self):
        '''
            Save context.
        '''
        if self._id is None:
            self._id = str(uuid.uuid4()).replace('-', '')
        redis = self._redis_getter()

        json_data = json.dumps(self).encode('utf8')
        redis.set(self._redis_context_prefix + self._id, json_data, ex = self._timeout)


    def _load_basic_client_information(self):
        '''
            Try to get basic client information
        '''
        remote_addr = get_real_remote_address()
        if remote_addr != '':
            self._public_ip = remote_addr
            self._net = Network.FromIP(remote_addr)

    def _resolve_device_mac(self):
        '''
            Resolve Device MAC
        '''
        map_device = {nid: {ip: mac for ip in ips} for mac, (nid, ips) in current_app.device_list.Snapshot().items()}
        if self._net and self._net.ID in map_device:
            if self._local_ip in map_device[self._net.ID]:
                self.mac = map_device[self._net.ID][self._local_ip]

        
    def ResumeFromRequest(self):
        '''
            Load context according to request parameters.

            :return:
                return True when context is loaded successfully.
                Otherwise, return False.
        '''
        self._load_basic_client_information()

        # Try to get previous context ID
        if self._context_id_query_key not in request.args:
            return False
        raw = request.args[self._context_id_query_key]
        try:
            token = APIToken.FromString(raw)
        except (InvalidJWSsignature, JWTExpire, ValueError) as e:
            return False

        if not isinstance(token, ShimResponseToken):
            return False
        rid = token.RequestID
        if not ID_RE.match(rid):
            return False
        self._id = rid

        # Load device MAC and Local IP here
        self._local_ip = token.LocalIP
        if self._net is None:
            nid = token.NetworkID
            self._net = NetworkID(nid)


        return self.Resume()
        

    def Resume(self):
        '''
            Load context

            :return:
                return True when context is loaded successfully.
                Otherwise, return False.
        '''
        redis = self._redis_getter()
        raw = redis.get(self._redis_context_prefix + self._id)
        if raw is None:
            return False
        try:
            ctx_data = json.loads(raw)
        except json.JSONDecodeError as e:
            return False
        self.update(ctx_data)
        return True


    def RedirectForDeviceInfo(self):
        '''
            Make redirect response to local agent.
        '''
        if self._net is None or self._public_ip is None:
            self._load_basic_client_information()
            if self._net is None:
                return resource_access_denied()
        token = ShimToken(_redirect = request.url, _query_key = self._context_id_query_key, _request_id = self.ID, _timeout = 10)
        token.make_signed_token()
        querys = url_encode({
                "token": token.serialize()
        })
        redirect_to = 'http://' + self._net.LocalAgentIP + ':8000' + SHIM_REDIRECT_PATH + '?' + querys
        return redirect(redirect_to)
        
        

    @property
    def _redis_context_prefix(self):
        return self._redis_prefix_getter() + '_rcontext_'

    @property
    def ID(self):
        if self._id is None:
            self._id = str(uuid.uuid4()).replace('-', '')
        return self._id

    @property
    def Net(self):
        return self._net

    @property
    def MAC(self):
        if self._mac is None:
            self._resolve_device_mac()
        return self._mac

    @property
    def LocalIP(self):
        return self._local_ip

    @property
    def PublicIP(self):
        return self._public_ip
