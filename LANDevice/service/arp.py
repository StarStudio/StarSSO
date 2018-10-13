import socket
import netifaces
from struct import Struct, unpack
from LANDevice.utils import IPv4ToInt, IntToIPv4
from datetime import timedelta, datetime


ETH_P_ARP = 0x806
ARP_OP_REQUEST = 1
ARP_OP_RESPONSE = 2
RARP_OP_REQUEST = 3
RARP_OP_RESPONSE = 4

def mac_normalizer(mac):
    try:
        if type(mac) is str:
            parts = [int(part, 16) for part in mac.split(':')]
            if len(parts) != 6:
                raise ValueError('Has invalid length.')
            return bytes(parts)
        elif type(mac) is int:
            return bytes([mac & ((0xFF << offset) ^ 0xFFFFFFFFFFFF) for offset in range(40, -8, -8)])
        elif type(mac) is bytes:
            return mac
    except ValueError as e:
        raise ValueError('Invalid MAC Address %s' % str(e))
        
class ARPETHFrame:

    FIELD_LIST = frozenset([
        ('HWSrc', (int, str, bytes), mac_normalizer)
        , ('HWDst', (int, str, bytes), mac_normalizer)
        , ('FrameType', int, None)
        , ('HWType', int, None)
        , ('ProtocolType', int, None)
        , ('HWProLen', int, None)
        , ('ProLen', int, None)
        , ('OP', int, None)
        , ('SenderMAC', (int, str, bytes), mac_normalizer)
        , ('SenderIP', (int, str, bytes), IPv4ToInt)
        , ('DestinationMAC', (int, str, bytes), mac_normalizer)
        , ('DestinationIP', (int, str, bytes), IPv4ToInt)
    ])

    ARP_FRAME_STRUCT = Struct('!6s6sHHHBBH6sL6sL')


    HWDst = b'\xFF\xFF\xFF\xFF\xFF\xFF'
    HWSrc = b'\x00\x00\x00\x00\x00\x00'
    FrameType = 0x0806
    HWType = 1
    ProtocolType = 0x0800
    HWProLen = 6
    ProLen = 4
    OP = ARP_OP_REQUEST
    SenderMAC = 0
    SenderIP = 0
    DestinationMAC = b'\x00\x00\x00\x00\x00\x00'
    DestinationIP = b'\xFF\xFF\xFF\xFF\xFF\xFF'

    
    def __init__(self, *args, **kwargs):
        '''
            Construct an ARP Packet from raw bytes or specified fields.
        '''
        if len(args) == 1:
            self.Unpack(args[0])
        elif len(args) > 1:
            raise ValueError('Too many raw data to unpack.')

        for ident, _, _ in ARPETHFrame.FIELD_LIST:
            val = kwargs.get(ident, None)
            if val is None:
                continue
            setattr(self, ident, val)


    def _normalize_fields(self):
        '''
            Normalize all fields to pack.
        '''
        for ident, ident_types, normalizer in ARPETHFrame.FIELD_LIST:
            val = getattr(self, ident, None)
            if ident_types.__class__ is not tuple:
                ident_types = (ident_types,) 

            if val is None:
                setattr(self, ident, getattr(ARPETHFrame, ident))
            elif val.__class__ not in ident_types:
                raise ValueError('Field %s has unaccptable type: %s' % (ident, val.__class__.__name__))
            if normalizer is not None:
                setattr(self, ident, normalizer(val))
            

    def Pack(self):
        '''
            Pack.
        '''
        self._normalize_fields()
        return ARPETHFrame.ARP_FRAME_STRUCT.pack(self.HWDst, self.HWSrc
            , self.FrameType, self.HWType, self.ProtocolType
            , self.HWProLen, self.ProLen, self.OP
            , self.SenderMAC, self.SenderIP, self.DestinationMAC
            , self.DestinationIP)


    def Unpack(self, raw):
        '''
            Unpack
        '''
        self.HWDst, self.HWSrc, self.FrameType \
        , self.HWType, self.ProtocolType, self.HWProLen\
        , self.ProLen, self.OP, self.SenderMAC \
        , self.SenderIP, self.DestinationMAC \
        , self.DestinationIP = ARPETHFrame.ARP_FRAME_STRUCT.unpack(raw)


def ARPRequest(_interface, _ip, _timeout = 10000):
    '''
        Make an ARP request to resolve MAC of target IP.

        :params:
            _interface      Name of the network interface to bind.
            _ip             Target IP
            _timeout        Timeout in milliseconds. 
                            Raise socket.timeout if there is no reply for _timeout milliseconds.
        :return:
            MAC address string
            Or a zero-length string.
    '''

    iface_addrs = netifaces.ifaddresses(_interface)
    
    if len(iface_addrs[netifaces.AF_INET]) < 1:
        ip = '255.255.255.255'
    else :
        ip = iface_addrs[netifaces.AF_INET][0]['addr']
    if len(iface_addrs[netifaces.AF_LINK]) < 1:
        raise RuntimeError('Interface %s doesn\'t have MAC.' % _interface)
    mac = iface_addrs[netifaces.AF_LINK][0]['addr']
    norm_mac = mac_normalizer(mac)
    norm_ip = IPv4ToInt(_ip)

    frame = ARPETHFrame(HWSrc = mac, OP = ARP_OP_REQUEST
                    , SenderMAC = mac, SenderIP = ip
                    , DestinationMAC = '00:00:00:00:00:00'
                    , DestinationIP = _ip)
    
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ARP))
    sock.bind((_interface, 0))
    sock.send(frame.Pack())

    this_time = datetime.now()
    end_time = this_time + timedelta(microseconds = _timeout * 1000)
    found_resp = None
    try:
        while end_time > this_time:
            delta_time = end_time - this_time
            sock.settimeout(delta_time.total_seconds())
            arp_raw = sock.recv(ARPETHFrame.ARP_FRAME_STRUCT.size)
            arp_resp = ARPETHFrame(arp_raw)
            if arp_resp.DestinationMAC == norm_mac and arp_resp.SenderIP == norm_ip:
                found_resp = arp_resp
                break
            this_time = datetime.now()
    except socket.timeout as e:
        pass

    if found_resp is None:
        raise socket.timeout()
        return ''
    return ':'.join(['%02x' % part for part in unpack('BBBBBB', arp_resp.SenderMAC)])
