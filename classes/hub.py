import pprint
import logging
from classes import *
import device
import struct
import time
import binascii
import threading
import sqlite3

pp = pprint.PrettyPrinter(indent=4)

class Hub(Base):

    def __init__(self, serialObj = False):
        Base.__init__(self, serialObj)

        # Type Info
        self.manu = 'AlertMe.com'
        self.type = 'Nano Hub'
        self.date = '2017-01-01'
        self.version = 00001

        # List of associated nodes
        self.addr_long_to_id = {}

    def command(self, node_id, attribute, value):
        # Lookup node
        nodes = self.list_nodes()

        # Work out Zigbee addresses
        dest_addr_long = nodes[node_id]['AddressLong']
        dest_addr_short = nodes[node_id]['AddressShort']

        # Basic message details
        message = {
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'profile': self.ALERTME_PROFILE_ID
        }

        # Construct message data
        if attribute == 'state':
            message['cluster'] = b'\x00\xee'
            if value == 'ON':
                message['data'] = b'\x11\x00\x02\x01\x01'
            if value == 'OFF':
                message['data'] = b'\x11\x00\x02\x00\x01'

        # Send message
        self.send_message(message, dest_addr_long, dest_addr_short)


    def set_node_attributes(self, node_id, attributes):
        for attribute, value in attributes.iteritems():
            self.set_node_attribute(node_id, attribute, value)

    def set_node_attribute(self, node_id, attribute, value):
        db = sqlite3.connect('nodes.db')
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO NodeAttribute (NodeId, Attribute, Value, Time) VALUES (:NodeId, :Attribute, :Value, CURRENT_TIMESTAMP)',
            {'NodeId': node_id, 'Attribute': attribute, 'Value': value}
        )
        db.commit()

    def set_node_name(self, node_id, name):
        db = sqlite3.connect('nodes.db')
        cursor = db.cursor()
        cursor.execute(
            'UPDATE Node SET Name = :Name WHERE Id = :NodeId',
            {'Name' : name, 'NodeId' : node_id}
        )
        db.commit()

    def set_node_type(self, node_id, details):
        db = sqlite3.connect('nodes.db')
        cursor = db.cursor()
        cursor.execute(
            'UPDATE Node SET Type = :Type, Version = :Version, Manufacturer = :Manufacturer, ManufactureDate = :ManufactureDate WHERE Id = :NodeId',
            {'Type': details['Type'], 'Version': details['Version'], 'Manufacturer': details['Manufacturer'], 'ManufactureDate': details['ManufactureDate'], 'NodeId': node_id}
        )
        self.logger.debug('Setting type to %s', details)
        db.commit()

    def get_node_type(self, node_id):

        # Lookup node
        nodes = self.list_nodes()

        # Work out Zigbee addresses
        dest_addr_long = nodes[node_id]['AddressLong']
        dest_addr_short = nodes[node_id]['AddressShort']

        self.logger.debug('Sending version req to %s', node_id)
        message = self.get_action('version_info')
        self.send_message(message, dest_addr_long, dest_addr_short)

    def list_nodes(self):
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d

        db = sqlite3.connect('nodes.db')
        db.text_factory = str
        db.row_factory = dict_factory
        cursor = db.cursor()
        cursor.execute('SELECT * FROM Node')

        nodes = {}
        for node in cursor.fetchall():
            nodes[node['Id']] = node
            cursor.execute(
                'SELECT a.Id, a.Attribute, a.Value, a.Time FROM NodeAttribute a JOIN (SELECT MAX(Id) AS Id FROM NodeAttribute GROUP BY Attribute) b ON a.Id = b.id AND a.NodeId = :NodeId',
                {'NodeId' : node['Id']}
            )
            nodes[node['Id']]['Attributes'] = cursor.fetchall()

        return nodes

    def lookup_node_id(self, addr_long):
        db = sqlite3.connect('nodes.db')
        db.text_factory = lambda x: unicode(x, 'utf-8', 'ignore')
        cursor = db.cursor()

        # Lookup in local cache
        if addr_long in self.addr_long_to_id:
            node_id = self.addr_long_to_id[addr_long]

        else:
            # Lookup in DB
            cursor.execute('SELECT Id FROM Node WHERE AddressLong = :AddrLong', {'AddrLong': addr_long})
            row = cursor.fetchone()

            if row is not None:
                node_id = row[0]
            else:
                # Create in DB
                cursor.execute(
                    'INSERT INTO Node (AddressLong, Name, FirstSeen, LastSeen) VALUES (:AddrLong, :Name, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
                    {'AddrLong': addr_long, 'Name': 'Unnamed Device'}
                )
                node_id = cursor.lastrowid
                db.commit()

            # Add to local cache
            self.addr_long_to_id[addr_long] = node_id

        return node_id

    def process_message(self, message):
        super(Hub, self).process_message(message)

        # We are only interested in Zigbee Explicit packets.
        if message['id'] == 'rx_explicit':
            profile_id = message['profile']
            cluster_id = message['cluster']

            source_addr_long = message['source_addr_long']
            source_addr = message['source_addr']
            node_id = self.lookup_node_id(source_addr_long)

            # Increment packet counter
            db = sqlite3.connect('nodes.db')
            cursor = db.cursor()
            cursor.execute(
                'UPDATE Node SET LastSeen = CURRENT_TIMESTAMP, MessagesReceived = MessagesReceived + 1 WHERE Id = :NodeId',
                {'NodeId': node_id}
            )
            db.commit()

            if (profile_id == self.ZDP_PROFILE_ID):
                # Zigbee Device Profile ID
                if (cluster_id == b'\x13'):
                    # Device Announce Message.
                    # Due to timing problems with the switch itself, we don't
                    # respond to this message, we save the response for later after the
                    # Match Descriptor request comes in. You'll see it down below.
                    self.logger.debug('Received Device Announce Message')

                elif (cluster_id == b'\x80\x00'):
                    # Possibly Network (16-bit) Address Response.
                    # Not sure what this is? Only seen on the Hive ActivePlug?
                    # See: http://www.desert-home.com/2015/06/hacking-into-iris-door-sensor-part-4.html
                    # http://ftp1.digi.com/support/images/APP_NOTE_XBee_ZigBee_Device_Profile.pdf
                    self.logger.debug('Received Network (16-bit) Address Response')

                elif (cluster_id == b'\x80\x05'):
                    # Active Endpoint Response.
                    # This message tells us what the device can do, but it isn't constructed correctly to match what
                    # the switch can do according to the spec. This is another message that gets it's response after
                    # we receive the Match Descriptor below.
                    self.logger.debug('Received Active Endpoint Response')

                elif (cluster_id == b'\x802'):
                    # Route Record Broadcast Response.
                    self.logger.debug('Received Route Record Broadcast Response')

                elif (cluster_id == b'\x00\x06'):
                    # Match Descriptor Request.
                    self.logger.debug('Received Match Descriptor Request')
                    # This is the point where we finally respond to the switch. Several messages are sent to cause
                    # the switch to join with the controller at a network level and to cause it to regard this
                    # controller as valid.

                    # First send the Active Endpoint Request
                    reply = self.get_action('active_endpoints_request')
                    self.send_message(reply, source_addr_long, source_addr)
                    self.logger.debug('Sent Active Endpoints Request')

                    # Now send the Match Descriptor Response
                    reply = self.get_action('match_descriptor_response')
                    self.send_message(reply, source_addr_long, source_addr)
                    self.logger.debug('Sent Match Descriptor Response')

                    # Now there are two messages directed at the hardware code (rather than the network code).
                    # The switch has to receive both of these to stay joined.
                    reply = self.get_action('hardware_join_1')
                    self.send_message(reply, source_addr_long, source_addr)
                    reply = self.get_action('hardware_join_2')
                    self.send_message(reply, source_addr_long, source_addr)
                    self.logger.debug('Sent Hardware Join Messages')

                    # We are fully associated!
                    self.logger.debug('Device Associated')

                else:
                    self.logger.error('Unrecognised Cluster ID: %e', cluster_id)

            elif (profile_id == self.ALERTME_PROFILE_ID):
                # AlertMe Profile ID

                # Python 2 / 3 hack
                if (hasattr(bytes(), 'encode')):
                    cluster_cmd = message['rf_data'][2]
                else:
                    cluster_cmd = bytes([message['rf_data'][2]])

                if (cluster_id == b'\x00\xee'):
                    if (cluster_cmd == b'\x80'):
                        properties = self.parse_switch_status(message['rf_data'])
                        self.logger.debug('Switch Status: %s', properties)
                        self.set_node_attributes(node_id, properties)
                    else:
                        self.logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                elif (cluster_id == b'\x00\xef'):
                    if (cluster_cmd == b'\x81'):
                        properties = self.parse_power_info(message['rf_data'])
                        self.logger.debug('Current Instantaneous Power: %s', properties)
                        self.set_node_attributes(node_id, properties)
                    elif (cluster_cmd == b'\x82'):
                        properties = self.parse_usage_info(message['rf_data'])
                        self.logger.debug('Uptime: %s Usage: %s', properties['upTime'], properties['powerConsumption'])
                        self.set_node_attributes(node_id, properties)
                    else:
                        self.logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                elif (cluster_id == b'\x00\xf0'):
                    if (cluster_cmd == b'\xfb'):
                        properties = self.parse_status_update(message['rf_data'])
                        self.logger.debug('Status Update: %s', properties)
                        # self.set_node_attributes(node_id, properties)
                    else:
                        self.logger.error('Unrecognised Cluster Cmd: %r', cluster_cmd)

                elif (cluster_id == b'\x00\xf2'):
                    properties = self.parse_tamper(message['rf_data'])
                    self.logger.debug('Tamper Switch Changed State: %s', properties)
                    self.set_node_attributes(node_id, properties)

                elif (cluster_id == b'\x00\xf3'):
                    properties = self.parse_button_press(message['rf_data'])
                    self.logger.debug('Button Press: %s', properties)
                    self.set_node_attributes(node_id, properties)

                elif (cluster_id == b'\x00\xf6'):
                    if (cluster_cmd == b'\xfd'):
                        properties = self.parse_range_info(message['rf_data'])
                        self.logger.debug('Range Test RSSI Value: %s', properties)
                        self.set_node_attributes(node_id, properties)

                    elif (cluster_cmd == b'\xfe'):
                        properties = self.parse_version_info(message['rf_data'])
                        self.logger.debug('Version Information: %s', properties)
                        self.set_node_attributes(node_id, properties)
                        self.set_node_type(node_id, properties)

                    else:
                        self.logger.error('Unrecognised Cluster Command: %e', cluster_cmd)

                elif (cluster_id == b'\x05\x00'):
                    self.logger.debug('Security Event')
                    # Security Cluster.
                    # When the device first connects, it come up in a state that needs initialization, this command
                    # seems to take care of that. So, look at the value of the data and send the command.
                    if (message['rf_data'][3:7] == b'\x15\x00\x39\x10'):
                        self.logger.debug('Sending Security Initialization')
                        reply = self.get_action('security_initialization')
                        self.send_message(reply, source_addr_long, source_addr)

                    vals = self.parse_security_device(message['rf_data'])
                    self.logger.debug('Security Device Values: %s', vals)

                else:
                    self.logger.error('Unrecognised Cluster ID: %r', cluster_id)

            else:
                self.logger.error('Unrecognised Profile ID: %r', profile_id)

    def discovery(self):
        self.logger.debug('Discovery')
        self.thread = threading.Thread(target=self._discovery)

    def _discovery(self):
        # First, send out a broadcast every 3 seconds for 30 seconds
        timeout = time.time() + 30
        i=1
        while True:
            if time.time() > timeout:
                break
            self.logger.debug('Sending discover # %s', i)
            message = self.get_action('routing_table_request')
            self.send_message(message, self.BROADCAST_LONG, self.BROADCAST_SHORT)
            time.sleep(3.00)
            i = i+1

        # Next, sent out a version request to each node we have discovered above
        nodes = self.list_nodes()
        message = self.get_action('version_info')
        for id, node in nodes.iteritems():
            self.logger.debug('Sending version req to %s', id)
            self.send_message(message, node['AddressLong'], node['AddressShort'])
            time.sleep(1.00)


    @staticmethod
    def parse_version_info(rf_data):
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
            .replace('\x0b', '\n') \
            .replace('\x06', '\n')

        ret['Manufacturer']    = ret['String'].split('\n')[0]
        ret['Type']            = ret['String'].split('\n')[1]
        ret['ManufactureDate'] = ret['String'].split('\n')[2]
        del ret['String']

        return ret

    @staticmethod
    def parse_range_info(rf_data):
        # Parse for RSSI Range Test value
        values = dict(zip(
            ('cluster_cmd', 'RSSI'),
            struct.unpack('< 2x s B 1x', rf_data)
        ))
        rssi = values['RSSI']
        return {'RSSI' : rssi}

    @staticmethod
    def parse_power_info(rf_data):
        # Parse for Current Instantaneous Power value
        values = dict(zip(
            ('cluster_cmd', 'Power'),
            struct.unpack('< 2x s H', rf_data)
        ))
        return {'instantaneousPower' : values['Power']}

    @staticmethod
    def parse_usage_info(rf_data):
        # Parse Usage Stats
        ret = {}
        values = dict(zip(
            ('cluster_cmd', 'powerConsumption', 'upTime'),
            struct.unpack('< 2x s I I 1x', rf_data)
        ))
        ret['powerConsumption'] = values['powerConsumption']
        ret['upTime']           = values['upTime']

        return ret

    @staticmethod
    def parse_switch_status(rf_data):
        # Parse Switch Status
        values = struct.unpack('< 2x b b b', rf_data)
        if (values[2] & 0x01):
            return {'state' : 'ON'}
        else:
            return {'state' : 'OFF'}

    @staticmethod
    def parse_button_press(rf_data):
        ret = {}
        if rf_data[2] == b'\x00':
            ret['state'] = 'OFF'
        elif rf_data[2] == b'\x01':
            ret['state'] = 'ON'
        else:
            ret['state'] = {}

        ret['counter'] = struct.unpack('<H', rf_data[5:7])[0]

        return ret

    @staticmethod
    def parse_status_update(rf_data):
        ret = {}
        status = rf_data[3]
        if (status == b'\x1c'):
            # Power Switch
            ret['Type'] = 'Power Switch'
            # Never found anything useful in this

        elif (status == b'\x1d'):
            # Key Fob
            ret['Type'] = 'Key Fob'
            ret['Temp_F']  = float(struct.unpack("<h", rf_data[8:10])[0]) / 100.0 * 1.8 + 32
            ret['Counter'] = struct.unpack('<I', rf_data[4:8])[0]

        elif (status == b'\x1e') or (status == b'\x1f'):
            # Door Sensor
            ret['Type'] = 'Door Sensor'
            if (ord(rf_data[-1]) & 0x01 == 1):
                ret['ReedSwitch']  = 'open'
            else:
                ret['ReedSwitch']  = 'closed'

            if (ord(rf_data[-1]) & 0x02 == 0):
                ret['TamperSwith'] = 'open'
            else:
                ret['TamperSwith'] = 'closed'

            if (status == b'\x1f'):
                ret['Temp_F']      = float(struct.unpack("<h", rf_data[8:10])[0]) / 100.0 * 1.8 + 32
            else:
                ret['Temp_F']      = None

        else:
            logging.error('Unrecognised Device Status')

        return ret

    @staticmethod
    def parse_security_device(rf_data):
        # The switch state is in byte [3] and is a bitfield
        # bit 0 is the magnetic reed switch state
        # bit 3 is the tamper switch state
        ret = {}
        switchState = ord(rf_data[3])
        if (switchState & 0x01):
            ret['ReedSwitch']  = 'open'
        else:
            ret['ReedSwitch']  = 'closed'

        if (switchState & 0x04):
            ret['TamperSwith'] = 'closed'
        else:
            ret['TamperSwith'] = 'open'

        return ret

    @staticmethod
    def parse_tamper(rf_data):
        # Parse Tamper Switch State Change
        ret = {}
        if ord(rf_data[3]) == 0x02:
            ret['TamperSwith'] = 'open'
        else:
            ret['TamperSwith'] = 'closed'

        return ret

