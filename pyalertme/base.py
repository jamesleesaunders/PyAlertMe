import logging
from pyalertme import *
import struct
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
        self._logger = logging.getLogger('pyalertme')

        self._xbee = None
        self._serial = None
        self._callback = callback if callback else self._callback
        self._updates_thread = threading.Thread(target=self._updates)

        # Type Info
        self.manu = None
        self.type = None
        self.date = None
        self.version = None

        # My addresses
        self.addr_short = None
        self.addr_long = None
        self._addr_long_list = [b'', b'']

        self.associated = False
        self.started = False

    def _callback(self, type, node_id, field, value):
        if type == 'Attribute':
            print("Attribute Update [Node ID: " + node_id + "\tField: " + field + "\tValue: " + str(value) + "]")
        elif type == 'Property':
            print("Property Update [Node ID: " + node_id + "\tField: " + field + "\tValue: " + str(value) + "]")

    def _updates(self):
        """
        Continual Updates Thread

        """
        while self.started:
            time.sleep(0.00)

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
            self.started = True
            self._updates_thread.start()

    def halt(self):
        """
        Halt Device
        Close XBee and Serial

        :return:
        """
        self.started = False # This should kill the updates thread
        self._updates_thread.join() # Wait for updates thread to finish
        self._xbee.halt()
        self._serial.close()

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
                self.addr_long = b''.join(self._addr_long_list)

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

    def __str__(self):
        """
        Object to String

        :return: String
        """
        return "Device Type: %s" % (self.type)

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
        return ret1

    messages = {
        'routing_table_request': {
            'description': 'Management Routing Table Request',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x00',
            'cluster': b'\x00\x32',
            'profile': ZDP_PROFILE_ID,
            'data': '\x12\x01'
        },
        'permit_join_request': {
            'description': 'Management Permit Join Request',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x00',
            'cluster': b'\x00\x36',
            'profile': ZDP_PROFILE_ID,
            'data': '\xff\x00'
        },
        'active_endpoint_request': {
            'description': 'Active Endpoint Request',  # Device
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x00',
            'cluster': b'\x00\x05',
            'profile': ZDP_PROFILE_ID,
            'data': b'\x00\x00'
        },
        'match_descriptor_response': {
            'description': 'Match Descriptor Response', # Hub
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x00',
            'cluster': b'\x80\x06',
            'profile': ZDP_PROFILE_ID,
            'data': b'\x00\x00\x00\x00\x01\x02'
        },
        'version_info': {
            'description': 'Version Request',  # Device
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xf6',
            'profile': ALERTME_PROFILE_ID,
            'data': b'\x11\x00\xfc'
        },
        'plug_off': {
            'description': 'Switch Plug Off',  # SmartPlug
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xee',
            'profile': ALERTME_PROFILE_ID,
            'data': b'\x11\x00\x02\x00\x01'
        },
        'plug_on': {
            'description': 'Switch Plug On',  # SmartPlug
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xee',
            'profile': ALERTME_PROFILE_ID,
            'data': b'\x11\x00\x02\x01\x01'
        },
        'switch_status': {
            'description': 'Switch Status',  # SmartPlug
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xee',
            'profile': ALERTME_PROFILE_ID,
            'data': b'\x11\x00\x01\x01'
        },
        'normal_mode': {
            'description': 'Normal Mode',  # SmartPlug
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xf0',
            'profile': ALERTME_PROFILE_ID,
            'data': b'\x11\x00\xfa\x00\x01'
        },
        'range_test': {
            'description': 'Range Test',  # Device
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xf0',
            'profile': ALERTME_PROFILE_ID,
            'data': b'\x11\x00\xfa\x01\x01'
        },
        'locked_mode': {
            'description': 'Locked Mode',   # SmartPlug
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xf0',
            'profile': ALERTME_PROFILE_ID,
            'data': b'\x11\x00\xfa\x02\x01'
        },
        'silent_mode': {
            'description': 'Silent Mode',   # SmartPlug
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xf0',
            'profile': ALERTME_PROFILE_ID,
            'data': b'\x11\x00\xfa\x03\x01'
        },
        'security_initialization': {
            'description': 'Security Initialization',  # Sensor
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x05\x00',
            'profile': ALERTME_PROFILE_ID,
            'data': b'\x11\x80\x00\x00\x05'
        }
    }

    def list_actions(self):
        """
        List Actions

        :return:
        """
        actions = {}
        for id, message in self.messages.items():
            actions[id] = message['description']
        return actions

    def get_action(self, type):
        """
        Get the message from the dictionary

        :param type:
        :return:
        """
        return self.messages[type]
