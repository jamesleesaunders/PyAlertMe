import logging
from pyalertme.zbnode import *


class ZBDevice(ZBNode):
    """
    ZigBee Device object.
    """
    def __init__(self, serial, callback=None):
        """
        Device Constructor.

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

    def process_message(self, addr_long, addr_short, attributes):
        """
        Process after message received.

        :param addr_long: Short Address
        :param addr_short: Long Address
        :param attributes: Dict of message
        :return:
        """
        self.set_attributes(attributes)

        if not self.associated:
            # If we are not associated at this point try and invoke an association
            # by sending a Match Descriptor Request.
            self.hub_obj = Node()
            self.hub_obj.addr_long = addr_long
            self.hub_obj.addr_short = addr_short
            params = {
                'sequence': 1,
                'addr_short': BROADCAST_SHORT,
                'profile_id': PROFILE_ID_ALERTME,
                'in_cluster_list': b'',
                'out_cluster_list': CLUSTER_ID_AM_STATUS
            }

            reply = self.generate_message('match_descriptor_request', params)
            self.send_message(reply, self.hub_obj.addr_long, self.hub_obj.addr_short)
            self.associated = True
            self._logger.info('Device Associated')

    def message_range_update(self):
        """
        Generate Range Update Message.

        :return: Message
        """
        params = {'rssi': self.rssi}
        message = self.generate_message('range_update', params)
        return message

    def message_version_info_update(self):
        """
        Generate Version update Message.

        :return: Message
        """
        params = {
            'type': self.type,
            'version': self.version,
            'manu': self.manu,
            'manu_date': self.manu_date
        }
        message = self.generate_message('version_info_update', params)
        return message