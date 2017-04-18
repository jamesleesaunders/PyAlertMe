import logging
from pyalertme import *
import struct
import time
import binascii
import threading
import sqlite3

class Hub(Base):

    def __init__(self, callback=None):
        """
        Hub Constructor

        """
        Base.__init__(self, callback)

        self._discovery_thread = threading.Thread(target=self._discovery)

        # Type Info
        self.manu = 'PyAlertMe'
        self.type = 'Nano Hub'
        self.date = '2017-01-01'
        self.version = None

        # List of Associated Nodes
        self.nodes = {}

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
        while time.time() < timeout and self.started:
            self._logger.debug('Sending Discovery Request #%s', i)
            message = {
                'description': 'Management Routing Table Request',
                'src_endpoint': b'\x00',
                'dest_endpoint': b'\x00',
                'cluster': b'\x00\x32',
                'profile': self.ZDP_PROFILE_ID,
                'data': '\x12\x01'
            }
            self.send_message(message, self.BROADCAST_LONG, self.BROADCAST_SHORT)
            i += 1
            time.sleep(2.00)

        # Next, sent out a version request to each node we have discovered above
        for node_id in self.nodes.keys():
            self.send_type_request(node_id)
            time.sleep(1.00)

    def save_node_attributes(self, node_id, attributes):
        """
        Save Multiple Node Attributes
        :param node_id:
        :param attributes:
        :return:
        """
        for attrib_name, value in attributes.iteritems():
            self.save_node_attribute(node_id, attrib_name, value)

    def save_node_attribute(self, node_id, attrib_name, value):
        """
        Save Single Node Attribute

        :param node_id:
        :param attrib_name:
        :param value:
        :return:
        """
        self._logger.debug('Updating Node Attribute: %s Value: %s', attrib_name, value)
        self.nodes[node_id]['Attributes'][attrib_name] = value
        self._callback('Attribute', node_id, attrib_name, value)

    def save_node_properties(self, node_id, properties):
        """
        Save Multiple Node Properties

        :param node_id:
        :param properties:
        :return:
        """
        for property_name, value in properties.iteritems():
            self.save_node_property(node_id, property_name, value)

    def save_node_property(self, node_id, property_name, value):
        """
        Save Single Node Property

        :param node_id:
        :param property_name:
        :param value:
        :return:
        """
        self._logger.debug('Updating Node Property: %s Value: %s', property_name, value)
        self.nodes[node_id][property_name] = value
        self._callback('Property', node_id, property_name, value)

    def get_nodes(self):
        """
        Get Nodes

        :return: Dictionary of Nodes
        """
        return self.nodes

    def get_node(self, node_id):
        """
        Given a Node ID return node.

        :param node_id: Integer Short Node ID
        :return: Node record
        """
        return self.nodes[node_id]

    def addr_long_to_node_id(self, addr_long):
        """
        Given a 48-bit Long Address lookup or generate new Node ID.

        :param addr_long: 48-bits Long Address
        :return: Node ID
        """
        # If this address is me, don't add to nodes list and don't generate node_id
        if addr_long == self.addr_long:
            return None

        # See if we already know about this device.
        addr_long_to_id = dict((addresses['AddressLong'], id) for id, addresses in self.nodes.iteritems())
        if addr_long in addr_long_to_id:
            node_id = addr_long_to_id[addr_long]
        else:
            # If not generate new node_id and add to list of known devices.
            node_id = Base.pretty_mac(addr_long)
            self.nodes[node_id] = {'AddressLong': addr_long, 'Attributes': {}}
        return node_id

    def node_id_to_addrs(self, node_id):
        """
        Given a Node ID return a tuple of 48-bit Long Address and 16-bit Short Address.
        This is typically used to pass addresses to send_message().

        :param node_id:  Integer Short Node ID
        :return: Tuple of long and short addresses
        """
        addr_long = self.nodes[node_id]['AddressLong']
        addr_short = self.nodes[node_id]['AddressShort']

        return addr_long, addr_short

    def process_message(self, message):
        """
        Process incoming message

        :param message:
        :return:
        """
        super(Hub, self).process_message(message)

        # Zigbee Explicit Packets
        if message['id'] == 'rx_explicit':
            source_addr_long = message['source_addr_long']
            source_addr_short = message['source_addr']
            node_id = self.addr_long_to_node_id(source_addr_long)

            if node_id:
                self.save_node_properties(node_id, {'AddressLong': source_addr_long, 'AddressShort': source_addr_short})
                profile_id = message['profile']
                cluster_id = message['cluster']

                if profile_id == self.ZDP_PROFILE_ID:
                    # Zigbee Device Profile ID

                    if cluster_id == b'\x13':
                        # Device Announce Message.
                        self._logger.debug('Received Device Announce Message')
                        # This will tell me the address of the new thing
                        # so we're going to send an active endpoint request
                        reply = self.generate_active_endpoints_request(source_addr_short)
                        self.send_message(reply, source_addr_long, source_addr_short)

                    elif cluster_id == b'\x00\x00':
                        # Network (16-bit) Address Request.
                        self._logger.debug('Received Network (16-bit) Address Request')

                    elif cluster_id == b'\x80\x00':
                        # Network (16-bit) Address Response.
                        # Not sure what this is? Only seen on the Hive ActivePlug?
                        # See: http://www.desert-home.com/2015/06/hacking-into-iris-door-sensor-part-4.html
                        # http://ftp1.digi.com/support/images/APP_NOTE_XBee_ZigBee_Device_Profile.pdf
                        self._logger.debug('Received Network (16-bit) Address Response')

                    elif cluster_id == b'\x00\x05':
                        # Active Endpoint Request.
                        self._logger.debug('Received Active Endpoint Request')

                    elif cluster_id == b'\x80\x05':
                        # Active Endpoint Response.
                        # This message tells us what the device can do, but it isn't constructed correctly to match what
                        # the switch can do according to the spec. This is another message that gets it's response after
                        # we receive the Match Descriptor below.
                        self._logger.debug('Received Active Endpoint Response')

                    elif cluster_id == b'\x00\x04':
                        # Route Record Broadcast Response.
                        self._logger.debug('Received Simple Descriptor Request')

                    elif cluster_id == b'\x80\x38':
                        self._logger.debug('Received Management Network Update Request')

                    elif cluster_id == b'\x802':
                        # Route Record Broadcast Response.
                        self._logger.debug('Received Route Record Broadcast Response')

                    elif cluster_id == b'\x00\x06':
                        # Match Descriptor Request.
                        self._logger.debug('Received Match Descriptor Request')
                        # This is the point where we finally respond to the switch. A couple of messages are sent
                        # to cause the switch to join with the controller at a network level and to cause it to
                        # regard this controller as valid.

                        # First send the Match Descriptor Response
                        reply = self.generate_match_descriptor_response(message['rf_data'])
                        self.send_message(reply, source_addr_long, source_addr_short)

                        # The next message is directed at the hardware code (rather than the network code).
                        time.sleep(2)
                        # The device has to receive this message to stay joined.
                        reply = self.generate_hardware_join_1()
                        self.send_message(reply, source_addr_long, source_addr_short)
                        reply = self.generate_hardware_join_2()
                        self.send_message(reply, source_addr_long, source_addr_short)

                        # We are fully associated!
                        self._logger.debug('New Device Fully Associated')

                    else:
                        self._logger.error('Unrecognised Cluster ID: %r', cluster_id)

                elif profile_id == self.ALERTME_PROFILE_ID:
                    # AlertMe Profile ID

                    # Python 2 / 3 hack
                    if hasattr(bytes(), 'encode'):
                        cluster_cmd = message['rf_data'][2]
                    else:
                        cluster_cmd = bytes([message['rf_data'][2]])

                    if cluster_id == b'\x00\xee':
                        if cluster_cmd == b'\x80':
                            self._logger.debug('Received Switch Status Update')
                            attributes = self.parse_switch_state(message['rf_data'])
                            self.save_node_attributes(node_id, attributes)

                        else:
                            self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                    elif cluster_id == b'\x00\xef':
                        if cluster_cmd == b'\x81':
                            self._logger.debug('Received Power Demand Update')
                            attributes = self.parse_power_demand(message['rf_data'])
                            self.save_node_attributes(node_id, attributes)

                        elif cluster_cmd == b'\x82':
                            self._logger.debug('Received Power Consumption & Uptime Update')
                            attributes = self.parse_power_consumption(message['rf_data'])
                            self.save_node_attributes(node_id, attributes)

                        else:
                            self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                    elif cluster_id == b'\x00\xf0':
                        if cluster_cmd == b'\xfb':
                            self._logger.debug('Received Status Update')
                            attributes = self.parse_status_update(message['rf_data'])
                            self.save_node_attributes(node_id, attributes)

                            # This may be the missing link to this thing?
                            self._logger.debug('Sending Missing Link')
                            reply = self.generate_missing_link(message['dest_endpoint'], message['source_endpoint'])
                            self.send_message(reply, source_addr_long, source_addr_short)

                        else:
                            self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                    elif cluster_id == b'\x00\xf2':
                        self._logger.debug('Received Tamper Switch Changed Update')
                        attributes = self.parse_tamper_state(message['rf_data'])
                        self.save_node_attributes(node_id, attributes)

                    elif cluster_id == b'\x00\xf3':
                        self._logger.debug('Received Button Press Update')
                        attributes = self.parse_button_press(message['rf_data'])
                        self.save_node_attributes(node_id, attributes)


                    elif cluster_id == b'\x00\xf6':
                        if cluster_cmd == b'\xfd':
                            self._logger.debug('Received RSSI Range Test Update')
                            attributes = self.parse_range_info(message['rf_data'])
                            self.save_node_attributes(node_id, attributes)

                        elif (cluster_cmd == b'\xfe'):
                            self._logger.debug('Received Version Information')
                            properties = self.parse_version_info(message['rf_data'])
                            self.save_node_properties(node_id, properties)

                        else:
                            self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                    elif cluster_id == b'\x05\x00':
                        self._logger.debug('Received Security Event')
                        # Security Cluster.
                        # When the device first connects, it comes up in a state that needs initialization, this command
                        # seems to take care of that. So, look at the value of the data and send the command.
                        if message['rf_data'][3:7] == b'\x15\x00\x39\x10':
                            reply = self.generate_security_init()
                            self.send_message(reply, source_addr_long, source_addr_short)

                        attributes = self.parse_security_state(message['rf_data'])
                        self.save_node_attributes(node_id, attributes)

                    else:
                        self._logger.error('Unrecognised Cluster ID: %r', cluster_id)

                else:
                    self._logger.error('Unrecognised Profile ID: %r', profile_id)

    def call_node_command(self, node_id, command, value):
        """
        Shortcut function to set node state, mode etc.
        Calls send_state_request, send_mode_request etc.

        :param node_id: Integer Short Node ID
        :param command: Parameter or command to be sent
        :param value: Value, State, Mode
        """
        if command == 'State':
            self.send_state_request(node_id, value)
        elif command == 'Mode':
            self.send_mode_request(node_id, value)
        else:
            self._logger.error('Invalid Attribute Request')

    def send_type_request(self, node_id):
        """
        Send Type Request

        :param node_id: Integer Short Node ID
        """
        message = self.generate_type_request()
        addresses = self.node_id_to_addrs(node_id)
        self.send_message(message, *addresses)

    def send_state_request(self, node_id, state):
        """
        Send State Request

        :param node_id: Integer Short Node ID
        :param state:
        """
        message = self.generate_state_change_request(state)
        addresses = self.node_id_to_addrs(node_id)
        self.send_message(message, *addresses)

    def send_mode_request(self, node_id, mode):
        """
        Send Mode Request

        :param node_id: Integer Short Node ID
        :param mode:
        """
        message = self.generate_mode_change_request(mode)
        addresses = self.node_id_to_addrs(node_id)
        self.send_message(message, *addresses)

    def generate_active_endpoints_request(self, addr_short):
        """
        Generate Active Endpoints Request
        The active endpoint request needs the short address of the device
        in the payload. Remember, it needs to be little endian (backwards)
        The first byte in the payload is simply a number to identify the message
        the response will have the same number in it.
        See: http://ftp1.digi.com/support/images/APP_NOTE_XBee_ZigBee_Device_Profile.pdf

        Field Name       Size (bytes)   Description
        Network Address  2              16-bit address of a device in the network whose
                                        active endpoint list being requested.

        :param node_id:
        :param source_addr:
        """
        data = b'\xaa' + addr_short[1] + addr_short[0]
        message = {
            'description': 'Active Endpoints Request',
            'profile': self.ZDP_PROFILE_ID,
            'cluster': b'\x00\x05',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x00',
            'data': data
        }
        return message

    def generate_match_descriptor_response(self, rf_data):
        """
        Generate Match Descriptor Response
        If a descriptor match is found on the device, this response contains a list of endpoints that
        support the request criteria.

        Field Name       Size (bytes)   Description
        Status           1
        Network Address  2              Indicates the 16-bit address of the responding device.
        Length           1              The number of endpoints on the remote device that match
                                        the request criteria.
        Match List       Variable       List of endpoints on the remote that match the request criteria.

        :param node_id:
        :param received_message:
        """
        data = rf_data[0:1] + b'\x00\x00\x00\x01\x02'
        message = {
            'description': 'Match Descriptor Response',
            'profile': self.ZDP_PROFILE_ID,
            'cluster': b'\x80\x06',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x00',
            'data': data
        }
        return message

    def generate_state_change_request(self, state):
        """
        Generate Node State Change Request
        States:
            ON, OFF, CHECK

        :param state: Switch State
        :return: message
        """
        message = {
            'profile': self.ALERTME_PROFILE_ID,
            'cluster': b'\x00\xee',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02'
        }

        if state == 'ON':
            message['description'] = 'Switch Plug On'
            message['data'] = b'\x11\x00\x02\x01\x01'
        elif state == 'OFF':
            message['description'] = 'Switch Plug Off'
            message['data'] = b'\x11\x00\x02\x00\x01'
        elif state == 'CHECK':
            message['description'] = 'Switch State Request'
            message['data'] = b'\x11\x00\x01\x01'
        else:
            self._logger.error('Invalid state request %s', state)

        return message

    def generate_mode_change_request(self, mode):
        """
        Generate Mode Change Request
        Modes:
            NORMAL, RANGE, LOCKED, SILENT

        :param mode: Switch Mode
        :return: message
        """
        message = {
            'profile': self.ALERTME_PROFILE_ID,
            'cluster': b'\x00\xf0',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
        }

        if mode == 'NORMAL':
            message['description'] = 'Normal Mode'
            message['data'] = b'\x11\x00\xfa\x00\x01'
        elif mode == 'RANGE':
            message['description'] = 'Range Test'
            message['data'] = b'\x11\x00\xfa\x01\x01'
        elif mode == 'LOCKED':
            message['description'] = 'Locked Mode'
            message['data'] = b'\x11\x00\xfa\x02\x01'
        elif mode == 'SILENT':
            message['description'] = 'Silent Mode'
            message['data'] = b'\x11\x00\xfa\x03\x01'
        else:
            self._logger.error('Invalid mode request %s', mode)

        return message

    def generate_type_request(self):
        """
        Generate Node Type Request
            Version, Manufacturer, etc

        :return: Message
        """
        message = {
            'description': 'Version Request',
            'profile': self.ALERTME_PROFILE_ID,
            'cluster': b'\x00\xf6',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': b'\x11\x00\xfc\x00\x01'
        }
        return message

    def generate_hardware_join_1(self):
        """
        Generate Hardware Join 1

        """
        message = {
            'description': 'Hardware Join Messages 1',
            'profile': self.ALERTME_PROFILE_ID,
            'cluster': b'\x00\xf6',
            'src_endpoint': b'\x02',
            'dest_endpoint': b'\x02',
            'data': b'\x11\x01\xfc'
        }
        return message

    def generate_hardware_join_2(self):
        """
        Generate Hardware Join 2

        """
        message = {
            'description': 'Hardware Join Messages 2',
            'profile': self.ALERTME_PROFILE_ID,
            'cluster': b'\x00\xf0',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': b'\x19\x01\xfa\x00\x01'
        }
        return message

    def generate_security_init(self):
        """
        Generate Security Initialization

        """
        message = {
            'description': 'Security Initialization',
            'profile': self.ALERTME_PROFILE_ID,
            'cluster': b'\x05\x00',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': b'\x11\x80\x00\x00\x05'
        }
        return message

    def generate_missing_link(self, src_endpoint, dest_endpoint):
        """
        Generate 'Missing Link'

        :param src_endpoint: Note: This is the dest endpoint of the received message
        :param dest_endpoint: Note: This is the dest endpoint of the received message
        """
        message = {
            'description': 'Missing Link',
            'profile': self.ALERTME_PROFILE_ID,
            'cluster': b'\x00\xf0',
            'src_endpoint': src_endpoint,
            'dest_endpoint': dest_endpoint,
            'data': b'\x11\x39\xfd'
        }
        return message

    @staticmethod
    def parse_version_info(rf_data):
        """
        Process message, parse for version information:
        Type, Version, Manufacturer and Manufacturer Date

        :param rf_data: Message data
        :return: Parameter dict of version info
        """
        # The version string is variable length. We therefore have to calculate the
        # length of the string which we then use in the unpack
        l = len(rf_data) - 22
        values = dict(zip(
            ('cluster_cmd', 'hw_version', 'string'),
            struct.unpack('< 2x s H 17x %ds' % l, rf_data)
        ))

        # Break down the version string into its component parts
        ret = {}
        ret['Version'] = values['hw_version']
        ret['String']  = str(values['string'].decode())\
            .replace('\t', '\n')\
            .replace('\r', '\n')\
            .replace('\x0e', '\n')\
            .replace('\x0b', '\n')\
            .replace('\x06', '\n')\
            .replace('\x04', '\n') \
            .replace('\x12', '\n')

        ret['Manufacturer']    = ret['String'].split('\n')[0]
        ret['Type']            = ret['String'].split('\n')[1]
        ret['ManufactureDate'] = ret['String'].split('\n')[2]
        del ret['String']

        return ret

    @staticmethod
    def parse_range_info(rf_data):
        """
        Process message, parse for RSSI range test value

        :param rf_data: Message data
        :return: Parameter dict of RSSI value
        """
        values = dict(zip(
            ('cluster_cmd', 'RSSI'),
            struct.unpack('< 2x s B 1x', rf_data)
        ))
        rssi = values['RSSI']
        return {'RSSI' : rssi}

    @staticmethod
    def parse_power_demand(rf_data):
        """
        Process message, parse for power demand value.

        :param rf_data: Message data
        :return: Parameter dict of power value
        """
        values = dict(zip(
            ('cluster_cmd', 'powerDemand'),
            struct.unpack('< 2x s H', rf_data)
        ))

        return {'PowerDemand' : values['powerDemand']}

    @staticmethod
    def parse_power_consumption(rf_data):
        """
        Process message, parse for power consumption value.


        :param rf_data: Message data
        :return: Parameter dict of usage stats
        """
        ret = {}
        values = dict(zip(
            ('cluster_cmd', 'powerConsumption', 'upTime'),
            struct.unpack('< 2x s I I 1x', rf_data)
        ))
        ret['PowerConsumption'] = values['powerConsumption']
        ret['UpTime'] = values['upTime']

        return ret

    @staticmethod
    def parse_switch_state(rf_data):
        """
        Process message, parse for switch status

        :param rf_data: Message data
        :return: Parameter dict of switch status
        """
        values = struct.unpack('< 2x b b b', rf_data)
        if (values[2] & 0x01):
            return {'State': 'ON'}
        else:
            return {'State': 'OFF'}

    @staticmethod
    def parse_tamper_state(rf_data):
        """
        Process message, parse for Tamper Switch State Change

        :param rf_data: Message data
        :return: Parameter dict of tamper status
        """
        ret = {}
        if ord(rf_data[3]) == 0x02:
            ret['TamperSwitch'] = 'OPEN'
        else:
            ret['TamperSwitch'] = 'CLOSED'

        return ret

    @staticmethod
    def parse_button_press(rf_data):
        """
        Process message, parse for button press status

        :param rf_data: Message data
        :return: Parameter dict of button status
        """
        ret = {}
        if rf_data[2] == b'\x00':
            ret['State'] = 'OFF'
        elif rf_data[2] == b'\x01':
            ret['State'] = 'ON'

        ret['Counter'] = struct.unpack('<H', rf_data[5:7])[0]

        return ret

    @staticmethod
    def parse_security_state(rf_data):
        """
        Process message, parse for security state

        :param rf_data: Message data
        :return: Parameter dict of security state
        """
        ret = {}
        # The switch state is in byte [3] and is a bitfield
        # bit 0 is the magnetic reed switch state
        # bit 3 is the tamper switch state
        state = ord(rf_data[3])
        if (state & 0x01):
            ret['ReedSwitch']  = 'OPEN'
        else:
            ret['ReedSwitch']  = 'CLOSED'

        if (state & 0x04):
            ret['TamperSwitch'] = 'CLOSED'
        else:
            ret['TamperSwitch'] = 'OPEN'

        return ret

    @staticmethod
    def parse_status_update(rf_data):
        """
        Process message, parse for status update

        :param rf_data: Message data
        :return: Parameter dict of state
        """
        ret = {}
        status = rf_data[3]
        if (status == b'\x1c'):
            # Power Switch
            # Never found anything useful in this
            pass

        if (status == b'\x1d'):
            # Key Fob
            ret['Counter'] = struct.unpack('<I', rf_data[4:8])[0]

        if (status == b'\x1e') or (status == b'\x1f'):
            # Door Sensor
            if (ord(rf_data[-1]) & 0x01 == 1):
                ret['ReedSwitch']  = 'OPEN'
            else:
                ret['ReedSwitch']  = 'CLOSED'

            if (ord(rf_data[-1]) & 0x02 == 0):
                ret['TamperSwitch'] = 'OPEN'
            else:
                ret['TamperSwitch'] = 'CLOSED'

        if ((status == b'\x1f') or (status == b'\x1d')):
            # Door Sensor & Key Fob
            ret['TempFahrenheit'] = float(struct.unpack("<h", rf_data[8:10])[0]) / 100.0 * 1.8 + 32

        else:
            logging.error('Unrecognised Device Status %r', rf_data)

        return ret