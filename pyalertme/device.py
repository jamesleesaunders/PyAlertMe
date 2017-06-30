import logging
from pyalertme.zigbee import *
import binascii



class Device(object):
    def __init__(self, callback=None):
        """
        Base Constructor

        :param callback: Optional
        """
        # Resources
        self._logger = logging.getLogger('pyalertme')

        # Type Info
        self.type = None
        self.version = None
        self.manu = None
        self.manu_date = None

        # Callback
        self._callback = callback if callback else self._callback

        # My addresses
        self._addr_long_list = [b'', b'']
        self.addr_long = None
        self.addr_short = None

        # Status Flags
        self.associated = False
        self.started = False

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

        :param callback: Optional
        """
        return self.addr_long, self.addr_short

    @staticmethod
    def pretty_mac(address_long):
        """
        Convert long address to pretty mac address string
        TODO: This may be a little over complicated at the moment,
        I was struggling to get this to work for both Python2 and Python3.
        I am sure this could be simplified... but for now - this works!

        # MAC Address Manufacturers
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

    def __str__(self):
        return self.type

    def _callback(self, type, node_id, field, value):
        if type == 'Attribute':
            print("Attribute Update [Node ID: " + node_id + "\tField: " + field + "\tValue: " + str(value) + "]")
        elif type == 'Property':
            print("Property Update [Node ID: " + node_id + "\tField: " + field + "\tValue: " + str(value) + "]")

    def set_attribute(self, attribute, value):
        """
        Set Associated

        :param string: attribute
        :param mixed: value
        :return:
        """
        self._logger.debug('Setting attribute: %s to value: %s', attribute, value)
        setattr(self, attribute, value)

    def list_messages(self):
        """
        List Messages

        :param message: Dict of message
        :return:
        """
        return list_messages()