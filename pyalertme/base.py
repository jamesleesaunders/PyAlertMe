import logging
from pyalertme import *
import struct
import copy
import time
import binascii
import threading
from xbee import ZigBee

class Base(object):

    # ZigBee Profile IDs
    ZDP_PROFILE_ID     = b'\x00\x00'  # Zigbee Device Profile
    HA_PROFILE_ID      = b'\x01\x04'  # HA Device Profile
    LL_PROFILE_ID      = b'\xc0\x5e'  # Light Link Profile
    ALERTME_PROFILE_ID = b'\xc2\x16'  # AlertMe Private Profile

    # ZigBee Addressing
    BROADCAST_LONG  = b'\x00\x00\x00\x00\x00\x00\xff\xff'
    BROADCAST_SHORT = b'\xff\xfe'



    def __init__(self, callback=None):
        """
        Base Constructor

        :param callback: Optional
        """
        # Resources
        self._logger = logging.getLogger('pyalertme')
        self._xbee = None
        self._serial = None

        # Type Info
        self.manu = None
        self.type = None
        self.date = None
        self.version = None

        # Scheduler Thread
        self._schedule_thread = threading.Thread(target=self._schedule_loop)
        self._schedule_interval = 2
        self._callback = callback if callback else self._callback

        # My addresses
        self._addr_long_list = [b'', b'']
        self.addr_long = None
        self.addr_short = None

        # Status Flags
        self.associated = False
        self.started = False

    def start(self, serial):
        """
        Start Device
        Initiate Serial and XBee

        :param serial: Serial Object
        :return:
        """
        if serial:
            self._serial = serial
            self._xbee = ZigBee(ser=self._serial, callback=self.receive_message, error_callback=self.xbee_error, escaped=True)
            self.read_addresses()
            self._started = True
            self._schedule_thread.start()

    def halt(self):
        """
        Halt Device
        Close XBee and Serial

        :return:
        """
        self._started = False         # This should kill the updates thread
        self._schedule_thread.join()  # Wait for updates thread to finish
        self._xbee.halt()
        self._serial.close()

    def _callback(self, type, node_id, field, value):
        if type == 'Attribute':
            print("Attribute Update [Node ID: " + node_id + "\tField: " + field + "\tValue: " + str(value) + "]")
        elif type == 'Property':
            print("Property Update [Node ID: " + node_id + "\tField: " + field + "\tValue: " + str(value) + "]")

    def _schedule_loop(self):
        """
        Continual Updates Thread calls the _updates() function every at intervals set in self._schedule_interval.

        """
        while self._started:
            if self.associated:
                self._schedule_event()

                # The following for loop is being used in place of a simple
                # time.sleep(self._schedule_interval)
                # This is done so we can interrupt the thread quicker.
                for i in range(self._schedule_interval * 10):
                    if self._started:
                        time.sleep(0.1)

    def _schedule_event(self):
        """
        The _schedule_event() function is called by the _schedule_loop() thread function called at regular intervals.

        """
        self._logger.debug('Continual Update')

    def get_node_id(self):
        return self.pretty_mac(self.addr_long)

    def xbee_error(self, error):
        """
        On XBee error this function is called

        :param error:
        :return:
        """
        self._logger.critical('XBee Error: %s', error)

    def read_addresses(self):
        """
        Work out own address

        """
        self._logger.debug('Requesting own addresses')
        self._xbee.send('at', command='MY')
        time.sleep(0.05)
        self._xbee.send('at', command='SH')
        time.sleep(0.05)
        self._xbee.send('at', command='SL')
        time.sleep(0.05)

    def send_message(self, message, dest_addr_long, dest_addr_short):
        """
        Send message to XBee

        :param message: Dict message
        :param dest_addr_long: 48-bits Long Address
        :param dest_addr_short: 16-bit Short Address
        :return:
        """
        # Tack on destination addresses
        message['dest_addr_long']  = dest_addr_long
        message['dest_addr'] = dest_addr_short

        self._logger.debug('Sending Message: %s', message)
        self._xbee.send('tx_explicit', **message)

    def receive_message(self, message):
        """
        Receive message from XBee
        Calls process message

        :param message: Dict of message
        :return:
        """
        self._logger.debug('Received Message: %s', message)
        self.process_message(message)

    def set_addr_long(self, addr_long):
        """
        Set Long Address

        :param addr_long: Long Address
        :return:
        """
        self._logger.debug('Setting Long Address: %s', addr_long)
        self.addr_long = addr_long

    def process_message(self, message):
        """
        Process incoming message

        :param message: Dict of message
        :return:
        """
        # AT Packets
        if message['id'] == 'at_response':
            if message['command'] == 'MY':
                self.addr_short = message['parameter']
            if message['command'] == 'SH':
                self._addr_long_list[0] = message['parameter']
            if message['command'] == 'SL':
                self._addr_long_list[1] = message['parameter']
            # If we have worked out both the High and Low addresses then calculate the full addr_long
            if self._addr_long_list[0] and self._addr_long_list[1]:
                self.set_addr_long(b''.join(self._addr_long_list))

        # Zigbee Explicit Packets
        if message['id'] == 'rx_explicit':
            profile_id = message['profile']
            cluster_id = message['cluster']

            if profile_id == self.ZDP_PROFILE_ID:
                # Zigbee Device Profile ID
                self._logger.debug('Received Zigbee Device Profile Packet')

            elif profile_id == self.ALERTME_PROFILE_ID:
                # AlertMe Profile ID
                self._logger.debug('Received AlertMe Specific Profile Packet')

            elif profile_id == self.HA_PROFILE_ID:
                # HA Profile ID
                self._logger.debug('Received HA Profile Packet')

            else:
                self._logger.error('Unrecognised Profile ID: %r', profile_id)

    @staticmethod
    def pretty_mac(address_long):
        """
        Convert long address to pretty mac address string
        TODO: This may be a little over complicated at the moment,
        I was struggling to get this to work for both Python2 and Python3.
        I am sure this could be simplified... but for now - this works!

        :param address_long:
        :return:
        """
        str1 = str(binascii.b2a_hex(address_long).decode())
        arr1 = [str1[i:i+2] for i in range(0, len(str1), 2)]
        ret1 = ':'.join(b for b in arr1)
        
        # MAC Address Manufacturers
        # 00:0d:6f:00:03:bb:b9:f8 = Ember Corporation
        # 00:13:a2:00:40:a2:3b:09 = MaxStream, Inc
        # 00:1E:5E:09:02:14:C5:AB = Computime Ltd.
                            
        return ret1

    messages = {
        'routing_table_request': {
            'name': 'Management Routing Table Request',
            'frame': {
                'src_endpoint': b'\x00',
                'dest_endpoint': b'\x00',
                'cluster': b'\x00\x32',
                'profile': ZDP_PROFILE_ID,
                'data': '\x12\x01'
            }
        },
        'permit_join_request': {
            'name': 'Management Permit Join Request',
            'frame': {
                'src_endpoint': b'\x00',
                'dest_endpoint': b'\x00',
                'cluster': b'\x00\x36',
                'profile': ZDP_PROFILE_ID,
                'data': '\xff\x00'
            }
        },
        'active_endpoint_request': {
            'name': 'Active Endpoints Request',
            'frame': {
                'src_endpoint': b'\x00',
                'dest_endpoint': b'\x00',
                'cluster': b'\x00\x05',
                'profile': ZDP_PROFILE_ID,
                'data': b'\x00\x00'
            }
        },
        'match_descriptor_response': {
            'name': 'Match Descriptor Response',
            'frame': {
                'src_endpoint': b'\x00',
                'dest_endpoint': b'\x00',
                'cluster': b'\x80\x06',
                'profile': ZDP_PROFILE_ID,
                'data': b'\x00\x00\x00\x00\x01\x02'
            }
        },
        'version_info': {
            'name': 'Version Request',
            'frame': {
                'src_endpoint': b'\x00',
                'dest_endpoint': b'\x02',
                'cluster': b'\x00\xf6',
                'profile': ALERTME_PROFILE_ID,
                'data': b'\x11\x00\xfc'
            }
        },
        'plug': {
            'name': 'Plug State Change',
            'frame': {
                'src_endpoint': b'\x00',
                'dest_endpoint': b'\x02',
                'cluster': b'\x00\xee',
                'profile': ALERTME_PROFILE_ID,
                'data': lambda self, params: self.generate_relay_state(params)
            }
        },
        'plug_off': {
            'name': 'Switch Plug Off',
            'frame': {
                'src_endpoint': b'\x00',
                'dest_endpoint': b'\x02',
                'cluster': b'\x00\xee',
                'profile': ALERTME_PROFILE_ID,
                'data': b'\x11\x00\x02\x00\x01'
            }
        },
        'plug_on': {
            'name': 'Switch Plug On',
            'frame': {
                'src_endpoint': b'\x00',
                'dest_endpoint': b'\x02',
                'cluster': b'\x00\xee',
                'profile': ALERTME_PROFILE_ID,
                'data': b'\x11\x00\x02\x01\x01'
            }
        },
        'switch_status': {
            'name': 'Switch Status',
            'frame': {
                'src_endpoint': b'\x00',
                'dest_endpoint': b'\x02',
                'cluster': b'\x00\xee',
                'profile': ALERTME_PROFILE_ID,
                'data': b'\x11\x00\x01\x01'
            }
        },
        'normal_mode': {
            'name': 'Normal Mode',
            'frame': {
                'src_endpoint': b'\x00',
                'dest_endpoint': b'\x02',
                'cluster': b'\x00\xf0',
                'profile': ALERTME_PROFILE_ID,
                'data': b'\x11\x00\xfa\x00\x01'
            }
        },
        'range_test': {
            'name': 'Range Test',
            'frame': {
                'src_endpoint': b'\x00',
                'dest_endpoint': b'\x02',
                'cluster': b'\x00\xf0',
                'profile': ALERTME_PROFILE_ID,
                'data': b'\x11\x00\xfa\x01\x01'
            }
        },
        'locked_mode': {
            'name': 'Locked Mode',
            'frame': {
                'src_endpoint': b'\x00',
                'dest_endpoint': b'\x02',
                'cluster': b'\x00\xf0',
                'profile': ALERTME_PROFILE_ID,
                'data': b'\x11\x00\xfa\x02\x01'
            }
        },
        'silent_mode': {
            'name': 'Silent Mode',
            'frame': {
                'src_endpoint': b'\x00',
                'dest_endpoint': b'\x02',
                'cluster': b'\x00\xf0',
                'profile': ALERTME_PROFILE_ID,
                'data': b'\x11\x00\xfa\x03\x01'
            }
        },
        'security_initialization': {
            'name': 'Security Initialization',
            'frame': {
                'src_endpoint': b'\x00',
                'dest_endpoint': b'\x02',
                'cluster': b'\x05\x00',
                'profile': ALERTME_PROFILE_ID,
                'data': b'\x11\x80\x00\x00\x05'
            }
        }
    }

    @staticmethod
    def generate_relay_state(params):
        checksum = b'\th'
        cluster_cmd = b'\x80'
        payload = b'\x07\x01' if params['State'] else b'\x06\x00'
        data = checksum + cluster_cmd + payload
        return data

    def list_messages(self):
        """
        List messages

        :return:
        """
        actions = {}
        for id, message in self.messages.items():
            actions[id] = message['name']
        return actions

    def get_message(self, message_id, params):
        """
        Get message

        :param message_id:
        :param param:
        :return:
        """
        # Make a copy of the message
        message = copy.deepcopy(self.messages[message_id])
        data = message['frame']['data']

        # If data is a lambda then call it and replace with return value
        if callable(data):
            message['frame']['data'] = data(self, params)

        # Return processed message
        return message['frame']
