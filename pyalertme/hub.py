import logging
from pyalertme import *
from pyalertme.zigbee import *
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

        # Discovery thread and list of discovered nodes
        self._discovery_thread = threading.Thread(target=self._discovery)
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
            message = get_message('routing_table_request')
            self.send_message(message, BROADCAST_LONG, BROADCAST_SHORT)
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
        # If this address is me, don't add to nodes list and don't generate node_id,
        # also if we don't know what our own address is yet.
        if self.addr_long == addr_long or self.addr_long is None:
            return None

        # See if we already know about this device.
        addr_long_to_id = dict((addresses['AddressLong'], id) for id, addresses in self.nodes.iteritems())
        if addr_long in addr_long_to_id:
            node_id = addr_long_to_id[addr_long]
        else:
            # If not generate new node_id and add to list of known devices.
            node_id = Base.pretty_mac(addr_long)
            node_obj = Device()
            self.nodes[node_id] = {'AddressLong': addr_long, 'Attributes': {}, 'Obj': node_obj}

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

        # ZigBee Explicit Packets
        if message['id'] == 'rx_explicit':
            source_addr_long = message['source_addr_long']
            source_addr_short = message['source_addr']
            node_id = self.addr_long_to_node_id(source_addr_long)

            if node_id != None:
                self.nodes[node_id]['AddressLong'] = source_addr_long
                self.nodes[node_id]['AddressShort'] = source_addr_short

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
                            self.save_node_attributes(node_id, attributes)

                        else:
                            self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                    elif cluster_id == CLUSTER_ID_AM_POWER:
                        if cluster_cmd == CLUSTER_CMD_AM_PWR_DEMAND:
                            self._logger.debug('Received Power Demand Update')
                            attributes = parse_power_demand(message['rf_data'])
                            self.save_node_attributes(node_id, attributes)

                        elif cluster_cmd == CLUSTER_CMD_AM_PWR_CONSUMPTION:
                            self._logger.debug('Received Power Consumption & Uptime Update')
                            attributes = parse_power_consumption(message['rf_data'])
                            self.save_node_attributes(node_id, attributes)

                        elif cluster_cmd == CLUSTER_CMD_AM_PWR_UNKNOWN:
                            self._logger.debug('Unknown Power Update')
                            attributes = parse_power_unknown(message['rf_data'])
                            self.save_node_attributes(node_id, attributes)

                        else:
                            self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                    elif cluster_id == CLUSTER_ID_AM_STATUS:
                        if cluster_cmd == CLUSTER_CMD_AM_STATUS:
                            self._logger.debug('Received Status Update')
                            attributes = parse_status_update(message['rf_data'])
                            self.save_node_attributes(node_id, attributes)

                        else:
                            self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                    elif cluster_id == CLUSTER_ID_AM_TAMPER:
                        self._logger.debug('Received Tamper Switch Changed Update')
                        attributes = parse_tamper_state(message['rf_data'])
                        self.save_node_attributes(node_id, attributes)

                    elif cluster_id == CLUSTER_ID_AM_BUTTON:
                        self._logger.debug('Received Button Press Update')
                        attributes = parse_button_press(message['rf_data'])
                        self.save_node_attributes(node_id, attributes)

                    elif cluster_id == CLUSTER_ID_AM_DISCOVERY:
                        if cluster_cmd == CLUSTER_CMD_AM_RSSI:
                            self._logger.debug('Received RSSI Range Test Update')
                            attributes = parse_range_info_update(message['rf_data'])
                            self.save_node_attributes(node_id, attributes)

                        elif cluster_cmd == CLUSTER_CMD_AM_VERSION_RESP:
                            self._logger.debug('Received Version Information')
                            properties = parse_version_info_update(message['rf_data'])
                            self.save_node_properties(node_id, properties)

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
                        self.save_node_attributes(node_id, attributes)

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
            'Sequence':  170,
            'AddressShort': addr_short
        }
        return get_message('active_endpoints_request', params)

    def generate_match_descriptor_response(self, sequence):
        """
        Generate Match Descriptor Response.

        :param rf_data:
        """
        params = {
            'Sequence': 3, # sequence,
            'AddressShort': self.addr_short,
            'EndpointList': ENDPOINT_ALERTME
        }
        return get_message('match_descriptor_response', params)

    def generate_relay_state_request(self, state=''):
        """
        Generate Relay State Change Request.

        :param state: Switch Relay State
        :return: message
        """
        return get_message('switch_state_request', {'RelayState': state})

    def generate_mode_change_request(self, mode):
        """
        Generate Mode Change Request
        Available Modes: 'Normal', 'RangeTest', 'Locked', 'Silent'

        :param mode: Switch Mode
        :return: message
        """
        return get_message('mode_change_request', {'Mode': mode})

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











    def call_node_command(self, node_id, command, value):
        """
        Shortcut function to set node state, mode etc.
        Calls send_state_request, send_mode_request etc.

        :param node_id: Integer Short Node ID
        :param command: Parameter or command to be sent
        :param value: Value, State, Mode
        """
        if command == 'RelayState':
            self.send_relay_state_request(node_id, value)
        elif command == 'Mode':
            self.send_mode_request(node_id, value)
        else:
            self._logger.error('Invalid Attribute Request')

    def send_type_request(self, node_id):
        """
        Send Type Request

        :param node_id: Integer Short Node ID
        """
        message = self.generate_version_info_request()
        addresses = self.node_id_to_addrs(node_id)
        self.send_message(message, *addresses)

    def send_relay_state_request(self, node_id, state):
        """
        Send Relay State Request

        :param node_id: Integer Short Node ID
        :param state:
        """
        message = self.generate_relay_state_request(state)
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