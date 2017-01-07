import pprint
import logging
from classes import *
import struct
import time
import binascii

pp = pprint.PrettyPrinter(indent=4)

class Sensor(Device):

    def __init__(self, serialObj):
        Device.__init__(self, serialObj)

        # Type Info
        self.manu = 'AlertMe.com'
        self.type = 'Button Device'
        self.date = '2010-11-15'
        self.version = 59435

        # Relay State
        self.tamper = 0
        self.triggered = 0

    def process_message(self, message):
        super(Sensor, self).process_message(message)

        # We are only interested in Zigbee Explicit packets.
        if (message['id'] == 'rx_explicit'):
            profile_id = message['profile']
            cluster_id = message['cluster']

            source_addr_long = message['source_addr_long']
            source_addr = message['source_addr']

            if (profile_id == self.ALERTME_PROFILE_ID):
                # AlertMe Profile ID

                # Python 2 / 3 hack
                if (hasattr(bytes(), 'encode')):
                    cluster_cmd = message['rf_data'][2]
                else:
                    cluster_cmd = bytes([message['rf_data'][2]])

                if (cluster_id == b'\x05\x00'):
                    # Security Initialization
                    self.logger.info('Security Initialization')

                else:
                    self.logger.error('Unrecognised Cluster ID: %r', cluster_id)

            else:
                self.logger.error('Unrecognised Profile ID: %r', profile_id)
