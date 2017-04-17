import logging
from pyalertme import *
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
        self.manu = 'PyAlertMe'
        self.type = 'Generic Device'
        self.date = '2016-09-18'
        self.version = 00001

        # Start off not associated
        self.associated = False
        self.hub_addr_long = None
        self.hub_addr_short = None
        self._updates_thread = threading.Thread(target=self._updates)
        self._updates_thread.start()

        self.rssi = 197

    def updates(self):
        """
        Continual Updates
        Overwrite this function with things you want running every 2 seconds.
        """
        return None

    def _updates(self):
        """
        Continual Updates Thread

        """
        while True:
            if self.associated == True
                self.updates()
            time.sleep(2.00)

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

            if self.associated == False:
                self.send_message(self.generate_match_descriptor_request(), source_addr_long, source_addr_short)

            if profile_id == self.ZDP_PROFILE_ID:
                # Zigbee Device Profile ID
                if cluster_id == b'\x00\x32':
                    self._logger.debug('Received Broacast Discover TBC')

                elif cluster_id == b'\x00\x05':
                    self._logger.debug('Received Active Endpoint Request')

                elif cluster_id == b'\x80\x06':
                    self._logger.debug('Received Match Descriptor Response')

            elif (profile_id == self.ALERTME_PROFILE_ID):
                # AlertMe Profile ID

                # Python 2 / 3 hack
                if hasattr(bytes(), 'encode'):
                    cluster_cmd = message['rf_data'][2]
                else:
                    cluster_cmd = bytes([message['rf_data'][2]])

                if cluster_id == b'\x00\xf6':
                    # b'\x11\x00\xfc\x00\x01'
                    self._logger.debug('Received Version Request')
                    self.send_message(self.generate_type_update(), self.hub_addr_long, self.hub_addr_short)

                # elif cluster_id == b'\x00\xf6':
                    # b'\x11\x01\xfc'
                    # Almost the same as type above? Not sure on link yet?
                    # self._logger.debug('Received Hardware Join Message 1')

                elif cluster_id == b'\x00\xf0':
                    self._logger.debug('Received Hardware Join Message 2')
                    # Take note of hub address
                    self.hub_addr_long = message['source_addr_long']
                    self.hub_addr_short = message['source_addr']
                    # We are now fully associated
                    self.associated = True

                elif cluster_id == b'\x00\xee':
                    if cluster_cmd == b'\xfa':
                        self._logger.debug('Received Range Test Request')
                        self.send_message(self.generate_range_update(), self.hub_addr_long, self.hub_addr_short)

            else:
                self._logger.error('Unrecognised Profile ID: %r', profile_id)

    def generate_type_update(self):
        """
        Generate type message

        :return: Message of device type
        """
        checksum = b'\tq'
        cluster_cmd = b'\xfe'
        payload = struct.pack('H', self.version) \
            +  b'\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0b' \
            + self.manu \
            + '\n' + self.type \
            + '\n' + self.date
        data = checksum + cluster_cmd + payload

        message = {
            'description':  'Type Info',
            'profile': self.ALERTME_PROFILE_ID,
            'cluster': b'\x00\xf6',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': data,
        }
        return(message)

    def generate_range_update(self):
        """
        Generate range message

        :return: Message of range value
        """
        checksum = b'\t+'
        cluster_cmd = b'\xfd'
        payload = struct.pack('B', self.rssi)
        data = checksum + cluster_cmd + payload

        message = {
            'description': 'Range Info',
            'profile': self.ALERTME_PROFILE_ID,
            'cluster': b'\x00\xf6',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': data,
        }
        return(message)

    def generate_match_descriptor_request(self):
        """
        Generate Match Descriptor Request
        Broadcast or unicast transmission used to discover the device(s) that supports
        a specified profile ID and/or clusters.

        Field Name       Size (bytes)   Description
        Network Address  2              16-bit address of a device in the network whose
                                        power descriptor is being requested.
        Profile ID       2              Profile ID to be matched at the destination.
        Number of Input  1              The number of input clusters in the In Cluster
        Clusters                        List for matching. Set to 0 if no clusters supplied.
        Input Cluster    2*             List of input cluster IDs to be used for matching.
        List
        Number of Output 1              The number of output clusters in the Output Cluster
        Clusters                        List for matching. Set to 0 if no clusters supplied.
        Output Cluster   2*             List of output cluster IDs to be used for matching.
        List
                          * Number of Input Clusters
        """
        data = b'\x03\xfd\xff\x16\xc2\x00\x01\xf0\x00'
        message = {
            'description': 'Match Descriptor Request',
            'profile': self.ZDP_PROFILE_ID,
            'cluster': b'\x00\x06',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x00',
            'data': data
        }
        return message
