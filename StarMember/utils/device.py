from flask import request
from StarMember.agent.utils import IPv4ToInt


def get_real_remote_address():
    '''
        Get real remote IP according to HTTP Header
    '''
    forward_chain = request.headers.get('X-Forwarded-For', None)
    if forward_chain is None:
        ipv4_int = -1
    else:
        last = forward_chain.split(',')[-1].strip()
        ipv4_int = IPv4ToInt(last)

    if ipv4_int < 0:
        return request.remote_addr

    return last

