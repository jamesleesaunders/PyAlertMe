import logging
from pyalertme import *
from pyalertme.messages import *
import struct
import time
import binascii
import threading


class Device(Base):

    def __init__(self, callback=None):
        """
        Device Constructor

        """
        Base.__init__(self, callback)

        # Type Info
        self.type = 'Generic Device'
        self.version = 12345
        self.manu = 'PyAlertMe'
        self.manu_date = '2017-01-01'

        # Start off not associated
        self.associated = False

        # Addresses of the hub we are associated with
        self.hub_addr_long = None
        self.hub_addr_short = None

        # Attributes
        self.rssi = 197
        self.mode = 'NORMAL'

    def process_message(self, message):
        """
        Process incoming message

        :param message: Dict of message
        :return:
        """
        super(Device, self).process_message(message)

        # Zigbee Explicit Packets
        if message['id'] == 'rx_explicit':
            profile_id = message['profile']
            cluster_id = message['cluster']
            source_addr_long = message['source_addr_long']
            source_addr_short = message['source_addr']

            if not self.associated:
                self.send_message(self.generate_match_descriptor_request(), source_addr_long, source_addr_short)

            if profile_id == ZDP_PROFILE_ID:
                # Zigbee Device Profile ID
                if cluster_id == b'\x00\x32':
                    self._logger.debug('Received Management Routing Table Request')

                elif cluster_id == b'\x00\x05':
                    self._logger.debug('Received Active Endpoint Request')

                elif cluster_id == b'\x80\x06':
                    self._logger.debug('Received Match Descriptor Response')

            elif profile_id == ALERTME_PROFILE_ID:
                # AlertMe Profile ID

                # Python 2 / 3 hack
                if hasattr(bytes(), 'encode'):
                    cluster_cmd = message['rf_data'][2]
                else:
                    cluster_cmd = bytes([message['rf_data'][2]])

                if cluster_id == b'\x00\xf6':
                    # b'\x11\x00\xfc\x00\x01'
                    self._logger.debug('Received Version Request')
                    self.send_message(self.generate_version_info_update(), source_addr_long, source_addr_short)

                elif cluster_id == b'\x00\xf0':
                    if cluster_cmd == b'\xfa':
                        self._logger.debug('Received Mode Change Request')
                        # Take note of hub address
                        self.hub_addr_long = source_addr_long
                        self.hub_addr_short = source_addr_short
                        # We are now fully associated
                        self.associated = True

                        modeCmd = message['rf_data'][3] + message['rf_data'][4]
                        if modeCmd == b'\x00\x01':
                            # Normal
                            # b'\x11\x00\xfa\x00\x01'
                            self._logger.debug('Normal Mode')
                            self.mode = 'NORMAL'

                        elif modeCmd == b'\x01\x01':
                            # Range Test
                            # b'\x11\x00\xfa\x01\x01'
                            self._logger.debug('Range Test Mode')
                            self.mode = 'RANGE'
                            # TODO Setup thread loop to send regular range RSSI updates - for now just send one...
                            self.send_message(self.generate_range_update(), source_addr_long, source_addr_short)

                        elif modeCmd == b'\x02\x01':
                            # Locked
                            # b'\x11\x00\xfa\x02\x01'
                            self._logger.debug('Locked Mode')
                            self.mode = 'LOCKED'

                        elif modeCmd == b'\x03\x01':
                            # Silent
                            # b'\x11\x00\xfa\x03\x01'
                            self._logger.debug('Silent Mode')
                            self.mode = 'SILENT'

            else:
                self._logger.error('Unrecognised Profile ID: %r', profile_id)

    def generate_version_info_update(self):
        """
        Generate type message

        :return: Message of device type
        """
        params = {
            'Type': self.type,
            'Version': self.version,
            'Manufacturer': self.manu,
            'ManufactureDate': self.manu_date
        }
        return get_message('version_info_update', params)

    def generate_range_update(self):
        """
        Generate range message

        :return: Message of range value
        """
        return get_message('range_info_update', {'RSSI': self.rssi})

    def generate_match_descriptor_request(self):
        """
        Generate Match Descriptor Request

        """
        return temp_generate_match_descriptor_request()

