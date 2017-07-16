import logging
from pyalertme.zb import *
from pyalertme.zbnode import ZBNode
import struct
import time
import binascii
import threading
from pyalertme.zbnode import Node


class ZBDevice(ZBNode):

    def __init__(self, serial, callback=None):
        """
        Device Constructor

        :param serial: Serial Object
        :param callback: Optional
        """
        ZBNode.__init__(self, serial, callback)

        # Type Info
        self.type = 'ZBDevice'
        self.version = 12345
        self.manu = 'PyAlertMe'
        self.manu_date = '2017-01-01'

        # Addresses of the hub we are associated with
        self.hub_addr_long = None
        self.hub_addr_short = None
        self.hub_obj = None
        self.associated = False

        # Attributes
        self.rssi = 197
        self.mode = 'NORMAL'


    def receive_message(self, message):
        hub_obj = Node

        if not self.associated:
            params = {
                'sequence': 1,
                'addr_short': BROADCAST_SHORT,
                'profile_id': PROFILE_ID_ALERTME,
                'in_cluster_list': b'',
                'out_cluster_list': CLUSTER_ID_AM_STATUS
            }
            message = self.get_message('match_descriptor_request', params)
            self.send_message(message, message['source_addr_long'], message['source_addr'])

        attributes = super(ZBDevice, self).receive_message(message)

        if hub_obj:
            hub_obj.set_attributes(attributes)

        return attributes