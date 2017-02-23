import pprint
import logging
from classes import *
import struct
import time
import binascii
import threading
import serial
from xbee import ZigBee

pp = pprint.PrettyPrinter(indent=4)
logger = logging.getLogger('pihive')

class Base(object):
    # ZigBee Profile IDs
    ZDP_PROFILE_ID     = b'\x00\x00'  # Zigbee Device Profile
    HA_PROFILE_ID      = b'\x01\x04'  # HA Device Profile
    LL_PROFILE_ID      = b'\xc0\x5e'  # Light Link Profile
    ALERTME_PROFILE_ID = b'\xc2\x16'  # AlertMe Private Profile

    # ZigBee Addressing
    BROADCAST_LONG  = b'\x00\x00\x00\x00\x00\x00\xff\xff'
    BROADCAST_SHORT = b'\xff\xfe'

    messages = {
        'routing_table_request': {
            'description'   : 'Management Rtg (Routing Table) Request',
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x00',
            'cluster'       : b'\x00\x32',
            'profile'       : ZDP_PROFILE_ID,
            'data'          : '\x12\x01'
        },
        'permit_join_request': {
            'description'   : 'Management Permit Join Request',
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x00',
            'cluster'       : b'\x00\x36',
            'profile'       : ZDP_PROFILE_ID,
            'data'          : '\xff\x00'
        },
        'match_descriptor_response': {
            'description'   : 'Match Descriptor Response',
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x00',
            'cluster'       : b'\x80\x06',
            'profile'       : ZDP_PROFILE_ID,
            'data'          : b'\x00\x00\x00\x00\x01\x02'
            #'data'          : '\x03\xfd\xff\x16\xc2\x00\x01\xf0\x00' // SmartPlug
        },
        'active_endpoints_request': {
            'description'   : 'Active Endpoints Request',  #Device
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x00',
            'cluster'       : b'\x00\x05',
            'profile'       : ZDP_PROFILE_ID,
            'data'          : b'\x00\x00'
        },
        'hardware_join_1' : {
            'description'   : 'Hardware Join Messages 1',  #Device
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xf6',
            'profile'       : ALERTME_PROFILE_ID, 
            'data'          : b'\x11\x01\xfc'
        },
        'hardware_join_2' : {
            'description'   : 'Hardware Join Messages 2',  #Device (also note Version req)
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xf0',
            'profile'       : ALERTME_PROFILE_ID, 
            'data'          : b'\x19\x01\xfa\x00\x01'
        },
        'version_info' : {
            'description'   : 'Version Request',   #Device
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02', 
            'cluster'       : b'\x00\xf6', 
            'profile'       : ALERTME_PROFILE_ID, 
            'data'          : b'\x11\x00\xfc\x00\x01'
        },
        'plug_off': {
            'description'   : 'Switch Plug Off',  #SmartPlug
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xee',
            'profile'       : ALERTME_PROFILE_ID,
            'data'          : b'\x11\x00\x02\x00\x01'
        },
        'plug_on': {
            'description'   : 'Switch Plug On',  #SmartPlug
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xee',
            'profile'       : ALERTME_PROFILE_ID,
            'data'          : b'\x11\x00\x02\x01\x01'
        },
        'switch_status': {
            'description'   : 'Switch Status',  #SmartPlug
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xee',
            'profile'       : ALERTME_PROFILE_ID,
            'data'          : b'\x11\x00\x01\x01'
        },
        'normal_mode': {
            'description'   : 'Normal Mode',  #SmartPlug
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xf0',
            'profile'       : ALERTME_PROFILE_ID,
            'data'          : b'\x11\x00\xfa\x00\x01'
        },
        'range_test': {
            'description'   : 'Range Test',  # Device
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xf0',
            'profile'       : ALERTME_PROFILE_ID,
            'data'          : b'\x11\x00\xfa\x01\x01'
        },
        'locked_mode': {
            'description'   : 'Locked Mode',   #SmartPlug
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xf0',
            'profile'       : ALERTME_PROFILE_ID,
            'data'          : b'\x11\x00\xfa\x02\x01'
        },
        'silent_mode': {
            'description'   : 'Silent Mode',   #SmartPlug
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xf0',
            'profile'       : ALERTME_PROFILE_ID,
            'data'          : b'\x11\x00\xfa\x03\x01'
        },
        'security_initialization': {
           'description'    : 'Security Initialization',   #Sensor
           'src_endpoint'   : b'\x00',
           'dest_endpoint'  : b'\x02',
           'cluster'        : b'\x05\x00',
           'profile'        : ALERTME_PROFILE_ID,
           'data'           : b'\x11\x80\x00\x00\x05'
        }
    }

    def __init__(self, serialObj = False):
        self.logger = logger or logging.getLogger(__name__)

        # Setup serial and xbee
        if(serialObj != False):
            self.zb = ZigBee(ser=serialObj, callback=self.receive_message, error_callback=self.xbee_error)

        # Type Info
        self.manu = None
        self.type = None
        self.date = None
        self.version = None

        # Received and Sent Messages
        self.outgoing_messages = []
        self.incoming_messages = []

        self.associated = False

    def list_actions(self):
        actions = {}
        for id, message in self.messages.items():
            actions[id] = message['description']
        return actions

    def get_action(self, type):
        # Get the message from the dictionary
        return self.messages[type]

    def send_message(self, message, dest_addr_long, dest_addr_short):
        self.logger.debug('sending message..')
        # Tack on destination addresses
        message['dest_addr_long']  = dest_addr_long
        message['dest_addr_short'] = dest_addr_short
        device_id = Base.pretty_mac(dest_addr_long)

        self.logger.debug('Device: %s Sending: %s', device_id, message)
        self.zb.send('tx_explicit', **message)

    def receive_message(self, message):
        # Grab source address, work out device ID
        source_addr_long = message['source_addr_long']
        device_id = Base.pretty_mac(source_addr_long)

        self.logger.debug('Device: %s Received: %s', device_id, message)
        self.process_message(message)
       
    def process_message(self, message):
        # We are only interested in Zigbee Explicit packets.
        if (message['id'] == 'rx_explicit'):
            profile_id = message['profile']
            cluster_id = message['cluster']

            if (profile_id == self.ZDP_PROFILE_ID):
                # Zigbee Device Profile ID
                self.logger.debug('Zigbee Device Profile Packet Receieved')

            elif (profile_id == self.ALERTME_PROFILE_ID):
                # AlertMe Profile ID
                self.logger.debug('AlertMe Specific Profile Packet Received')

            elif (profile_id == self.HA_PROFILE_ID):
                # HA Profile ID
                self.logger.debug('HA Profile Packet Received')

            else:
                self.logger.error('Unrecognised Profile ID: %e', profile_id)

    def halt(self):
        self.zb.halt()

    def xbee_error(self, error):
        self.logger.critical('XBee Error: %s', error)

    def __str__(self):
        return "Device Type: %s" % (self.type)

    @staticmethod
    def pretty_mac(macString):
        # TODO: This may be a little over complicated at the moment,
        # I was struggling to get this to work for both Python2 and Python3.
        # I am sure this could be simplified... but for now - this works!
        str1 = str(binascii.b2a_hex(macString).decode())
        arr1 = [str1[i:i+2] for i in range(0, len(str1), 2)]
        ret1 = ':'.join(b for b in arr1)
        return ret1
