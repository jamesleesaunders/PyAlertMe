import logging
from pyalertme import *
import struct
import time
import binascii
import threading


class Device(Base):

    def __init__(self):
        """
        Device Constructor

        """
        Base.__init__(self)

        # Type Info
        self.manu = 'AlertMe.com'
        self.type = 'Generic Device'
        self.date = '2017-01-02'
        self.version = 1

        # Start off not associated
        self.associated = False

        self.rssi = 197

    def process_message(self, message):
        """
        Process incoming message

        :param message: Dict of message
        :return:
        """
        super(Device, self).process_message(message)
        # We are only interested in Zigbee Explicit packets.
        if (message['id'] == 'rx_explicit'):
            profile_id = message['profile']
            cluster_id = message['cluster']

            # Take note of hub address
            self.hub_addr_long = message['source_addr_long']
            self.hub_addr_short = message['source_addr']

            if (profile_id == self.ZDP_PROFILE_ID):
                # Zigbee Device Profile ID
                if (cluster_id == b'\x00\x32'):
                    self.logger.debug('Broacast Discover TBC')

                elif (cluster_id == b'\x00\x05'):
                    self.logger.debug('Active Endpoint Request')

                elif (cluster_id == b'\x80\x06'):
                    self.logger.debug('Match Descriptor')

            elif (profile_id == self.ALERTME_PROFILE_ID):
                # AlertMe Profile ID

                # Python 2 / 3 hack
                if (hasattr(bytes(), 'encode')):
                    cluster_cmd = message['rf_data'][2]
                else:
                    cluster_cmd = bytes([message['rf_data'][2]])

                if (cluster_id == b'\x00\xf6'):
                    #'data': b'\x11\x01\xfc' same as type?
                    self.logger.debug('Hardware Join Messages 1')

                elif (cluster_id == b'\x00\xf6'):
                    # b'\x11\x00\xfc\x00\x01'
                    self.logger.debug('Version Request')
                    self.send_message(self.get_type(), self.hub_addr_long, self.hub_addr_short)

                elif (cluster_id == b'\x00\xf0'):
                    self.logger.debug('Hardware Join Messages 2')
                    # We are now fully associated
                    self.associated = True

                elif (cluster_id == b'\x00\xee'):
                    if (cluster_cmd == b'\xfa'):
                        self.logger.debug('Range Test')
                        self.send_message(self.get_range(), self.hub_addr_long, self.hub_addr_short)

            else:
                self.logger.error('Unrecognised Profile ID: %e', profile_id)

    def get_type(self):
        """
        Generate type message

        :return: Message of device type
        """
        checksum = b'\tq'
        cluster_cmd = b'\xfe'
        data = \
            checksum \
            + cluster_cmd \
            + struct.pack('H', self.version) \
            +  b'\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0b' \
            + self.manu \
            + '\n' + self.type \
            + '\n' + self.date
        message = {
            'description':   'Type Info',
            'src_endpoint':  b'\x00',
            'dest_endpoint': b'\x02',
            'cluster':       b'\x00\xf6',
            'profile':       self.ALERTME_PROFILE_ID,
            'data':          data,
        }
        return(message)

    def get_range(self):
        """
        Generate range message

        :return: Message of range value
        """
        # 197
        # cluster_cmd == b'\xfd'
        # data = b'\t+\xfd\xc5w'
        data = b'\t+' + b'\xfd' + struct.pack('B', self.rssi)
        message = {
            'description':   'Range Info',
            'src_endpoint':  b'\x00',
            'dest_endpoint': b'\x02',
            'cluster':       b'\x00\xf6',
            'profile':       self.ALERTME_PROFILE_ID,
            'data':          data,
        }
        return(message)