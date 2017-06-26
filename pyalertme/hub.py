import logging
from pyalertme.zigbee import *
from pyalertme.base import Base
from pyalertme.device import Device
import struct
import time
import binascii
import threading

class Hub(Base):

    def __init__(self, callback=None):
        """
        Hub Constructor

        """
        Base.__init__(self, callback)

        # Type Info
        self.type = 'Nano Hub'
        self.version = 12345
        self.manu = 'PyAlertMe'
        self.manu_date = '2017-01-01'

        # By default the Hub is associated
        self.associated = True

        # Discovery thread and list of discovered devices
        self._discovery_thread = threading.Thread(target=self._discovery)
        self.devices = {}

    def discovery(self):
        """
        Start Discovery Mode - Start discovery thread.

        """
        self._logger.debug('Discovery Mode Started')
        self._discovery_thread.start()

    def _discovery(self):
        """
        Discovery Thread

        """
        # First, send out a broadcast every 2 seconds for 30 seconds
        timeout = time.time() + 30
        i = 1
        while time.time() < timeout:
            self._logger.debug('Sending Discovery Request #%s', i)
            message = get_message('routing_table_request')
            self.send_message(message, BROADCAST_LONG, BROADCAST_SHORT)
            i += 1
            time.sleep(2.00)

        # Next, sent out a version request to each device we have discovered above
        for (device_id, device_obj) in self.devices.items():
            self.send_type_request(device_obj)
            time.sleep(1.00)

    def set_device_attributes(self, device_obj, attributes):
        """
        Save Multiple Node Attributes

        :param device_obj: Device Object
        :param attributes: Attributes Dict
        :return:
        """
        for attrib_name, value in attributes.iteritems():
            self.set_device_attribute(device_obj, attrib_name, value)

    def set_device_attribute(self, device_obj, attrib_name, value):
        """
        Save Single Node Attribute

        :param device_obj: Device Object
        :param attrib_name: Attribute Name
        :param value: Attribute Value
        :return:
        """
        self._logger.debug('Updating Node Attribute: %s Value: %s', attrib_name, value)
        device_obj.set_attribute(attrib_name, value)
        device_id = device_obj.id
        self._callback('Attribute', device_id, attrib_name, value)

    def list_devices(self):
        """
        Return list of known devices.

        :return: Dictionary of Nodes
        """
        devices = {}
        for (device_id, device_obj) in self.devices.items():
            devices[device_id] = {
                'type': device_obj.type,
                'manu': device_obj.manu,
                'version': device_obj.version
            }

        return devices

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

    def device_obj_from_addr_long(self, addr_long):
        """
        Given a 48-bit Long Address return Device Object.
        If the device is not in the known devices list of known devices
        then generate new Device Object and add it to the list.

        :param addr_long: 48-bits Long Address
        :return: Device Object
        """
        # If this address is me (i.e. the hub), don't add to known devices list and don't
        # generate device object, also if we don't know what our own address is yet we can't check.
        if self.addr_long == addr_long or self.addr_long is None:
            device_obj = None

        else:
            # See if we already know about this device.
            # If not get device_id and add to list of known devices.
            device_id = Base.pretty_mac(addr_long)
            device_obj = self.device_obj_from_id(device_id)

            if not device_obj:
                device_obj = Device()
                device_obj.addr_long = addr_long
                self.devices[device_id] = device_obj

        return device_obj

    def process_message(self, message):
        """
        Process incoming message

        :param message:
        :return:
        """
        super(Hub, self).process_message(message)

        # ZigBee Explicit Packets
        if message['id'] == 'rx_explicit':
            source_addr_long = message['source_addr_long']
            source_addr_short = message['source_addr']
            device_obj = self.device_obj_from_addr_long(source_addr_long)

            if device_obj is not None:
                # We don't need to do this every time!
                device_obj.addr_short = source_addr_short

                profile_id = message['profile']
                cluster_id = message['cluster']

                if profile_id == PROFILE_ID_ZDP:
                    # ZigBee Device Profile ID
                    if cluster_id == CLUSTER_ID_ZDO_NWK_ADDR_REQ:
                        # Network (16-bit) Address Request
                        self._logger.debug('Received Network (16-bit) Address Request')

                    elif cluster_id == CLUSTER_ID_ZDO_NWK_ADDR_RSP:
                        # Network (16-bit) Address Response.
                        self._logger.debug('Received Network (16-bit) Address Response')

                    elif cluster_id == CLUSTER_ID_ZDO_MGMT_RTG_RSP:
                        # Management Routing Response
                        self._logger.debug('Received Management Routing Response')
                        
                    elif cluster_id == CLUSTER_ID_ZDO_SIMPLE_DESC_REQ:
                        # Simple Descriptor Request.
                        self._logger.debug('Received Simple Descriptor Request')
                        
                    elif cluster_id == CLUSTER_ID_ZDO_ACTIVE_EP_REQ:
                        # Active Endpoint Request.
                        self._logger.debug('Received Active Endpoint Request')

                    elif cluster_id == CLUSTER_ID_ZDO_ACTIVE_EP_RSP:
                        # Active Endpoints Response
                        # This message tells us what the device can do, but it isn't constructed correctly to match what
                        # the switch can do according to the spec. This is another message that gets it's response after
                        # we receive the Match Descriptor below.
                        self._logger.debug('Received Active Endpoint Response')

                    elif cluster_id == CLUSTER_ID_ZDO_MATCH_DESC_REQ:
                        # Match Descriptor Request
                        self._logger.debug('Received Match Descriptor Request')
                        # This is the point where we finally respond to the switch. A couple of messages are sent
                        # to cause the switch to join with the controller at a network level and to cause it to
                        # regard this controller as valid.

                        # First send the Match Descriptor Response
                        sequence = message['rf_data'][0:1]
                        reply = self.generate_match_descriptor_response(sequence)
                        self.send_message(reply, source_addr_long, source_addr_short)

                        # The next messages are directed at the hardware code (rather than the network code).
                        # The device has to receive these two message to stay joined.
                        time.sleep(2)
                        reply = self.generate_version_info_request()
                        self.send_message(reply, source_addr_long, source_addr_short)
                        time.sleep(2)
                        reply = self.generate_mode_change_request('Normal')
                        self.send_message(reply, source_addr_long, source_addr_short)

                        # We are fully associated!
                        device_obj.associated = True
                        self._logger.debug('New Device Fully Associated')
                        
                    elif cluster_id == CLUSTER_ID_ZDO_END_DEVICE_ANNCE:
                        # Device Announce Message
                        self._logger.debug('Received Device Announce Message')
                        # This will tell me the address of the new thing
                        # so we're going to send an active endpoint request
                        reply = self.generate_active_endpoints_request(source_addr_short)
                        self.send_message(reply, source_addr_long, source_addr_short)
                        
                    elif cluster_id == CLUSTER_ID_ZDO_MGMT_NETWORK_UPDATE:
                        # Management Network Update Notify.
                        self._logger.debug('Received Management Network Update Notify')

                    else:
                        self._logger.error('Unrecognised Cluster ID: %r', cluster_id)

                elif profile_id == PROFILE_ID_ALERTME:
                    # AlertMe Profile ID
                    cluster_cmd = message['rf_data'][2:3]

                    if cluster_id == CLUSTER_ID_AM_SWITCH:
                        if cluster_cmd == CLUSTER_CMD_AM_STATE_RESP:
                            self._logger.debug('Received Switch Status Update')
                            attributes = parse_switch_state_update(message['rf_data'])
                            self.set_device_attributes(device_obj, attributes)

                        else:
                            self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                    elif cluster_id == CLUSTER_ID_AM_POWER:
                        if cluster_cmd == CLUSTER_CMD_AM_PWR_DEMAND:
                            self._logger.debug('Received Power Demand Update')
                            attributes = parse_power_demand(message['rf_data'])
                            self.set_device_attributes(device_obj, attributes)

                        elif cluster_cmd == CLUSTER_CMD_AM_PWR_CONSUMPTION:
                            self._logger.debug('Received Power Consumption & Uptime Update')
                            attributes = parse_power_consumption(message['rf_data'])
                            self.set_device_attributes(device_obj, attributes)

                        elif cluster_cmd == CLUSTER_CMD_AM_PWR_UNKNOWN:
                            self._logger.debug('Unknown Power Update')
                            attributes = parse_power_unknown(message['rf_data'])
                            self.set_device_attributes(device_obj, attributes)

                        else:
                            self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                    elif cluster_id == CLUSTER_ID_AM_STATUS:
                        if cluster_cmd == CLUSTER_CMD_AM_STATUS:
                            self._logger.debug('Received Status Update')
                            attributes = parse_status_update(message['rf_data'])
                            self.set_device_attributes(device_obj, attributes)

                        else:
                            self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                    elif cluster_id == CLUSTER_ID_AM_TAMPER:
                        self._logger.debug('Received Tamper Switch Changed Update')
                        attributes = parse_tamper_state(message['rf_data'])
                        self.set_device_attributes(device_obj, attributes)

                    elif cluster_id == CLUSTER_ID_AM_BUTTON:
                        self._logger.debug('Received Button Press Update')
                        attributes = parse_button_press(message['rf_data'])
                        self.set_device_attributes(device_obj, attributes)

                    elif cluster_id == CLUSTER_ID_AM_DISCOVERY:
                        if cluster_cmd == CLUSTER_CMD_AM_RSSI:
                            self._logger.debug('Received RSSI Range Test Update')
                            attributes = parse_range_info_update(message['rf_data'])
                            self.set_device_attributes(device_obj, attributes)

                        elif cluster_cmd == CLUSTER_CMD_AM_VERSION_RESP:
                            self._logger.debug('Received Version Information')
                            attributes = parse_version_info_update(message['rf_data'])
                            self.set_device_attributes(device_obj, attributes)

                        else:
                            self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                    elif cluster_id == CLUSTER_ID_AM_SECURITY:
                        self._logger.debug('Received Security Event')
                        # Security Cluster
                        # When the device first connects, it comes up in a state that needs initialization, this command
                        # seems to take care of that. So, look at the value of the data and send the command.
                        if message['rf_data'][3:7] == b'\x15\x00\x39\x10':
                            reply = self.generate_security_init()
                            self.send_message(reply, source_addr_long, source_addr_short)

                        attributes = parse_security_state(message['rf_data'])
                        self.set_device_attributes(device_obj, attributes)

                    else:
                        self._logger.error('Unrecognised Cluster ID: %r', cluster_id)

                else:
                    self._logger.error('Unrecognised Profile ID: %r', profile_id)

    def generate_active_endpoints_request(self, addr_short):
        """
        Generate Active Endpoints Request.

        :param addr_short:
        """
        params = {
            'sequence':  170,
            'addr_short': addr_short
        }
        return get_message('active_endpoints_request', params)

    def generate_match_descriptor_response(self, sequence):
        """
        Generate Match Descriptor Response.

        :param rf_data:
        """
        params = {
            'sequence': 3, # sequence,
            'addr_short': self.addr_short,
            'endpoint_list': ENDPOINT_ALERTME
        }
        return get_message('match_descriptor_response', params)

    def generate_relay_state_request(self, state=''):
        """
        Generate Relay State Change Request.

        :param state: Switch Relay State
        :return: message
        """
        return get_message('switch_state_request', {'relay_state': state})

    def generate_mode_change_request(self, mode):
        """
        Generate Mode Change Request
        Available Modes: 'Normal', 'RangeTest', 'Locked', 'Silent'

        :param mode: Switch Mode
        :return: message
        """
        return get_message('mode_change_request', {'mode': mode})

    def generate_version_info_request(self):
        """
        Generate Node Type Request. Version, Manufacturer, etc.

        :return: Message
        """
        return get_message('version_info_request')

    def generate_security_init(self):
        """
        Generate Security Initialization

        :return: Message
        """
        return get_message('security_init')











    def call_device_command(self, device_id, command, value):
        """
        Shortcut function to set device state, mode etc.
        Calls send_state_request, send_mode_request etc.

        :param device_id:
        :param command: Parameter or command to be sent
        :param value: Value, State, Mode
        """
        if command == 'relay_state':
            self.send_relay_state_request(device_id, value)
        elif command == 'mode':
            self.send_mode_request(device_id, value)
        else:
            self._logger.error('Invalid Attribute Request')

    def send_type_request(self, device_obj):
        """
        Send Type Request

        :param device_obj:
        """
        message = self.generate_version_info_request()
        addresses = device_obj.addr_tuple
        self.send_message(message, *addresses)

    def send_relay_state_request(self, device_obj, state):
        """
        Send Relay State Request

        :param device_obj:
        :param state:
        """
        message = self.generate_relay_state_request(state)
        addresses = device_obj.addr_tuple
        self.send_message(message, *addresses)

    def send_mode_request(self, device_obj, mode):
        """
        Send Mode Request

        :param device_obj:
        :param mode:
        """
        message = self.generate_mode_change_request(mode)
        addresses = device_obj.addr_tuple
        self.send_message(message, *addresses)