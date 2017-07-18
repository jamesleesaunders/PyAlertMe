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
        self.power_demand = 0
        self.power_consumption = 0

    def receive_message(self, message):

        attributes = {}
        if message['id'] == 'rx_explicit':
            if not self.associated:
                self.hub_obj = Node()
                self.hub_obj.addr_long = message['source_addr_long']
                self.hub_obj.addr_short = message['source_addr']

                params = {
                    'sequence': 1,
                    'addr_short': BROADCAST_SHORT,
                    'profile_id': PROFILE_ID_ALERTME,
                    'in_cluster_list': b'',
                    'out_cluster_list': CLUSTER_ID_AM_STATUS
                }
                reply = self.get_message('match_descriptor_request', params)
                self.send_message(reply, message['source_addr_long'], message['source_addr'])

                self.associated = True

            attributes = super(ZBDevice, self).receive_message(message)

            self.hub_obj.set_attributes(attributes)

        return attributes

    def message_range_update(self):
        params = {'rssi': self.rssi}
        message = self.get_message('range_update', params)
        return message

    def message_version_info_update(self):
        params = {
            'type': self.type,
            'version': self.version,
            'manu': self.manu,
            'manu_date': self.manu_date
        }
        message = self.get_message('version_info_update', params)
        return message

    def message_switch_state_update(self):
        params = {'switch_state': self.switch_state}
        message = self.get_message('switch_state_update', params)
        return message

    def message_power_demand_update(self):
        params = {'power_demand': self.power_demand}
        message = self.get_message('power_demand_update', params)
        return message