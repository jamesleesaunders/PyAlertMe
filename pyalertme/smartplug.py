import logging
from pyalertme import *
import struct
import time
import binascii
import threading


class SmartPlug(Device):

    def __init__(self, serialObj = False):
        Device.__init__(self, serialObj)

        # Type Info
        self.manu = 'AlertMe.com'
        self.type = 'SmartPlug'
        self.date = '2013-09-26'
        self.version = 20045

        # Relay State
        self.state = 0

    def process_message(self, message):
        super(SmartPlug, self).process_message(message)

        # We are only interested in Zigbee Explicit packets.
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
                        self.logger.debug('Switch State is: %s', self.state)
                        self.send_message(self.get_state(), self.hub_addr_long, self.hub_addr)

                    elif (cluster_cmd == b'\02'):
                        # Change State
                        # b'\x11\x00\x02\x01\x01' On
                        # b'\x11\x00\x02\x00\x01' Off
                        self.state = self.parse_switch_state_change(message['rf_data'])
                        self.logger.debug('Switch State Changed to: %s', self.state)
                        self.send_message(self.get_state(), self.hub_addr_long, self.hub_addr)

                    elif (cluster_cmd == b'\xfa'):
                        # Set Mode
                        if(message['rf_data'][4] == b'\x00\x01'):
                            # Normal
                            # b'\x11\x00\xfa\x00\x01'
                            self.logger.debug('Normal Mode')

                        elif(message['rf_data'][4] == b'\x00\x01'):
                            # Locked
                            # b'\x11\x00\xfa\x02\x01'
                            self.logger.debug('Locked Mode')

                        elif(message['rf_data'][4] == b'\x03\x01'):
                            # Silent
                            # b'\x11\x00\xfa\x03\x01'
                            self.logger.debug('Silent Mode')

                    else:
                        self.logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                else:
                    self.logger.error('Unrecognised Cluster ID: %r', cluster_id)

            else:
                self.logger.error('Unrecognised Profile ID: %r', profile_id)

    def set_state(self, state):
        # This simulates the physical button being pressed
        self.state = state
        self.logger.debug('Switch State Changed to: %s', self.state)
        self.send_message(self.get_state(), self.hub_addr_long, self.hub_addr)


    def get_state(self):
        # cluster_cmd == b'\x80'
        if(self.state):
            data = b'\th\x80\x06\x00'
        else:
            data = b'\th\x80\x07\x01'
        message = {
            'description':   'Switch State',
            'src_endpoint':  b'\x00',
            'dest_endpoint': b'\x02',
            'cluster':       b'\x00\xee',
            'profile':       self.ALERTME_PROFILE_ID,
            'data':          data,
        }
        return(message)

    @staticmethod
    def parse_switch_state_change(rf_data):
        # Parse Switch State Request
        if (rf_data == b'\x11\x00\x02\x01\x01'):
            return 1
        elif (rf_data == b'\x11\x00\x02\x00\x01'):
            return 0
        else:
            logging.error('Unknown State Request')
