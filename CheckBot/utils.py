import re

RE_MAC_PATTEN = re.compile('^(?:[0-9a-fA-F]{2}:){5}(?:[0-9a-fA-F]{2})$')

def MACToInt(_mac):
    '''
        Convert MAC address to int
    '''
    if not RE_MAC_PATTEN.match(_mac):
        raise ValueError('Invalid MAC format.')

    return int(_mac.replace(':', ''), 16)

def IntToMAC(_mac):
    '''
        Convert int to MAC address
    '''
    if _mac > 0xFFFFFFFFFFFF:
        return ValueError('MAC integer is too big.')
    digits = list('%012x' % _mac)
    return ':'.join([digits[i] + digits[i+1] for i in range(0, len(digits), 2)])
