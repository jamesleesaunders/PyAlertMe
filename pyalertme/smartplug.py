import logging
from pyalertme import *
import struct
import time
import binascii
import threading


class SmartPlug(Device):

    def __init__(self, callback=None):
        """
        SmartPlug Constructor

        """
        Device.__init__(self, callback)

        # Type Info
        self.manu = 'PyAlertMe'
        self.type = 'SmartPlug'
        self.date = '2013-09-26'
        self.version = 20045

        # Relay State
        self.state = 0

    def process_message(self, message):
        """
        Process incoming message

        :param message: Dict of message
        :return:
        """
        super(SmartPlug, self).process_message(message)

        # Zigbee Explicit Packets
        if (message['id'] == 'rx_explicit'):
            profile_id = message['profile']
            cluster_id = message['cluster']

            if (profile_id == self.ALERTME_PROFILE_ID):
                # AlertMe Profile ID

                # Python 2 / 3 hack
                if (hasattr(bytes(), 'encode')):
                    cluster_cmd = message['rf_data'][2]
                else:
                    cluster_cmd = bytes([message['rf_data'][2]])

                if (cluster_id == b'\x00\xee'):
                    if (cluster_cmd == b'\01'):
                        # State Request
                        # b'\x11\x00\x01\x01'
                        self._logger.debug('Switch State is: %s', self.state)
                        self.send_message(self.generate_switch_state_update(), self.hub_addr_long, self.hub_addr_short)

                    elif (cluster_cmd == b'\02'):
                        # Change State
                        # b'\x11\x00\x02\x01\x01' On
                        # b'\x11\x00\x02\x00\x01' Off
                        self.state = self.parse_switch_state_request(message['rf_data'])
                        self._logger.debug('Switch State Changed to: %s', self.state)
                        self.send_message(self.generate_switch_state_update(), self.hub_addr_long, self.hub_addr_short)
                        self._callback(self.get_node_id(), 'State', 'ON')

                    elif (cluster_cmd == b'\xfa'):
                        # Set Mode
                        if(message['rf_data'][4] == b'\x00\x01'):
                            # Normal
                            # b'\x11\x00\xfa\x00\x01'
                            self._logger.debug('Normal Mode')

                        elif(message['rf_data'][4] == b'\x00\x01'):
                            # Locked
                            # b'\x11\x00\xfa\x02\x01'
                            self._logger.debug('Locked Mode')

                        elif(message['rf_data'][4] == b'\x03\x01'):
                            # Silent
                            # b'\x11\x00\xfa\x03\x01'
                            self._logger.debug('Silent Mode')

                    else:
                        self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                else:
                    self._logger.error('Unrecognised Cluster ID: %r', cluster_id)

            else:
                self._logger.error('Unrecognised Profile ID: %r', profile_id)

    def set_state(self, state):
        """
        This simulates the physical button being pressed

        :param state:
        :return:
        """
        self.state = state
        self._logger.debug('Switch State Changed to: %s', self.state)
        self.send_message(self.generate_switch_state_update(), self.hub_addr_long, self.hub_addr_short)

    def generate_switch_state_update(self):
        """
        Generate State Message

        :return: Message of switch state
        """
        checksum = b'\th'
        cluster_cmd = b'\x80'
        payload = b'\x06\x00' if self.state else b'\x07\x01'
        data = checksum + cluster_cmd + payload

        message = {
            'description':   'Switch State Update',
            'src_endpoint':  b'\x00',
            'dest_endpoint': b'\x02',
            'cluster':       b'\x00\xee',
            'profile':       self.ALERTME_PROFILE_ID,
            'data':          data,
        }
        return(message)

    @staticmethod
    def parse_switch_state_request(rf_data):
        """
        Process message, parse for state change request

        :param rf_data:
        :return: Bool 1 = On, 0 = Off
        """
        # Parse Switch State Request
        if (rf_data == b'\x11\x00\x02\x01\x01'):
            return 1
        elif (rf_data == b'\x11\x00\x02\x00\x01'):
            return 0
        else:
            logging.error('Unknown State Request')
