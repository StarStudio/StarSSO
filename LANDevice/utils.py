
def IPv4ToInt(_ipv4):
    if _ipv4.__class__ is int:
        if _ipv4 > 0xFFFFFFFF:
            return -1
        return _ipv4
    parts = _ipv4.split('.')
    if len(parts) != 4:
        return -1

    target = 0
    try:
        for part in parts:
            target = (target << 8 ) + int(part)
    except ValueError as e:
        return -1

    return target


def IntToIPv4(_integer):
    if _integer > 0xFFFFFFFF:
        return ''
       
    return '.'.join([str(((0xFF000000 >> 8 * i) & _integer) >> (3 - i) * 8) for i in range(0, 4)])
