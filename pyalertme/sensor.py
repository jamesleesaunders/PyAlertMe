import logging
from pyalertme import *
from pyalertme.messages import *
import struct
import time
import binascii
import threading

class Sensor(Device):

    def __init__(self, callback=None):
        """
        Sensor Constructor

        """
        Device.__init__(self, callback)

        # Type Info
        self.type = 'Button Device'
        self.version = 12345
        self.manu = 'PyAlertMe'
        self.manu_date = '2017-01-01'

        # Relay State
        self.tamper = 0
        self.triggered = 0

    def process_message(self, message):
        """
        Process incoming message

        :param message: Dict of message
        :return:
        """
        super(Sensor, self).process_message(message)

        # Zigbee Explicit Packets
        if message['id'] == 'rx_explicit':
            profile_id = message['profile']
            cluster_id = message['cluster']

            source_addr_long = message['source_addr_long']
            source_addr_short = message['source_addr']

            if profile_id == PROFILE_ID_ALERTME:
                # AlertMe Profile ID

                # Python 2 / 3 hack
                if hasattr(bytes(), 'encode'):
                    cluster_cmd = message['rf_data'][2]
                else:
                    cluster_cmd = bytes([message['rf_data'][2]])

                if cluster_id == CLUSTER_ID_SECURITY:
                    # Security Initialization
                    self._logger.info('Received Security Initialization')

                else:
                    self._logger.error('Unrecognised Cluster ID: %r', cluster_id)

            else:
                self._logger.error('Unrecognised Profile ID: %r', profile_id)









    def generate_button_press_update(self):
        """
        Button Press Update
            To Finish...

        :return: Message
        """
        params = {
            'State': 1,
            'Counter': 62552
        }
        # At the moment this just generates a hard coded message.
        # Also see parse_button_press().
        message = {
            'profile': '\xc2\x16',
            'cluster': '\x00\xf3',
            'source_endpoint': '\x02',
            'dest_endpoint': '\x02',
            'data': '\t\x00\x01\x00\x01X\xf4\x00\x00'
        }
        return message