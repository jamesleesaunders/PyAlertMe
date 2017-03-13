import logging
from pyalertme import *
import struct
import time
import binascii
import threading
import sqlite3

class Hub(Base):

    def __init__(self, callback = False):
        Base.__init__(self)

        # Type Info
        self.manu = 'AlertMe.com'
        self.type = 'Nano Hub'
        self.date = '2017-01-01'
        self.version = 00001
        self.discovery_thread = threading.Thread(target=self._discovery)
        self.callback = callback

        self.db = sqlite3.connect('nodes.db', check_same_thread=False)
        self.db.text_factory = str
        self.db.row_factory = self.dict_factory
        self.cursor = self.db.cursor()

        # List of associated nodes
        self.addr_long_to_id = {}

    def discovery(self):
        self.logger.debug('Discovery Mode Started')
        self.discovery_thread.start()

    def _discovery(self):
        # First, send out a broadcast every 2 seconds for 30 seconds
        timeout = time.time() + 30
        i = 1
        while time.time() < timeout:
            self.logger.debug('Sending Discovery Request #%s', i)
            message = self.get_action('routing_table_request')
            self.send_message(message, self.BROADCAST_LONG, self.BROADCAST_SHORT)
            i += 1
            time.sleep(2.00)

        # Next, sent out a version request to each node we have discovered above
        nodes = self.get_nodes()
        for node_id in nodes.keys():
            self.send_type_request(node_id)
            time.sleep(1.00)

    def get_node(self, node_id):
        nodes = self.get_nodes()
        return nodes[node_id]

    def get_nodes(self):
        nodes = {}
        self.cursor.execute(
            'SELECT Id, Name, AddressLong, AddressShort, Type, Version, Manufacturer, ManufactureDate, FirstSeen, LastSeen, MessagesReceived FROM Nodes'
        )
        for node in self.cursor.fetchall():
            node_id = node['Id']
            nodes[node_id] = node
            nodes[node_id]['Attributes'] = self.get_node_attributes_latest(node_id)

        return nodes

    def get_node_attributes_latest(self, node_id):
        attributes = {}
        self.cursor.execute(
            'SELECT a.Id, a.Name, a.Value, a.Time FROM Attributes a JOIN (SELECT MAX(Id) AS Id FROM Attributes WHERE NodeId = :NodeId1 GROUP BY Name) b ON a.Id = b.Id AND a.NodeId = :NodeId2',
            {'NodeId1': node_id, 'NodeId2': node_id}
        )
        for attribute in self.cursor.fetchall():
            attrib_name = attribute['Name']
            value = attribute['Value']
            time = attribute['Time']
            attributes[attrib_name] = {'ReportedValue': value, 'ReportReceivedTime': time}

        return attributes

    def get_node_attribute_history(self, node_id, attrib_name, starttime, endtime):
        history = {
            attrib_name: {
                'NodeId': node_id,
                'StartTime': starttime,
                'EndTime': endtime,
                'Values': {}
            }
        }
        self.cursor.execute(
            'SELECT * FROM Attributes WHERE NodeId = :NodeId AND Name = :Name AND Time BETWEEN DATETIME(:StartTime, \'unixepoch\', \'localtime\') AND DATETIME(:EndTime, \'unixepoch\', \'localtime\')',
            {'NodeId': node_id, 'Name': attrib_name, 'StartTime': starttime, 'EndTime': endtime}
        )
        for attribute in self.cursor.fetchall():
            value = attribute['Value']
            time = attribute['Time']
            history[attrib_name]['Values'][time] = value

        return history

    def lookup_node_id(self, addr_long, addr_short):
        # Lookup in local cache
        if addr_long in self.addr_long_to_id:
            node_id = self.addr_long_to_id[addr_long]

        else:
            # Lookup in DB
            self.cursor.execute('SELECT Id FROM Nodes WHERE AddressLong = :AddrLong LIMIT 1', {'AddrLong': addr_long})
            row = self.cursor.fetchone()

            if row is not None:
                self.logger.debug('Row %s', row)
                node_id = row['Id']

            else:
                # Create in DB
                self.cursor.execute(
                    'INSERT INTO Nodes (AddressLong, Name, Type, FirstSeen, LastSeen) VALUES (:AddressLong, :Name, :Type, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)',
                    {'AddressLong': addr_long, 'Name': 'Unspecified', 'Type': 'Unknown'}
                )
                node_id = self.cursor.lastrowid
                self.db.commit()

            # Ensure we also have saved the latest short address
            self.set_node_short_address(node_id, addr_short)

            # Add to local cache
            self.addr_long_to_id[addr_long] = node_id

        return node_id

    def set_node_type(self, node_id, details):
        self.logger.debug('Setting Device Type to %s', details)
        self.db.execute(
            'UPDATE Nodes SET Type = :Type, Version = :Version, Manufacturer = :Manufacturer, ManufactureDate = :ManufactureDate WHERE Id = :NodeId',
            {'Type': details['Type'], 'Version': details['Version'], 'Manufacturer': details['Manufacturer'], 'ManufactureDate': details['ManufactureDate'], 'NodeId': node_id}
        )
        self.db.commit()

    def send_type_request(self, node_id):
        # Lookup node
        node = self.get_node(node_id)

        # Work out Zigbee addresses
        dest_addr_long = node['AddressLong']
        dest_addr_short = node['AddressShort']

        self.logger.debug('Sending Version Request to %s', node_id)
        message = self.get_action('version_info')
        self.send_message(message, dest_addr_long, dest_addr_short)

    def send_state_request(self, node_id, state):
        # Lookup node
        node = self.get_node(node_id)

        # Work out Zigbee addresses
        dest_addr_long = node['AddressLong']
        dest_addr_short = node['AddressShort']

        # Basic message details
        message = {
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'profile': self.ALERTME_PROFILE_ID,
            'cluster': b'\x00\xee'
        }

        if state == 'ON':
            message['data'] = b'\x11\x00\x02\x01\x01'
        elif state == 'OFF':
            message['data'] = b'\x11\x00\x02\x00\x01'
        elif state == 'CHECK':
            message['data'] = b'\x11\x00\x01\x01'
        else:
            self.logger.error('Invalid state request %s', state)

        # Send message
        self.send_message(message, dest_addr_long, dest_addr_short)

    def set_node_attributes(self, node_id, attributes):
        self.logger.error('Updating Attributes: %s', attributes)
        for attrib_name, value in attributes.iteritems():
            self.set_node_attribute(node_id, attrib_name, value)

    def set_node_attribute(self, node_id, attrib_name, value):
        if self.callback:
            self.callback(attrib_name, value)

        self.db.execute(
            'INSERT INTO Attributes (NodeId, Name, Value, Time) VALUES (:NodeId, :Name, :Value, CURRENT_TIMESTAMP)',
            {'NodeId': node_id, 'Name': attrib_name, 'Value': value}
        )
        self.db.commit()

    def set_node_short_address(self, node_id, addr_short):
        self.db.execute(
            'UPDATE Nodes SET AddressShort = :AddressShort WHERE Id = :NodeId',
            {'AddressShort': addr_short, 'NodeId': node_id}
        )
        self.db.commit()

    def set_node_name(self, node_id, name):
        self.db.execute(
            'UPDATE Nodes SET Name = :Name WHERE Id = :NodeId',
            {'Name': name, 'NodeId': node_id}
        )
        self.db.commit()

    def update_packet_counter(self, node_id):
        self.db.execute(
            'UPDATE Nodes SET LastSeen = CURRENT_TIMESTAMP, MessagesReceived = MessagesReceived + 1 WHERE Id = :NodeId',
            {'NodeId': node_id}
        )
        self.db.commit()

    def process_message(self, message):
        super(Hub, self).process_message(message)

        # We are only interested in Zigbee Explicit packets.
        if message['id'] == 'rx_explicit':
            profile_id = message['profile']
            cluster_id = message['cluster']

            source_addr_long = message['source_addr_long']
            source_addr = message['source_addr']
            node_id = self.lookup_node_id(source_addr_long, source_addr)
            # node_id = 1
            self.update_packet_counter(node_id)

            if (profile_id == self.ZDP_PROFILE_ID):
                # Zigbee Device Profile ID
                if (cluster_id == b'\x13'):
                    # Device Announce Message.
                    self.logger.debug('Received Device Announce Message')
                    # This will tell me the address of the new thing
                    # so I'm going to send an active endpoint request
                    self.logger.debug('Sending Active Endpoint Request')
                    epc = '\xaa'+message['source_addr'][1]+message['source_addr'][0]
                    self.zb.send('tx_explicit',
                        dest_addr_long = source_addr_long,
                        dest_addr = source_addr,
                        src_endpoint = '\x00',
                        dest_endpoint = '\x00',
                        cluster = '\x00\x05',
                        profile = self.HA_PROFILE_ID,
                        options = '\x01',
                        data = epc
                    )

                elif (cluster_id == b'\x00\x00'):
                    # Network (16-bit) Address Request.
                    self.logger.debug('Received Network (16-bit) Address Request')

                elif (cluster_id == b'\x80\x00'):
                    # Network (16-bit) Address Response.
                    # Not sure what this is? Only seen on the Hive ActivePlug?
                    # See: http://www.desert-home.com/2015/06/hacking-into-iris-door-sensor-part-4.html
                    # http://ftp1.digi.com/support/images/APP_NOTE_XBee_ZigBee_Device_Profile.pdf
                    self.logger.debug('Received Network (16-bit) Address Response')

                elif (cluster_id == b'\x00\x05'):
                    # Active Endpoint Request.
                    self.logger.debug('Received Active Endpoint Request')

                elif (cluster_id == b'\x80\x05'):
                    # Active Endpoint Response.
                    # This message tells us what the device can do, but it isn't constructed correctly to match what
                    # the switch can do according to the spec. This is another message that gets it's response after
                    # we receive the Match Descriptor below.
                    self.logger.debug('Received Active Endpoint Response')

                elif (cluster_id == b'\x00\x04'):
                    # Route Record Broadcast Response.
                    self.logger.debug('Simple Descriptor Request')

                elif (cluster_id == b'\x80\x38'):
                    self.logger.debug('Management Network Update Request')

                elif (cluster_id == b'\x802'):
                    # Route Record Broadcast Response.
                    self.logger.debug('Received Route Record Broadcast Response')

                elif (cluster_id == b'\x00\x06'):
                    # Match Descriptor Request.
                    self.logger.debug('Received Match Descriptor Request')
                    # This is the point where we finally respond to the switch. Several messages are sent to cause
                    # the switch to join with the controller at a network level and to cause it to regard this
                    # controller as valid.

                    # First send the Match Descriptor Response
                    # message = self.get_action('match_descriptor_response')
                    # self.send_message(message, source_addr_long, source_addr)
                    self.zb.send('tx_explicit',
                        dest_addr_long = source_addr_long,
                        dest_addr = source_addr,
                        src_endpoint = '\x00',
                        dest_endpoint = '\x00',
                        cluster = '\x80\x06',
                        profile = self.HA_PROFILE_ID,
                        options = '\x01',
                        data = message['rf_data'][0:1] + '\x00\x00\x00\x01\x02'
                    )
                    self.logger.debug('Sent Match Descriptor Response')
                    time.sleep(2)

                    # Now there are two messages directed at the hardware code (rather than the network code).
                    # The switch has to receive both of these to stay joined.
                    message = self.get_action('hardware_join_1')
                    self.send_message(message, source_addr_long, source_addr)
                    # message = self.get_action('hardware_join_2')
                    # self.send_message(message, source_addr_long, source_addr)
                    self.logger.debug('Sent Hardware Join Message(s)')

                    # We are fully associated!
                    self.logger.debug('Device should now be Associated')

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
                        properties = self.parse_switch_state(message['rf_data'])
                        self.set_node_attributes(node_id, properties)
                        self.logger.debug('Switch Status: %s', properties)

                    else:
                        self.logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                elif (cluster_id == b'\x00\xef'):
                    if (cluster_cmd == b'\x81'):
                        properties = self.parse_power_factor(message['rf_data'])
                        self.set_node_attributes(node_id, properties)
                        self.logger.debug('Current Instantaneous Power: %s', properties)

                    elif (cluster_cmd == b'\x82'):
                        properties = self.parse_power_consumption(message['rf_data'])
                        self.set_node_attributes(node_id, properties)
                        self.logger.debug('Uptime: %s Usage: %s', properties['UpTime'], properties['PowerConsumption'])

                    else:
                        self.logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                elif (cluster_id == b'\x00\xf0'):
                    if (cluster_cmd == b'\xfb'):
                        properties = self.parse_status_update(message['rf_data'])
                        self.set_node_attributes(node_id, properties)
                        self.logger.debug('Status Update: %s', properties)

                        # This may be the missing link to this thing
                        self.logger.debug('Sending Missing Link')
                        self.zb.send('tx_explicit',
                            dest_addr_long = source_addr_long,
                            dest_addr = source_addr,
                            src_endpoint = message['dest_endpoint'],
                            dest_endpoint = message['source_endpoint'],
                            cluster = '\x00\xf0',
                            profile = self.ALERTME_PROFILE_ID,
                            data = '\x11\x39\xfd'
                        )

                    else:
                        self.logger.error('Unrecognised Cluster Cmd: %r', cluster_cmd)

                elif (cluster_id == b'\x00\xf2'):
                    properties = self.parse_tamper_state(message['rf_data'])
                    self.set_node_attributes(node_id, properties)
                    self.logger.debug('Tamper Switch Changed State: %s', properties)

                elif (cluster_id == b'\x00\xf3'):
                    properties = self.parse_button_press(message['rf_data'])
                    self.set_node_attributes(node_id, properties)
                    self.logger.debug('Button Press: %s', properties)

                elif (cluster_id == b'\x00\xf6'):
                    if (cluster_cmd == b'\xfd'):
                        properties = self.parse_range_info(message['rf_data'])
                        self.set_node_attributes(node_id, properties)
                        self.logger.debug('Range Test RSSI Value: %s', properties)

                    elif (cluster_cmd == b'\xfe'):
                        properties = self.parse_version_info(message['rf_data'])
                        self.set_node_type(node_id, properties)
                        self.logger.debug('Version Information: %s', properties)

                    else:
                        self.logger.error('Unrecognised Cluster Command: %e', cluster_cmd)

                elif (cluster_id == b'\x05\x00'):
                    self.logger.debug('Security Event')
                    # Security Cluster.
                    # When the device first connects, it come up in a state that needs initialization, this command
                    # seems to take care of that. So, look at the value of the data and send the command.
                    if (message['rf_data'][3:7] == b'\x15\x00\x39\x10'):
                        self.logger.debug('Sending Security Initialization')
                        message = self.get_action('security_initialization')
                        self.send_message(message, source_addr_long, source_addr)

                    properties = self.parse_security_state(message['rf_data'])
                    self.set_node_attributes(node_id, properties)
                    self.logger.debug('Security Device Values: %s', properties)

                else:
                    self.logger.error('Unrecognised Cluster ID: %r', cluster_id)

            else:
                self.logger.error('Unrecognised Profile ID: %r', profile_id)



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
        # Parse for RSSI Range Test value
        values = dict(zip(
            ('cluster_cmd', 'RSSI'),
            struct.unpack('< 2x s B 1x', rf_data)
        ))
        rssi = values['RSSI']
        return {'RSSI' : rssi}

    @staticmethod
    def parse_power_factor(rf_data):
        # Parse for current Instantaneous Power value
        values = dict(zip(
            ('cluster_cmd', 'Power'),
            struct.unpack('< 2x s H', rf_data)
        ))

        return {'PowerFactor' : values['Power']}

    @staticmethod
    def parse_power_consumption(rf_data):
        # Parse Usage Stats
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
        # Parse Switch Status
        values = struct.unpack('< 2x b b b', rf_data)
        if (values[2] & 0x01):
            return {'State': 'ON'}
        else:
            return {'State': 'OFF'}

    @staticmethod
    def parse_tamper_state(rf_data):
        # Parse Tamper Switch State Change
        ret = {}
        if ord(rf_data[3]) == 0x02:
            ret['TamperSwitch'] = 'OPEN'
        else:
            ret['TamperSwitch'] = 'CLOSED'

        return ret

    @staticmethod
    def parse_button_press(rf_data):
        ret = {}
        if rf_data[2] == b'\x00':
            ret['State'] = 'OFF'
        elif rf_data[2] == b'\x01':
            ret['State'] = 'ON'

        ret['Counter'] = struct.unpack('<H', rf_data[5:7])[0]

        return ret

    @staticmethod
    def parse_security_state(rf_data):
        # The switch state is in byte [3] and is a bitfield
        # bit 0 is the magnetic reed switch state
        # bit 3 is the tamper switch state
        ret = {}
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
            logging.error('Unrecognised Device Status')

        return ret

    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d