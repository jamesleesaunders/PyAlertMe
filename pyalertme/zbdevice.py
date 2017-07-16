import logging
from pyalertme.zbnode import *


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

        attributes = {}
        if message['id'] == 'rx_explicit':
            if not self.hub_obj:
                self.hub_obj = Node()
                self.hub_obj.addr_long = message['source_addr_long']
                self.hub_obj.addr_short = message['source_addr']
                self.associated = True
            # Not sure if we need the above and the below - they are doing similar things
            if not self.associated:
                params = {
                    'sequence': 1,
                    'addr_short': self.BROADCAST_SHORT,
                    'profile_id': self.PROFILE_ID_ALERTME,
                    'in_cluster_list': b'',
                    'out_cluster_list': self.CLUSTER_ID_AM_STATUS
                }
                reply = self.get_message('match_descriptor_request', params)
                self.send_message(reply, message['source_addr_long'], message['source_addr'])

            attributes = super(ZBDevice, self).receive_message(message)

            self.hub_obj.set_attributes(attributes)

        return attributes
