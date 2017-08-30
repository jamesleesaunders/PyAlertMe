import logging
from pyalertme.zbnode import *
import time
import threading


class ZBHub(ZBNode):
    """
    ZigBee Hub object.
    """
    def __init__(self, serial, callback=None):
        """
        Hub Constructor.

        :param serial: Serial Object
        :param callback: Optional
        """
        ZBNode.__init__(self, serial, callback)

        # Type Info
        self.type = 'ZBHub'
        self.version = 12345
        self.manu = 'PyAlertMe'
        self.manu_date = '2017-01-01'

        # Discovery Thread and List of Known Devices
        self._discovery_thread = threading.Thread(target=self._discovery)
        self.devices = {}

    def discovery(self):
        """
        Start Discovery Mode - Start discovery thread.

        """
        self._logger.info('Discovery Mode Started')
        self._discovery_thread.start()

    def _discovery(self):
        """
        Discovery Thread.
        Send out a broadcast every 2 seconds for 30 seconds.

        """
        timeout = time.time() + 30
        i = 1
        while time.time() < timeout:
            self._logger.info('Sending Discovery Request #%s', i)
            message = self.generate_message('routing_table_request')
            self.send_message(message, BROADCAST_LONG, BROADCAST_SHORT)
            i += 1
            time.sleep(2.00)

    def list_devices(self):
        """
        Return list of associated devices.

        :return: Dictionary of Devices
        """
        devices = {}
        for (device_id, device_obj) in self.devices.items():
            devices[device_id] = {
                'type': device_obj.type,
                'manu': device_obj.manu,
                'version': device_obj.version
            }

        return devices

    def get_device(self, device_id):
        """
        Return single associated device.

        :param device_id: Dotted MAC Address
        :return: Dictionary of Node Attributes
        """
        device_obj = self.devices[device_id]

        return device_obj.__dict__

    def device_obj_from_id(self, device_id):
        """
        Given a Device ID return Device Object.
        If the device is not in the list then return None.

        :param device_id: Dotted MAC Address
        :return: Device Object
        """
        if device_id in self.devices.keys():
            device_obj = self.devices[device_id]
        else:
            device_obj = None

        return device_obj

    def device_obj_from_addrs(self, device_addr_long, device_addr_short):
        """
        Given Addresses return Device Object.
        If the device is not in the known devices list of known devices
        then generate new Device Object and add it to the list.

        :param device_addr_long: 48-bits Long Address
        :param device_addr_short: Short Address
        :return: Device Object
        """
        # If this address is me (i.e. the hub), do not add it to known devices list and
        # do not generate device object, also if we don't know what our own address is 
        # yet we can't check.
        if self.addr_long == device_addr_long or self.addr_long is None:
            device_obj = None

        else:
            # Do we already know about this device. Is it in our list of known devices?
            # If not generate a device_id (pretty mac) and add to list of known devices.
            device_id = ZBNode.pretty_mac(device_addr_long)
            device_obj = self.device_obj_from_id(device_id)

            if not device_obj:
                self._logger.info('Discovered New Device')
                # Create new device object
                device_obj = Node()
                device_obj.addr_long = device_addr_long
                device_obj.addr_short = device_addr_short
                self.devices[device_id] = device_obj

            if not device_obj.type:
                # The device has to receive these two messages to stay joined.
                message = self.generate_message('mode_change_request', {'mode': 'normal'})
                self.send_message(message, device_addr_long, device_addr_short)
                message = self.generate_message('version_info_request')
                self.send_message(message, device_addr_long, device_addr_short)

                # We are fully associated!
                device_obj.associated = True
                self._logger.info('New Device %s Fully Associated', device_id)

        return device_obj

    def process_message(self, addr_long, addr_short, attributes):
        """
        Process after message received.

        :param addr_long: Short Address
        :param addr_short: Long Address
        :param attributes: Dict of message
        :return:
        """
        device_obj = self.device_obj_from_addrs(addr_long, addr_short)
        if device_obj:
            device_obj.set_attributes(attributes)

    def send_type_request(self, device_obj):
        """
        Send Type Request.

        :param device_obj:
        """
        message = self.generate_message('version_info_request')
        addresses = device_obj.addr_tuple
        self.send_message(message, *addresses)

    def send_switch_state_request(self, device_obj, state):
        """
        Send Relay State Request.

        :param device_obj:
        :param state:
        """
        message = self.generate_message('switch_state_request', {'switch_state': state})
        addresses = device_obj.addr_tuple
        self.send_message(message, *addresses)

    def send_mode_request(self, device_obj, mode):
        """
        Send Mode Request.

        :param device_obj:
        :param mode:
        """
        message = self.generate_message('mode_change_request', {'mode': mode})
        addresses = device_obj.addr_tuple
        self.send_message(message, *addresses)

    def call_device_command(self, device_id, command, value):
        """
        Shortcut function to set device state, mode etc.
        Calls send_state_request, send_mode_request etc.

        :param device_id:
        :param command: Parameter or command to be sent
        :param value: Value, State, Mode
        """
        if command == 'switch_state':
            self.send_switch_state_request(device_id, value)
        elif command == 'mode':
            self.send_mode_request(device_id, value)
        else:
            self._logger.error('Invalid Attribute Request')
