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
        self.manu = 'AlertMe.com'
        self.type = 'Nano Hub'
        self.date = '2017-01-01'
        self.version = 1

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
        while time.time() < timeout:
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
        self._logger.debug('Updating Attributes: %s', attributes)
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
        self.nodes[node_id]['attributes'][attrib_name] = value

        if self._callback:
            self._callback(node_id, attrib_name, value)

    def get_node(self, node_id):
        """
        Given a Node ID return node.

        :param node_id: Integer Short Node ID
        :return: Node record
        """
        return self.nodes[node_id]

    def get_nodes(self):
        """
        Get Nodes

        :return: Dictionary of Nodes
        """
        return self.nodes

    def save_node_type(self, node_id, details):
        """
        Set Node Type

        :param node_id:
        :param details:
        """
        self._logger.debug('Setting Device Type to %s', details)
        for field, value in details.iteritems():
            self.nodes[node_id][field] = value

    def addrs_to_node_id(self, addr_long, addr_short):
        """
        Given a 48-bit Long Address and 16-bit Short Address lookup or generate new short integer Node ID.

        :param addr_long: 48-bits Long Address
        :param addr_short: 16-bit Short Address
        :return: Integer Short Node ID
        """
        node_id = Base.pretty_mac(addr_long)
        if node_id not in self.nodes:
            # Add to nodes list
            self.nodes[node_id] = {'addr_long': addr_long, 'addr_short': addr_short, 'attributes': {}}

        return node_id

    def node_id_to_addrs(self, node_id):
        """
        Given a Node ID return a tuple of 48-bit Long Address and 16-bit Short Address.
        This is typically used to pass addresses to send_message().

        :param node_id:  Integer Short Node ID
        :return: Tuple of long and short addresses
        """
        addr_long = self.nodes[node_id]['addr_long']
        addr_short = self.nodes[node_id]['addr_short']

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
            profile_id = message['profile']
            cluster_id = message['cluster']

            source_addr_long = message['source_addr_long']
            source_addr_short = message['source_addr']
            node_id = self.addrs_to_node_id(source_addr_long, source_addr_short)

            if (profile_id == self.ZDP_PROFILE_ID):
                # Zigbee Device Profile ID
                if (cluster_id == b'\x13'):
                    # Device Announce Message.
                    self._logger.debug('Received Device Announce Message')
                    # This will tell me the address of the new thing
                    # so we're going to send an active endpoint request
                    reply = self.generate_active_endpoints_request(source_addr_short)
                    self.send_message(reply, source_addr_long, source_addr_short)

                elif (cluster_id == b'\x00\x00'):
                    # Network (16-bit) Address Request.
                    self._logger.debug('Received Network (16-bit) Address Request')

                elif (cluster_id == b'\x80\x00'):
                    # Network (16-bit) Address Response.
                    # Not sure what this is? Only seen on the Hive ActivePlug?
                    # See: http://www.desert-home.com/2015/06/hacking-into-iris-door-sensor-part-4.html
                    # http://ftp1.digi.com/support/images/APP_NOTE_XBee_ZigBee_Device_Profile.pdf
                    self._logger.debug('Received Network (16-bit) Address Response')

                elif (cluster_id == b'\x00\x05'):
                    # Active Endpoint Request.
                    self._logger.debug('Received Active Endpoint Request')

                elif (cluster_id == b'\x80\x05'):
                    # Active Endpoint Response.
                    # This message tells us what the device can do, but it isn't constructed correctly to match what
                    # the switch can do according to the spec. This is another message that gets it's response after
                    # we receive the Match Descriptor below.
                    self._logger.debug('Received Active Endpoint Response')

                elif (cluster_id == b'\x00\x04'):
                    # Route Record Broadcast Response.
                    self._logger.debug('Received Simple Descriptor Request')

                elif (cluster_id == b'\x80\x38'):
                    self._logger.debug('Received Management Network Update Request')

                elif (cluster_id == b'\x802'):
                    # Route Record Broadcast Response.
                    self._logger.debug('Received Route Record Broadcast Response')

                elif (cluster_id == b'\x00\x06'):
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
                    self._logger.debug('Device should now be associated')

                else:
                    self._logger.error('Unrecognised Cluster ID: %e', cluster_id)

            elif (profile_id == self.ALERTME_PROFILE_ID):
                # AlertMe Profile ID

                # Python 2 / 3 hack
                if (hasattr(bytes(), 'encode')):
                    cluster_cmd = message['rf_data'][2]
                else:
                    cluster_cmd = bytes([message['rf_data'][2]])

                if (cluster_id == b'\x00\xee'):
                    if (cluster_cmd == b'\x80'):
                        properties = self.parse_switch_state(message['rf_data'])
                        self.save_node_attributes(node_id, properties)
                        self._logger.debug('Switch Status: %s', properties)

                    else:
                        self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                elif (cluster_id == b'\x00\xef'):
                    if (cluster_cmd == b'\x81'):
                        properties = self.parse_power_factor(message['rf_data'])
                        self.save_node_attributes(node_id, properties)
                        self._logger.debug('Current Instantaneous Power: %s', properties)

                    elif (cluster_cmd == b'\x82'):
                        properties = self.parse_power_consumption(message['rf_data'])
                        self.save_node_attributes(node_id, properties)
                        self._logger.debug('Uptime: %s Usage: %s', properties['UpTime'], properties['PowerConsumption'])

                    else:
                        self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                elif (cluster_id == b'\x00\xf0'):
                    if (cluster_cmd == b'\xfb'):
                        properties = self.parse_status_update(message['rf_data'])
                        self.save_node_attributes(node_id, properties)
                        self._logger.debug('Status Update: %s', properties)

                        # This may be the missing link to this thing?
                        self._logger.debug('Sending Missing Link')
                        reply = self.generate_missing_link(message['dest_endpoint'], message['source_endpoint'])
                        self.send_message(reply, source_addr_long, source_addr_short)

                    else:
                        self._logger.error('Unrecognised Cluster Cmd: %r', cluster_cmd)

                elif (cluster_id == b'\x00\xf2'):
                    properties = self.parse_tamper_state(message['rf_data'])
                    self.save_node_attributes(node_id, properties)
                    self._logger.debug('Tamper Switch Changed State: %s', properties)

                elif (cluster_id == b'\x00\xf3'):
                    properties = self.parse_button_press(message['rf_data'])
                    self.save_node_attributes(node_id, properties)
                    self._logger.debug('Button Press: %s', properties)

                elif (cluster_id == b'\x00\xf6'):
                    if (cluster_cmd == b'\xfd'):
                        properties = self.parse_range_info(message['rf_data'])
                        self.save_node_attributes(node_id, properties)
                        self._logger.debug('Range Test RSSI Value: %s', properties)

                    elif (cluster_cmd == b'\xfe'):
                        properties = self.parse_version_info(message['rf_data'])
                        self.save_node_type(node_id, properties)
                        self._logger.debug('Version Information: %s', properties)

                    else:
                        self._logger.error('Unrecognised Cluster Command: %e', cluster_cmd)

                elif (cluster_id == b'\x05\x00'):
                    self._logger.debug('Security Event')
                    # Security Cluster.
                    # When the device first connects, it comes up in a state that needs initialization, this command
                    # seems to take care of that. So, look at the value of the data and send the command.
                    if (message['rf_data'][3:7] == b'\x15\x00\x39\x10'):
                        reply = self.generate_security_init()
                        self.send_message(reply, source_addr_long, source_addr_short)

                    properties = self.parse_security_state(message['rf_data'])
                    self.save_node_attributes(node_id, properties)
                    self._logger.debug('Security Device Values: %s', properties)

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
    def parse_power_factor(rf_data):
        """
        Process message, parse for current instantaneous power value

        :param rf_data: Message data
        :return: Parameter dict of power value
        """
        values = dict(zip(
            ('cluster_cmd', 'Power'),
            struct.unpack('< 2x s H', rf_data)
        ))

        return {'PowerFactor' : values['Power']}

    @staticmethod
    def parse_power_consumption(rf_data):
        """
        Process message, parse for usage stats

        :param rf_data: Message data
        :return: Parameter dict of usage stats
        """
        ret = {}
        values = dict(zip(
            ('cluster_cmd', 'powerConsumption', 'upTime'),
            struct.unpack('< 2x s I I 1x', rf_data)
        ))
        ret['PowerConsumption'] = values['powerConsumption']
        ret['UpTime']           = values['upTime']

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
            logging.error('Unrecognised Device Status %s', rf_data)

        return ret

    @staticmethod
    def dict_factory(cursor, row):
        """
        Dict factory, used by SQLLite

        :param cursor:
        :param row:
        :return:
        """
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
