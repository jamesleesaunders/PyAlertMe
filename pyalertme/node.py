import logging
import binascii
import time


class Node(object):
    def __init__(self, callback=None):
        """
        Base Constructor

        :param callback: Optional

        """
        # Resources
        self._logger = logging.getLogger('pyalertme')

        # My addresses
        self.addr_long = b''
        self.addr_short = b''

        # Type Info
        self.type = None
        self.version = None
        self.manu = None
        self.manu_date = None
        self.last_update = None

        # Hub Info
        self.hub_addr_long = b''
        self.hub_addr_short = b''
        self.associated = False

        # Attributes
        # self.attributes = {}    # Alternate attributes option
        self.rssi = None
        self.mode = None
        self.switch_state = 0
        self.power_demand = 0
        self.power_consumption = 0
        self.tamper_state = 0
        self.triggered = 0

        # Callback
        self._callback = callback if callback else self._callback

    def __str__(self):
        return self.type

    @property
    def id(self):
        """
        Device ID

        :return: Dotted MAC Address
        """
        return self.pretty_mac(self.addr_long)

    @property
    def addr_tuple(self):
        """
        Return a tuple of the 48-bit Long Address and 16-bit Short Address.
        This is typically used to pass addresses to send_message().
        """
        return self.addr_long, self.addr_short

    @staticmethod
    def pretty_mac(address_long):
        """
        Convert long address to pretty mac address string
        TODO: This may be a little over complicated at the moment,
        I was struggling to get this to work for both Python2 and Python3.
        I am sure this could be simplified... but for now - this works!

        # MAC Address Manufacturers:
        #   00:0d:6f:00:03:bb:b9:f8 = Ember Corporation
        #   00:13:a2:00:40:a2:3b:09 = MaxStream, Inc
        #   00:1E:5E:09:02:14:C5:AB = Computime Ltd.

        :param address_long:
        :return:
        """
        mac_str = str(binascii.b2a_hex(address_long).decode())
        mac_arr = [mac_str[i:i + 2] for i in range(0, len(mac_str), 2)]
        ret = ':'.join(b for b in mac_arr)

        return ret

    def get_attribute(self, attr_name):
        """
        Get Single Attributes

        :param attr_name:
        :return:
        """
        attr_value = self.__getattribute__(attr_name)
        # attr_value = self.attributes[attr_name]    # Alternate attributes option

        return attr_value

    def set_attributes(self, attributes):
        """
        Set Multiple Attributes

        :param attributes:
        :return:
        """
        if attributes:
            for attr_name, attr_value in attributes.iteritems():
                self.set_attribute(attr_name, attr_value)

    def set_attribute(self, attr_name, attr_value):
        """
        Set Single Attribute

        :param attr_name:
        :param attr_value:
        :return:
        """
        self._logger.debug('Attribute Update [NodeID: %s Field: %s Value: %s]', self.id, attr_name, attr_value)
        self.__setattr__(attr_name, attr_value)
        # self.attributes[attr_name] = attr_value    # Alternate attributes option
        self.last_update = time.time()
        self._callback(attr_name, attr_value)

    def _callback(self, attr_name, attr_value):
        """
        Callback when attributes are updated

        :param attr_name:
        :param attr_value:
        :return:
        """
        print("Attribute Update [Node ID: " + self.id + "\tField: " + attr_name + "\tValue: " + str(attr_value) + "]")
