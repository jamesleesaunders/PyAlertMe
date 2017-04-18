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
        self.date = '2017-01-01'
        self.version = 12345

        # Relay State and Power Values
        self.state = False
        self.power_demand = 0
        self.power_consumption = 0

    def _updates(self):
        """
        Continual Updates

        """
        while self.started:
            if self.associated:
                self.send_message(self.generate_power_demand_update(), self.hub_addr_long, self.hub_addr_short)
            time.sleep(2.00)

    def process_message(self, message):
        """
        Process incoming message

        :param message: Dict of message
        :return:
        """
        super(SmartPlug, self).process_message(message)

        # Zigbee Explicit Packets
        if message['id'] == 'rx_explicit':
            profile_id = message['profile']
            cluster_id = message['cluster']
            source_addr_long = message['source_addr_long']
            source_addr_short = message['source_addr']

            if profile_id == self.ALERTME_PROFILE_ID:
                # AlertMe Profile ID

                # Python 2 / 3 hack
                if hasattr(bytes(), 'encode'):
                    cluster_cmd = message['rf_data'][2]
                else:
                    cluster_cmd = bytes([message['rf_data'][2]])

                if cluster_id == b'\x00\xee':
                    if cluster_cmd == b'\01':
                        # State Request
                        # b'\x11\x00\x01\x01'
                        self._logger.debug('Switch State is: %s', self.state)
                        self.send_message(self.generate_switch_state_update(), source_addr_long, source_addr_short)

                    elif cluster_cmd == b'\02':
                        # Change State
                        # b'\x11\x00\x02\x01\x01' On
                        # b'\x11\x00\x02\x00\x01' Off
                        state = self.parse_switch_state_request(message['rf_data'])
                        self.set_state(state)
                        self._logger.debug('Switch State Changed to: %s', self.state)
                        self.send_message(self.generate_switch_state_update(), source_addr_long, source_addr_short)
                        self._callback('Attribute', self.get_node_id(), 'State', 'ON')

                    else:
                        self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                # else:
                    # self._logger.error('Unrecognised Cluster ID: %r', cluster_id)

            # else:
                # self._logger.error('Unrecognised Profile ID: %r', profile_id)

    def set_state(self, state):
        """
        This simulates the physical button being pressed

        :param state:
        :return:
        """
        self.state = state
        self._logger.debug('Switch State Changed to: %s', self.state)
        if self.associated:
            self.send_message(self.generate_switch_state_update(), self.hub_addr_long, self.hub_addr_short)

        # Temporary code while testing power code...
        # Randomly set the power usage value.
        from random import randint
        self.set_power_demand(randint(0, 100))

    def set_power_demand(self, power_demand):
        """
        Set Power Demand

        :param state:
        :return:
        """
        self.power_demand = power_demand
        self._logger.debug('Power Demand Changed to: %s', self.power_demand)

    def generate_switch_state_update(self):
        """
        Generate State Message

        :return: Message of switch state
        """
        checksum = b'\th'
        cluster_cmd = b'\x80'
        payload = b'\x07\x01' if self.state else b'\x06\x00'
        data = checksum + cluster_cmd + payload

        message = {
            'description': 'Switch State Update',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xee',
            'profile': self.ALERTME_PROFILE_ID,
            'data': data
        }
        return(message)

    def generate_power_demand_update(self):
        """
        Generate Power Demand Update

        :return: Message
        """
        checksum = b'\tj'
        cluster_cmd = b'\x81'
        payload = struct.pack('H', self.power_demand)
        data = checksum + cluster_cmd + payload

        message = {
            'description': 'Current Power Demand',
            'profile': self.ALERTME_PROFILE_ID,
            'cluster': b'\x00\xef',
            'src_endpoint': b'\x02',
            'dest_endpoint': b'\x02',
            'data': data
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
        if rf_data == b'\x11\x00\x02\x01\x01':
            return True
        elif rf_data == b'\x11\x00\x02\x00\x01':
            return False
        else:
            logging.error('Unknown State Request')