import logging
from pyalertme.zigbee import *
from pyalertme.base import Base
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

        # ZigBee Explicit Packets
        if message['id'] == 'rx_explicit':
            profile_id = message['profile']
            cluster_id = message['cluster']
            source_addr_long = message['source_addr_long']
            source_addr_short = message['source_addr']

            if not self.associated:
                self.send_message(self.generate_match_descriptor_request(), source_addr_long, source_addr_short)

            if profile_id == PROFILE_ID_ZDP:
                # ZigBee Device Profile ID
                if cluster_id == CLUSTER_ID_ZDO_MGMT_RTG_REQ:
                    self._logger.debug('Received Management Routing Table Request')

                elif cluster_id == CLUSTER_ID_ZDO_ACTIVE_EP_REQ:
                    self._logger.debug('Received Active Endpoint Request')

                elif cluster_id == CLUSTER_ID_ZDO_MATCH_DESC_RSP:
                    self._logger.debug('Received Match Descriptor Response')

            elif profile_id == PROFILE_ID_ALERTME:
                # AlertMe Profile ID
                cluster_cmd = message['rf_data'][2:3]

                if cluster_id == CLUSTER_ID_AM_DISCOVERY:
                    if cluster_cmd == CLUSTER_CMD_AM_VERSION_REQ:
                        # b'\x11\x00\xfc\x00\x01'
                        self._logger.debug('Received Version Request')
                        self.send_message(self.generate_version_info_update(), source_addr_long, source_addr_short)

                    else:
                        self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                elif cluster_id == CLUSTER_ID_AM_STATUS:
                    if cluster_cmd == CLUSTER_CMD_AM_MODE_REQ:
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
                        self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

            else:
                self._logger.error('Unrecognised Profile ID: %r', profile_id)

    def set_attribute(self, attribute, value):
        """
        Set Associated

        :param string: attribute
        :param mixed: value
        :return:
        """
        self._logger.debug('Setting attribute: %s to value: %s', attribute, value)
        setattr(self, attribute, value)


    def generate_version_info_update(self):
        """
        Generate type message

        :return: Message of device type
        """
        params = {
            'type': self.type,
            'version': self.version,
            'manu': self.manu,
            'manu_date': self.manu_date
        }
        return get_message('version_info_update', params)

    def generate_range_update(self):
        """
        Generate range message

        :return: Message of range value
        """

        return get_message('range_info_update', {'rssi': self.rssi})

    def generate_match_descriptor_request(self):
        """
        Generate Match Descriptor Request

        """
        params = {
            'sequence': 1,
            'addr_short': BROADCAST_SHORT,
            'profile_id': PROFILE_ID_ALERTME,
            'in_cluster_list': b'',
            'out_cluster_list': CLUSTER_ID_AM_STATUS
        }
        return get_message('match_descriptor_request', params)

