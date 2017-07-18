from pyalertme.node import Node
import time
import threading
from xbee import ZigBee
import copy
import struct

# ZigBee Addressing
BROADCAST_LONG = b'\x00\x00\x00\x00\x00\x00\xff\xff'
BROADCAST_SHORT = b'\xff\xfd'

# ZigBee Profile IDs
PROFILE_ID_ZDP = b'\x00\x00'  # ZigBee Device Profile
PROFILE_ID_HA = b'\x01\x04'  # HA Device Profile
PROFILE_ID_LL = b'\xc0\x5e'  # Light Link Profile
PROFILE_ID_ALERTME = b'\xc2\x16'  # AlertMe Private Profile

# ZigBee Endpoints
ENDPOINT_ZDO = b'\x00'  # ZigBee Device Objects Endpoint
ENDPOINT_ALERTME = b'\x02'  # AlertMe / Iris Endpoint

# ZDP Status
ZDP_STATUS_OK = b'\x00'
ZDP_STATUS_INVALID = b'\x80'
ZDP_STATUS_NOT_FOUND = b'\x81'

# ZDO Clusters
# See:
#    http://ftp1.digi.com/support/images/APP_NOTE_XBee_ZigBee_Device_Profile.pdf
#    http://www.cel.com/pdf/misc/zic09_zdp_api.pdf
CLUSTER_ID_ZDO_NWK_ADDR_REQ = b'\x00\x00'  # Network (16-bit) Address Request
CLUSTER_ID_ZDO_NWK_ADDR_RSP = b'\x80\x00'  # Network (16-bit) Address Response
CLUSTER_ID_ZDO_SIMPLE_DESC_REQ = b'\x00\x04'  # Simple Descriptor Request
CLUSTER_ID_ZDO_ACTIVE_EP_REQ = b'\x00\x05'  # Active Endpoints Request
CLUSTER_ID_ZDO_ACTIVE_EP_RSP = b'\x80\x05'  # Active Endpoints Response
CLUSTER_ID_ZDO_MATCH_DESC_REQ = b'\x00\x06'  # Match Descriptor Request
CLUSTER_ID_ZDO_MATCH_DESC_RSP = b'\x80\x06'  # Match Descriptor Response
CLUSTER_ID_ZDO_END_DEVICE_ANNCE = b'\x00\x13'  # End Device Announce
CLUSTER_ID_ZDO_MGMT_RTG_REQ = b'\x00\x32'  # Management Routing Request
CLUSTER_ID_ZDO_MGMT_RTG_RSP = b'\x80\x32'  # Management Routing Response
CLUSTER_ID_ZDO_MGMT_PERMIT_JOIN_REQ = b'\x00\x36'  # Permit Join Request Request
CLUSTER_ID_ZDO_MGMT_NETWORK_UPDATE = b'\x80\x38'  # Management Network Update

# AlertMe Clusters
# See:
#    http://www.desert-home.com/2015/06/hacking-into-iris-door-sensor-part-4.html
CLUSTER_ID_AM_SWITCH = b'\x00\xee'  # SmartPlug Switch Cluster
CLUSTER_ID_AM_POWER = b'\x00\xef'  # Power Information
CLUSTER_ID_AM_STATUS = b'\x00\xf0'  # Device Status
CLUSTER_ID_AM_TAMPER = b'\x00\xf2'  # Device Tamper Cluster
CLUSTER_ID_AM_BUTTON = b'\x00\xf3'  # Keyfob / Button
CLUSTER_ID_AM_DISCOVERY = b'\x00\xf6'  # Device Discovery
CLUSTER_ID_AM_SECURITY = b'\x05\x00'  # Security

# AlertMe Cluster Commands
CLUSTER_CMD_AM_SECURITY = b'\x00'  # Security Event (Sensors)
CLUSTER_CMD_AM_STATE_REQ = b'\x01'  # State Request (SmartPlug)
CLUSTER_CMD_AM_STATE_CHANGE = b'\x02'  # Change State (SmartPlug)
CLUSTER_CMD_AM_STATE_RESP = b'\x80'  # Switch Status Update
CLUSTER_CMD_AM_PWR_DEMAND = b'\x81'  # Power Demand Update
CLUSTER_CMD_AM_PWR_CONSUMPTION = b'\x82'  # Power Consumption & Uptime Update
CLUSTER_CMD_AM_PWR_UNKNOWN = b'\x86'  # Unknown British Gas Power Meter Update
CLUSTER_CMD_AM_MODE_REQ = b'\xfa'  # Mode Change Request
CLUSTER_CMD_AM_STATUS = b'\xfb'  # Status Update
CLUSTER_CMD_AM_VERSION_REQ = b'\xfc'  # Version Information Request
CLUSTER_CMD_AM_RSSI = b'\xfd'  # RSSI Range Test Update
CLUSTER_CMD_AM_VERSION_RESP = b'\xfe'  # Version Information Response

# At the moment I am not sure what/if the following dictionary will be used?
# It is here to describe the relationship between Cluster ID and Cmd.
# One day this may be used by the process_message() function and link with the parse_xxxxx() functions?
alertme_cluster_cmds = {
    CLUSTER_ID_AM_SWITCH: {
        CLUSTER_CMD_AM_STATE_REQ: "Relay State Request (SmartPlug)",
        CLUSTER_CMD_AM_STATE_CHANGE: "Relay State Change (SmartPlug)",
        CLUSTER_CMD_AM_STATE_RESP: "Switch Status Update"
    },
    CLUSTER_ID_AM_POWER: {
        CLUSTER_CMD_AM_PWR_DEMAND: "Power Demand Update",
        CLUSTER_CMD_AM_PWR_CONSUMPTION: "Power Consumption & Uptime Update",
        CLUSTER_CMD_AM_PWR_UNKNOWN: "Unknown British Gas Power Meter Update"
    },
    CLUSTER_ID_AM_STATUS: {
        CLUSTER_CMD_AM_MODE_REQ: "Mode Change Request",
        CLUSTER_CMD_AM_STATUS: "Status Update"
    },
    CLUSTER_ID_AM_TAMPER: {},
    CLUSTER_ID_AM_BUTTON: {},
    CLUSTER_ID_AM_DISCOVERY: {
        CLUSTER_CMD_AM_RSSI: "RSSI Range Test Update",
        CLUSTER_CMD_AM_VERSION_REQ: "Version Information Request",
        CLUSTER_CMD_AM_VERSION_RESP: "Version Information Response"
    },
    CLUSTER_ID_AM_SECURITY: {
        CLUSTER_CMD_AM_SECURITY: "Security Command"
    }
}

# This messages dict holds the skeleton for the various ZDO and AlertMe messages.
# it is used in conjunction with get_message() to generate the messages.
# Those with a lambda in the data key make use of the generate_xxxx() functions
# to generate the data based on parameters pasded.
messages = {
    'version_info_request': {
        'name': 'Version Info Request',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_DISCOVERY,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda self, params: self.generate_version_info_request(params)
        }
    },
    'version_info_update': {
        'name': 'Version Info Update',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_DISCOVERY,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda self, params: self.generate_version_info_update(params)
        },
        'expected_params': ['version', 'type', 'manu', 'manu_date']
    },
    'range_update': {
        'name': 'Range Update',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_DISCOVERY,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda self, params: self.generate_range_update(params)
        },
        'expected_params': ['rssi']
    },
    'switch_state_request': {
        'name': 'Relay State Request',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_SWITCH,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda self, params: self.generate_switch_state_request(params)
        },
        'expected_params': ['switch_state']
    },
    'switch_state_update': {
        'name': 'Relay State Update',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_SWITCH,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda self, params: self.generate_switch_state_update(params)
        }
    },
    'mode_change_request': {
        'name': 'Mode Change Request',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_STATUS,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda self, params: self.generate_mode_change_request(params)
        },
        'expected_params': ['mode']
    },
    'status_update': {
        'name': 'Status Update',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_STATUS,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda self, params: self.generate_status_update(params)
        }
    },
    'power_demand_update': {
        'name': 'Power Demand Update',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_POWER,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda self, params: self.generate_power_demand_update(params)
        }
    },
    'power_consumption_update': {
        'name': 'Power Consumption Update',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_POWER,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda self, params: self.generate_power_consumption_update(params)
        }
    },
    'button_press': {
        'name': 'Button Press',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_BUTTON,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda self, params: self.generate_button_press(params)
        }
    },
    'security_init': {
        'name': 'Security Initialization',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_SECURITY,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda self, params: self.generate_security_init(params)
        }
    },
    'active_endpoints_request': {
        'name': 'Active Endpoints Request',
        'frame': {
            'profile': PROFILE_ID_ZDP,
            'cluster': CLUSTER_ID_ZDO_ACTIVE_EP_REQ,
            'src_endpoint': ENDPOINT_ZDO,
            'dest_endpoint': ENDPOINT_ZDO,
            'data': lambda self, params: self.generate_active_endpoints_request(params)
        },
        'expected_params': ['sequence', 'addr_short']
    },
    'match_descriptor_request': {
        'name': 'Match Descriptor Request',
        'frame': {
            'profile': PROFILE_ID_ZDP,
            'cluster': CLUSTER_ID_ZDO_MATCH_DESC_REQ,
            'src_endpoint': ENDPOINT_ZDO,
            'dest_endpoint': ENDPOINT_ZDO,
            'data': lambda self, params: self.generate_match_descriptor_request(params)
        },
        'expected_params': ['sequence', 'addr_short', 'profile_id', 'in_cluster_list', 'out_cluster_list']
    },
    'match_descriptor_response': {
        'name': 'Match Descriptor Response',
        'frame': {
            'profile': PROFILE_ID_ZDP,
            'cluster': CLUSTER_ID_ZDO_MATCH_DESC_RSP,
            'src_endpoint': ENDPOINT_ZDO,
            'dest_endpoint': ENDPOINT_ZDO,
            'data': lambda self, params: self.generate_match_descriptor_response(params)
        },
        'expected_params': ['sequence', 'addr_short', 'endpoint_list']
    },
    'routing_table_request': {
        'name': 'Management Routing Table Request',
        'frame': {
            'profile': PROFILE_ID_ZDP,
            'cluster': CLUSTER_ID_ZDO_MGMT_RTG_REQ,
            'src_endpoint': ENDPOINT_ZDO,
            'dest_endpoint': ENDPOINT_ZDO,
            'data': b'\x12\x01'
        }
    },
    'permit_join_request': {
        'name': 'Management Permit Join Request',
        'frame': {
            'profile': PROFILE_ID_ZDP,
            'cluster': CLUSTER_ID_ZDO_MGMT_PERMIT_JOIN_REQ,
            'src_endpoint': ENDPOINT_ZDO,
            'dest_endpoint': ENDPOINT_ZDO,
            'data': b'\xff\x00'
        }
    }
}


class ZBNode(Node):
    def __init__(self, serial, callback=None):
        """
        Base Constructor

        :param serial: Serial Object
        :param callback: Optional
        """
        Node.__init__(self, callback)

        # Type Info
        self.type = 'ZBNode'
        self.version = 12345
        self.manu = 'PyAlertMe'
        self.manu_date = '2017-01-01'

        # Start up Serial and ZigBee
        self._serial = serial
        self._xbee = ZigBee(ser=self._serial, callback=self.receive_message,
                            error_callback=self.xbee_error, escaped=True)

        # My addresses
        self.addr_long = None
        self.addr_short = None

        # Fire off messages to discover own addresses
        self._addr_long_list = [b'', b'']
        self.read_addresses()

        # Scheduler Thread
        self._started = True
        self._schedule_thread = threading.Thread(target=self._schedule_loop)
        self._schedule_interval = 30
        self._schedule_thread.start()

        # ZDO Sequence
        self.zdo_sequence = 1

    def _schedule_loop(self):
        """
        Continual Updates Thread calls the _updates() function every at intervals set in self._schedule_interval.

        """
        while self._started:
            if self.associated:
                self._schedule_event()

                # The following for loop is being used in place of a simple
                # time.sleep(self._schedule_interval)
                # This is done so we can interrupt the thread quicker.
                for i in range(self._schedule_interval * 10):
                    if self._started:
                        time.sleep(0.1)

    def _schedule_event(self):
        """
        The _schedule_event() function is called by the _schedule_loop() thread function called at regular intervals.

        """
        self._logger.debug('Continual Update')

    def halt(self):
        """
        Halt Device
        Close XBee and Serial

        :return:
        """
        self._started = False         # This should kill the updates thread
        self._schedule_thread.join()  # Wait for updates thread to finish
        self._xbee.halt()
        self._serial.close()

    def get_message(self, message_id, params=None):
        """
        Get message

        :param message_id: Message ID
        :param params: Optional
        :return:
        """
        if params is None or params == '':
            params = {}

        if message_id in messages.keys():
            # Take a deep copy of the message
            message = copy.deepcopy(messages[message_id])

            if 'expected_params' in message.keys():
                expected_params = sorted(message['expected_params'])
                provided_params = sorted(params.keys())
                missing_params = sorted(set(expected_params).difference(set(provided_params)))

                if len(missing_params) > 0:
                    raise Exception("Missing Parameters: %s" % missing_params)

            # If 'data' is a lambda, then call it and replace with the return value
            data = message['frame']['data']
            if callable(data):
                message['frame']['data'] = data(self, params)

            # Return processed message
            return message['frame']

        else:
            raise Exception("Message '%s' does not exist" % message_id)

    def list_messages(self):
        """
        List messages

        :return:
        """
        actions = {}
        for message_id, message in messages.items():
            actions[message_id] = {'name': message['name']}
            if 'expected_params' in message.keys():
                actions[message_id]['expected_params'] = message['expected_params']

        return actions

    def xbee_error(self, error):
        """
        On XBee error this function is called

        :param error:
        :return:
        """
        self._logger.critical('XBee Error: %s', error)

    def read_addresses(self):
        """
        Work out own address

        """
        self._logger.debug('Requesting own addresses')
        self._xbee.send('at', command='MY')
        time.sleep(0.05)
        self._xbee.send('at', command='SH')
        time.sleep(0.05)
        self._xbee.send('at', command='SL')
        time.sleep(0.05)

    def send_message(self, message, dest_addr_long, dest_addr_short):
        """
        Send message to XBee

        :param message: Dict message
        :param dest_addr_long: 48-bits Long Address
        :param dest_addr_short: 16-bit Short Address
        :return:
        """
        # Tack on destination addresses
        message['dest_addr_long'] = dest_addr_long
        message['dest_addr'] = dest_addr_short

        self._logger.debug('Sending Message: %s', message)
        self._xbee.send('tx_explicit', **message)

    def receive_message(self, message):
        """
        Receive message from XBee
        Calls process message
        Process incoming message

        :param message: Dict of message
        :return:
        """
        self._logger.debug('Received Message: %s', message)

        attributes = {}
        reply = {}

        # AT Packets
        if message['id'] == 'at_response':
            if message['command'] == 'MY':
                self.addr_short = message['parameter']
            if message['command'] == 'SH':
                self._addr_long_list[0] = message['parameter']
            if message['command'] == 'SL':
                self._addr_long_list[1] = message['parameter']
            # If we have worked out both the High and Low addresses then calculate the full addr_long
            if self._addr_long_list[0] and self._addr_long_list[1]:
                self.addr_long = b''.join(self._addr_long_list)

        # ZigBee Explicit Packets
        if message['id'] == 'rx_explicit':
            source_addr_long = message['source_addr_long']
            source_addr_short = message['source_addr']
            profile_id = message['profile']
            cluster_id = message['cluster']

            if profile_id == PROFILE_ID_ZDP:
                # ZigBee Device Profile ID
                self._logger.debug('Received ZigBee Device Profile Packet')

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
                    # This message tells us what the device can do, but it isn't
                    # constructed correctly to match what the switch can do according
                    # to the spec. This is another message that gets it's response
                    # after we receive the Match Descriptor below.
                    self._logger.debug('Received Active Endpoint Response')

                elif cluster_id == CLUSTER_ID_ZDO_MATCH_DESC_REQ:
                    # Match Descriptor Request
                    self._logger.debug('Received Match Descriptor Request')
                    # This is the point where we finally respond to the switch.
                    # A couple of messages are sent to cause the switch to join with
                    # the controller at a network level and to cause it to regard
                    # this controller as valid.

                    # First send the Match Descriptor Response
                    sequence = 4   # message['rf_data'][0:1]
                    params = {
                        'sequence': sequence,
                        'addr_short': self.addr_short,
                        'endpoint_list': ENDPOINT_ALERTME
                    }
                    reply1 = self.get_message('match_descriptor_response', params)
                    self.send_message(reply1, source_addr_long, source_addr_short)

                    # The next messages are directed at the hardware code (rather
                    # than the network code). The device has to receive these two
                    # messages to stay joined.
                    time.sleep(2)
                    reply2 = self.get_message('version_info_request')
                    self.send_message(reply2, source_addr_long, source_addr_short)
                    time.sleep(2)
                    reply3 = self.get_message('mode_change_request', {'mode': 'Normal'})
                    self.send_message(reply3, source_addr_long, source_addr_short)

                    # We are fully associated!
                    self._logger.debug('New Device Fully Associated')

                elif cluster_id == CLUSTER_ID_ZDO_END_DEVICE_ANNCE:
                    # Device Announce Message
                    self._logger.debug('Received Device Announce Message')
                    # This will tell me the address of the new thing
                    # so we're going to send an active endpoint request
                    sequence = 4   # message['rf_data'][0:1]
                    reply = self.get_message('active_endpoints_request', {'sequence': sequence, 'mode': source_addr_short})

                elif cluster_id == CLUSTER_ID_ZDO_MGMT_NETWORK_UPDATE:
                    # Management Network Update Notify.
                    self._logger.debug('Received Management Network Update Notify')

                else:
                    self._logger.error('Unrecognised Cluster ID: %r', cluster_id)

            elif profile_id == PROFILE_ID_ALERTME:
                # AlertMe Profile ID
                self._logger.debug('Received AlertMe Specific Profile Packet')
                cluster_cmd = message['rf_data'][2:3]

                if cluster_id == CLUSTER_ID_AM_SWITCH:
                    if cluster_cmd == CLUSTER_CMD_AM_STATE_RESP:
                        self._logger.debug('Received Switch Status Update')
                        attributes = self.parse_switch_state_update(message['rf_data'])

                    elif cluster_cmd == CLUSTER_CMD_AM_STATE_REQ:
                        # State Request
                        # b'\x11\x00\x01\x01'
                        self._logger.debug('Switch Relay State is: %s', self.switch_state)
                        reply = self.get_message('switch_state_update', {'switch_state': self.switch_state})

                    elif cluster_cmd == CLUSTER_CMD_AM_STATE_CHANGE:
                        # Change State
                        # b'\x11\x00\x02\x01\x01' On
                        # b'\x11\x00\x02\x00\x01' Off
                        self._logger.debug('Received Change State')
                        attributes = self.parse_switch_state_request(message['rf_data'])
                        self.switch_state = attributes['switch_state']
                        reply = self.get_message('switch_state_update', {'switch_state': self.switch_state})

                    else:
                        self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                elif cluster_id == CLUSTER_ID_AM_POWER:
                    if cluster_cmd == CLUSTER_CMD_AM_PWR_DEMAND:
                        self._logger.debug('Received Power Demand Update')
                        attributes = self.parse_power_demand(message['rf_data'])

                    elif cluster_cmd == CLUSTER_CMD_AM_PWR_CONSUMPTION:
                        self._logger.debug('Received Power Consumption & Uptime Update')
                        attributes = self.parse_power_consumption(message['rf_data'])

                    elif cluster_cmd == CLUSTER_CMD_AM_PWR_UNKNOWN:
                        self._logger.debug('Unknown Power Update')
                        attributes = self.parse_power_unknown(message['rf_data'])

                    else:
                        self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                elif cluster_id == CLUSTER_ID_AM_TAMPER:
                    self._logger.debug('Received Tamper Switch Changed Update')
                    attributes = self.parse_tamper_state(message['rf_data'])

                elif cluster_id == CLUSTER_ID_AM_BUTTON:
                    self._logger.debug('Received Button Press Update')
                    attributes = self.parse_button_press(message['rf_data'])

                elif cluster_id == CLUSTER_ID_AM_SECURITY:
                    self._logger.debug('Received Security Event')
                    # Security Cluster
                    # When the device first connects, it comes up in a state that
                    # needs initialization, this command seems to take care of that.
                    # So, look at the value of the data and send the command.
                    if message['rf_data'][3:7] == b'\x15\x00\x39\x10':
                        reply = self.get_message('security_init')
                    attributes = self.parse_security_state(message['rf_data'])

                elif cluster_id == CLUSTER_ID_AM_DISCOVERY:
                    if cluster_cmd == CLUSTER_CMD_AM_RSSI:
                        self._logger.debug('Received RSSI Range Test Update')
                        attributes = self.parse_range_info_update(message['rf_data'])

                    elif cluster_cmd == CLUSTER_CMD_AM_VERSION_RESP:
                        self._logger.debug('Received Version Information')
                        attributes = self.parse_version_info_update(message['rf_data'])

                    elif cluster_cmd == CLUSTER_CMD_AM_VERSION_REQ:
                        # b'\x11\x00\xfc\x00\x01'
                        self._logger.debug('Received Version Request')
                        params = {
                            'type': self.type,
                            'version': self.version,
                            'manu': self.manu,
                            'manu_date': self.manu_date
                        }
                        reply = self.get_message('version_info_update', params)

                    else:
                        self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                elif cluster_id == CLUSTER_ID_AM_STATUS:
                    if cluster_cmd == CLUSTER_CMD_AM_STATUS:
                        self._logger.debug('Received Status Update')
                        attributes = self.parse_status_update(message['rf_data'])

                    elif cluster_cmd == CLUSTER_CMD_AM_MODE_REQ:
                        self._logger.debug('Received Mode Change Request')
                        # Take note of hub address
                        self.hub_addr_long = source_addr_long
                        self.hub_addr_short = source_addr_short
                        # We are now fully associated
                        self.associated = True

                        mode_cmd = message['rf_data'][3] + message['rf_data'][4]
                        if mode_cmd == b'\x00\x01':
                            # Normal
                            # b'\x11\x00\xfa\x00\x01'
                            self._logger.debug('Normal Mode')
                            self.mode = 'NORMAL'

                        elif mode_cmd == b'\x01\x01':
                            # Range Test
                            # b'\x11\x00\xfa\x01\x01'
                            self._logger.debug('Range Test Mode')
                            self.mode = 'RANGE'
                            # TODO Setup thread loop to send regular range RSSI updates
                            # for now just send one...
                            reply = self.get_message('range_update')

                        elif mode_cmd == b'\x02\x01':
                            # Locked
                            # b'\x11\x00\xfa\x02\x01'
                            self._logger.debug('Locked Mode')
                            self.mode = 'LOCKED'

                        elif mode_cmd == b'\x03\x01':
                            # Silent
                            # b'\x11\x00\xfa\x03\x01'
                            self._logger.debug('Silent Mode')
                            self.mode = 'SILENT'

                    else:
                        self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

            elif profile_id == PROFILE_ID_HA:
                # HA Profile ID
                self._logger.debug('Received HA Profile Packet')

            else:
                self._logger.error('Unrecognised Profile ID: %r', profile_id)

            if reply:
                self.send_message(reply, source_addr_long, source_addr_short)

            return attributes

    def generate_version_info_request(self, params=None):
        """
        Generate Version Info Request
        This message is sent FROM the Hub TO the SmartPlug requesting version information.

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC
        Cluster Command            1          Cluster Command - Version Information Request (b'\xfc')

        :param params: Parameter dictionary (none required)
        :return: Message data
        """
        preamble = b'\x11\x00'
        cluster_cmd = CLUSTER_CMD_AM_VERSION_REQ
        payload = b''  # No data required in request

        data = preamble + cluster_cmd + payload
        return data

    def generate_version_info_update(self, params):
        """
        Generate Version Info Update
        This message is sent TO the Hub FROM the SmartPlug advertising version information.

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC
        Cluster Command            1          Cluster Command - Version Information Response (b'\xfe')
        Unknown                    17         Unknown Values TBC. There may be more interesting stuff in here?
        HW Version                 2          Hardware Version
        Type Info                  Variable   Type Information (b'AlertMe.com\nSmartPlug\n2013-09-26')

        :param params: Parameter dictionary of version info
        :return: Message data
        """
        preamble = b'\x09\x71'  # b'\tq'
        cluster_cmd = CLUSTER_CMD_AM_VERSION_RESP
        payload = struct.pack('H', params['version']) \
                  + b'\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0b' \
                  + params['manu'] \
                  + '\n' + params['type'] \
                  + '\n' + params['manu_date']

        data = preamble + cluster_cmd + payload
        return data

    def parse_version_info_update(self, data):
        """
        Process message, parse for version information:
            Version, Type, Manufacturer, Date

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC
        Cluster Command            1          Cluster Command - Version Information Response (b'\xfe')
        Unknown                    17         Unknown Content TBC There may be more interesting stuff in here?
        HW Version                 2          Hardware Version
        Type Info                  Variable   Type Information (b'AlertMe.com\nSmartPlug\n2013-09-26')

        :param data: Message data
        :return: Parameter dictionary of version info
        """
        # The version string is variable length.
        # We therefore have to calculate the length of the string 
        # which we then use in the unpack.
        l = len(data) - 22
        ret = dict(zip(
            ('cluster_cmd', 'version', 'manu_string'),
            struct.unpack('< 2x s H 17x %ds' % l, data)
        ))

        # Break down the version string into its component parts
        # AlertMe.com\nSmartPlug\n2013-09-26
        ret['manu_string'] = str(ret['manu_string'].decode()) \
            .replace('\t', '\n') \
            .replace('\r', '\n') \
            .replace('\x0e', '\n') \
            .replace('\x0b', '\n') \
            .replace('\x06', '\n') \
            .replace('\x04', '\n') \
            .replace('\x12', '\n')
        (ret['manu'], ret['type'], ret['manu_date']) = ret['manu_string'].split('\n')

        # Delete not required keys
        del ret['manu_string']
        del ret['cluster_cmd']

        return ret

    def generate_range_update(self, params):
        """
        Generate range message

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC
        Cluster Command            1          Cluster Command - RSSI Range Test Update (b'\xfd')
        RSSI Value                 1          RSSI Range Test Value
        Unknown                    1          ???

        :param params: Parameter dictionary of RSSI value
        :return: Message data
        """
        preamble = b'\x09\x2b'  # b'\t+'
        cluster_cmd = CLUSTER_CMD_AM_RSSI
        payload = struct.pack('B 1x', params['rssi'])

        data = preamble + cluster_cmd + payload
        return data

    def parse_range_info_update(self, data):
        """
        Process message, parse for RSSI range test value

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC
        Cluster Command            1          Cluster Command - RSSI Range Test Update (b'\xfd')
        RSSI Value                 1          RSSI Range Test Value
        Unknown                    1          ???

        :param data: Message data
        :return: Parameter dictionary of RSSI value
        """
        values = dict(zip(
            ('cluster_cmd', 'rssi'),
            struct.unpack('< 2x s B 1x', data)
        ))
        rssi = values['rssi']
        return {'rssi': rssi}

    def generate_power_demand_update(self, params):
        """
        Generate Power Demand Update message data

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC
        Cluster Command            1          Cluster Command - Power Demand Update (b'\x81')
        Power Value                2          Power Demand Value (kW)

        :param params: Parameter dictionary of power demand value
        :return: Message data
        """
        preamble = b'\x09\x6a'  # b'\tj'
        cluster_cmd = CLUSTER_CMD_AM_PWR_DEMAND
        payload = struct.pack('H', params['power_demand'])

        data = preamble + cluster_cmd + payload
        return data

    def generate_power_consumption_update(self, params):
        """
        Power Consumption & Uptime Update

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC
        Cluster Command            1          Cluster Command - Power Consumption & Uptime Update (b'\x82')
        Power Value                4          Power Consumption Value (kWh)
        Up Time                    4          Up Time Value (seconds)
        Unknown                    1          ???

        :return: Message
        """
        params = {
            'power_consumption': 19973,
            'up_time': 33207
        }
        # At the moment this just generates a hard coded message.
        # Also see parse_power_consumption().
        data = b'\tn\x82\x05N\x00\x00\xb7\x81\x00\x00\x01'

        return data

    def parse_power_demand(self, data):
        """
        Process message, parse for power demand value.

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC
        Cluster Command            1          Cluster Command - Power Demand Update (b'\x81')
        Power Value                2          Power Demand Value (kW)

        Examples:
            b'\tj\x81\x00\x00'  {'PowerDemand': 0}
            b'\tj\x81%\x00'     {'PowerDemand': 37}
            b'\tj\x81\x16\x00'  {'PowerDemand': 22}

        :param data: Message data
        :return: Parameter dictionary of power demand value
        """
        ret = dict(zip(
            ('cluster_cmd', 'power_demand'),
            struct.unpack('< 2x s H', data)
        ))
        del ret['cluster_cmd']

        return ret

    def parse_power_unknown(self, data):
        """
        Parse unknown power message seen from British Gas (AlertMe) power monitor.
        Could this be the same or merged with parse_power_demand() or parse_power_consumption() ?

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC              (b'\t\x00')
        Cluster Command            1          Cluster Command - Unknown Power   (b'\x86')
        Unknown                    11         ?? TODO Work out what power values this message contains!

        Examples:
            b'\t\x00\x86\x00\x00\x00\x00\x00\x00/\x00\x00\x00\x00'  = 0
            b'\t\x00\x86\x91\x012"\x00\x00M\x00\x00\x00\x00'        = ?
            b'\t\x00\x86F\x01{\xc9\x02\x007\x02\x00\x00\x00'        = ?

        :param data: Message data
        :return: Parameter dictionary of power demand value
        """

        value = struct.unpack('<H', data[3:5])[0]  # TBC
        return {'power_demand': value}

    def parse_power_consumption(self, data):
        """
        Process message, parse for power consumption value.

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC
        Cluster Command            1          Cluster Command - Power Consumption & Uptime Update (b'\x82')
        Power Value                4          Power Consumption Value (kWh)
        Up Time                    4          Up Time Value (seconds)
        Unknown                    1          ???

        :param data: Message data
        :return: Parameter dictionary of usage stats
        """
        ret = dict(zip(
            ('cluster_cmd', 'power_consumption', 'up_time'),
            struct.unpack('< 2x s I I 1x', data)
        ))
        del ret['cluster_cmd']

        return ret

    def generate_mode_change_request(self, params):
        """
        Generate Mode Change Request
        Available Modes: 'Normal', 'RangeTest', 'Locked', 'Silent'

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC
        Cluster Command            1          Cluster Command - Mode Change Request (b'\xfa')
        Mode                       2          Requested Mode (1: Normal, 257: Range Test, 513: Locked, 769: Silent)

        :param params: Parameter dictionary of requested mode
        :return: Message data
        """
        preamble = b'\x11\x00'
        cluster_cmd = CLUSTER_CMD_AM_MODE_REQ
        payload = b'\x00\x01'  # Default normal if no mode

        mode = params['mode']
        if mode == 'Normal':
            payload = b'\x00\x01'
        elif mode == 'RangeTest':
            payload = b'\x01\x01'
        elif mode == 'Locked':
            payload = b'\x02\x01'
        elif mode == 'Silent':
            payload = b'\x03\x01'
        else:
            self._logger.error('Invalid mode request %s', mode)

        data = preamble + cluster_cmd + payload
        return data

    def generate_switch_state_request(self, params):
        """
        Generate Switch State Change request data.
        This message is sent FROM the Hub TO the SmartPlug requesting state change.

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC
        Cluster Command            1          Cluster Command - Change State (SmartPlug) (b'\x01' / b'\x02')
        Requested Relay State      2*         b'\x01' = Check Only, b'\x01\x01' = On, b'\x00\x01' = Off
                                              * Size = 1 if check only

        :param params: Parameter dictionary of switch relay state
        :return: Message data
        """
        preamble = b'\x11\x00'

        if params['switch_state'] != '':
            cluster_cmd = CLUSTER_CMD_AM_STATE_CHANGE
            if int(params['switch_state']) == 1:
                payload = b'\x01\x01'  # On
            else:
                payload = b'\x00\x01'  # Off
        else:
            # Check Only
            cluster_cmd = CLUSTER_CMD_AM_STATE_REQ
            payload = b'\x01'

        data = preamble + cluster_cmd + payload
        return data

    def parse_switch_state_request(self, data):
        """
        Process message, parse for switch relay state change request.
        This message is sent FROM the Hub TO the SmartPlug requesting state change.

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC
        Cluster Command            1          Cluster Command - Change State (SmartPlug) (b'\x02')
        Requested Relay State      2          b'\x01\x01' = On, b'\x00\x01' = Off

        :param data: Message data
        :return: Parameter dictionary of switch relay state
        """
        # Parse Switch State Request
        if data == b'\x11\x00\x02\x01\x01':
            return {'switch_state': 1}
        elif data == b'\x11\x00\x02\x00\x01':
            return {'switch_state': 0}
        else:
            self._logger.error('Unknown State Request')

    def generate_switch_state_update(self, params):
        """
        Generate Switch State update message data.
        This message is sent TO the Hub FROM the SmartPlug advertising state change.

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC
        Cluster Command            1          Cluster Command - Switch Status Update (b'\x80')
        Relay State                2          b'\x07\x01' = On, b'\x06\x00' = Off

        :param params: Parameter dictionary of switch relay state
        :return: Message data
        """
        preamble = b'\x09\x68'  # b'\th'
        cluster_cmd = CLUSTER_CMD_AM_STATE_RESP
        payload = b'\x07\x01' if params['switch_state'] else b'\x06\x00'

        data = preamble + cluster_cmd + payload
        return data

    def parse_switch_state_update(self, data):
        """
        Process message, parse for switch status.
        This message is sent TO the Hub FROM the SmartPlug advertising state change.

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC
        Cluster Command            1          Cluster Command - Switch Status Update (b'\x80')
        Relay State                2          b'\x07\x01' = On, b'\x06\x00' = Off

        Examples:
            b'\th\x80\x07\x01'
            b'\th\x80\x06\x00'

        :param data: Message data
        :return: Parameter dictionary of switch status
        """
        values = struct.unpack('< 2x b b b', data)

        if values[2] & 0x01:
            return {'switch_state': 1}
        else:
            return {'switch_state': 0}

    def generate_button_press(self, params=None):
        """
        Button Press Update

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   1          Unknown Preamble TBC              (b'\t')
        Cluster Command            1          Cluster Command - Security Event  (b'\x00')
        Button State               1          Button State                      (b'\x01' = On, b'\x00' = Off)
        Unknown                    1          ???                               (b'\x00')
        Unknown                    1          ???                               (b'\x01')
        Counter                    2          Counter (milliseconds)            (b'X\xf4')
        Unknown                    2          ???                               (b'\x00\x00')

        :return: Message
        """
        params = {
            'button_state': 1,
            'counter': 62552
        }
        # At the moment this just generates a hard coded message.
        # Also see parse_button_press().
        data = b'\t\x00\x01\x00\x01X\xf4\x00\x00'

        return data

    def parse_button_press(self, data):
        """
        Process message, parse for button press status.

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   1          Unknown Preamble TBC              (b'\t')
        Cluster Command            1          Cluster Command - Security Event  (b'\x00')
        Button State               1          Button State                      (b'\x01' = On, b'\x00' = Off)
        Unknown                    1          ???                               (b'\x00')
        Unknown                    1          ???                               (b'\x01', b'\x02')
        Counter                    2          Counter (milliseconds)            (b'\xbf\xc3', b\x12\xca)
        Unknown                    2          ???                               (b'\x00\x00')

        Examples:
            b'\t\x00\x00\x00\x02\xbf\xc3\x00\x00' {'State': 0, 'Counter': 50111}
            b'\t\x00\x01\x00\x01\x12\xca\x00\x00' {'State': 1, 'Counter': 51730}

        :param data: Message data
        :return: Parameter dictionary of button status
        """
        ret = {}
        if ord(data[2]) == 0x00:
            ret['button_state'] = 0
        elif ord(data[2]) == 0x01:
            ret['button_state'] = 1

        ret['counter'] = struct.unpack('<H', data[5:7])[0]

        return ret

    def parse_tamper_state(self, data):
        """
        Process message, parse for Tamper Switch State Change

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   1          Unknown Preamble TBC              (b'\t')
        Cluster Command            1          Cluster Command - Security Event  (b'\x00')
        Unknown                    1          ???                               (b'\x00', b'\x01')
        Tamper State               1          Tamper State                      (b'\x01' = Closed, b'\x02' = Open)
        Counter                    2          Counter (milliseconds)            (b'\xe8\xa6')
        Unknown                    2          ???                               (b'\x00\x00')

        Examples:
            b'\t\x00\x00\x02\xe8\xa6\x00\x00'  {'Counter': 42728, 'TamperState': 1}
            b'\t\x00\x01\x01+\xab\x00\x00'     {'Counter': 43819, 'TamperState': 0}

        :param data: Message data
        :return: Parameter dictionary of tamper status
        """
        ret = {}
        if ord(data[3]) == 0x02:
            ret['tamper_state'] = 1  # Open
        else:
            ret['tamper_state'] = 0  # Closed

        ret['counter'] = struct.unpack('<H', data[4:6])[0]

        return ret

    def parse_security_state(self, data):
        """
        Process message, parse for security state.
        TODO: Is this the SAME AS parse_tamper_state!?!

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   1          Unknown Preamble TBC              (b'\t')
        Cluster Command            1          Cluster Command - Security Event  (b'\x00')
        Unknown                    1          ???                               (b'\x00')
        Button State               1          Security States Bitfield          (b'\00', b'\01', b'\04', b'\05')
        Unknown                    2          ???                               (b'\x00\x00')

        Examples:
            b'\t\x00\x00\x00\x00\x00'  {'TriggerState': 0, 'TamperState': 0}
            b'\t\x00\x00\x01\x00\x00'  {'TriggerState': 1, 'TamperState': 0}
            b'\t\x00\x00\x04\x00\x00'  {'TriggerState': 0, 'TamperState': 1}
            b'\t\x00\x00\x05\x00\x00'  {'TriggerState': 1, 'TamperState': 1}

        :param data: Message data
        :return: Parameter dictionary of security state
        """
        ret = {}
        # The security states are in byte [3] and is a bitfield:
        #    bit 0 is the magnetic reed switch state
        #    bit 3 is the tamper switch state
        state = ord(data[3])
        if state & 0x01:
            ret['trigger_state'] = 1  # Open
        else:
            ret['trigger_state'] = 0  # Closed

        if state & 0x04:
            ret['tamper_state'] = 1  # Open
        else:
            ret['tamper_state'] = 0  # Closed

        return ret

    def generate_security_init(self, params=None):
        """
        Generate Security Initialisation. Keeps security devices joined?

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC              (b'\x11\x80')
        Cluster Command            1          Cluster Command - Security Event  (b'\x00')
        Unknown                    2          ???                               (b'\x00\x05')

        :param params: Parameter dictionary (none required)
        :return: Message data
        """
        preamble = b'\x11\x80'
        cluster_cmd = CLUSTER_CMD_AM_SECURITY
        payload = b'\x00\x05'

        data = preamble + cluster_cmd + payload
        return data

    def parse_status_update(self, data):
        """
        Process message, parse for status update

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC              (b'\t\x89')
        Cluster Command            1          Cluster Command - Status Update   (b'\xfb')
        Type                       1          b'\x1b' Clamp, b'\x1c' Switch, b'\x1d' Key Fob, b'\x1e', b'\x1f' Door
        Counter                    4          Counter                           (b'\xdb2\x00\x00')
        TempFahrenheit             2          Temperature (Fahrenheit)          (b'\xf0\x0b')
        Unknown                    6          ???                               (b'na\xd3\xff\x03\x00')

        Examples:
            b'\t\x89\xfb\x1d\xdb2\x00\x00\xf0\x0bna\xd3\xff\x03\x00' {'Temperature': 87.008, 'Counter': 13019}
            b'\t\r\xfb\x1f<\xf1\x08\x02/\x10D\x02\xcf\xff\x01\x00'   {'Temperature': 106.574, 'TriggerState': 0, 'TamperState': 1}

        :param data: Message data
        :return: Parameter dictionary of state
        """
        ret = {}
        _type = data[3]
        if _type == b'\x1b':
            # Power Clamp
            # Unknown
            pass

        elif _type == b'\x1c':
            # Power Switch
            # Unknown
            pass

        elif _type == b'\x1d':
            # Key Fob
            ret['temperature'] = float(struct.unpack("<h", data[8:10])[0]) / 100.0 * 1.8 + 32
            ret['counter'] = struct.unpack('<I', data[4:8])[0]

        elif _type == b'\x1e' or _type == b'\x1f':
            # Door Sensor
            ret['temperature'] = float(struct.unpack("<h", data[8:10])[0]) / 100.0 * 1.8 + 32
            if ord(data[-1]) & 0x01 == 1:
                ret['trigger_state'] = 1  # Open
            else:
                ret['trigger_state'] = 0  # Closed

            if ord(data[-1]) & 0x02 == 0:
                ret['tamper_state'] = 1  # Open
            else:
                ret['tamper_state'] = 0  # Closed

        else:
            self._logger.error('Unrecognised Device Status %r  %r', _type, data)

        return ret

    def generate_status_update(self, params):
        """
        Generate Status Update

        Field Name                 Size       Description
        ----------                 ----       -----------
        Preamble                   2          Unknown Preamble TBC b'\t\r'
        Cluster Command            1          Cluster Command - Status Update (b'\xfb')
        Type                       1          b'\x1b' Clamp, b'\x1c' Switch, b'\x1d' Key Fob, b'\x1e', b'\x1f' Door
        Counter                    4          Counter
        TempFahrenheit             2          Temperature (Fahrenheit)
        Unknown                    6          ???

        :return: Message
        """
        params = {
            'trigger_state': 0,
            'temperature': 106.574,
            'tamper_state': 1
        }
        # At the moment this just generates a hard coded message.
        # The below is just one type of status update, see parse_status_update() for more.
        data = b'\t\r\xfb\x1f<\xf1\x08\x02/\x10D\x02\xcf\xff\x01\x00'

        return data

    def generate_active_endpoints_request(self, params):
        """
        Generate Active Endpoints Request
        The active endpoint request needs the short address of the device
        in the payload. Remember, it needs to be little endian (backwards)
        The first byte in the payload is simply a number to identify the message
        the response will have the same number in it.

        Field Name                 Size       Description
        ----------                 ----       -----------
        Sequence                   1          Frame Sequence
        Network Address            2          16-bit address of a device in the network whose active endpoint list being requested.

        :param params:
        :return: Message data

        Example:
            b'\xaa\x9f\x88'
        """
        sequence = struct.pack('B', params['sequence'])  # b'\xaa'
        net_addr = params['addr_short'][1] + params['addr_short'][0]  # b'\x9f\x88'

        data = sequence + net_addr
        return data

    def generate_match_descriptor_request(self, params):
        """
        Generate Match Descriptor Request
        Broadcast or unicast transmission used to discover the device(s) that supports
        a specified profile ID and/or clusters.

        Field Name                 Size       Description
        ----------                 ----       -----------
        Sequence                   1          Frame Sequence
        Network Address            2          16-bit address of a device in the network whose power descriptor is being requested.
        Profile ID                 2          Profile ID to be matched at the destination.
        Number of Input Clusters   1          The number of input clusters in the In Cluster List for matching. Set to 0 if no clusters supplied.
        Input Cluster List         2*         List of input cluster IDs to be used for matching.
        Number of Output Clusters  1          The number of output clusters in the Output Cluster List for matching. Set to 0 if no clusters supplied.
        Output Cluster List        2*         List of output cluster IDs to be used for matching.
                                              * Number of Input Clusters

        Example:
            b'\x01\xfd\xff\x16\xc2\x00\x01\xf0\x00'

        :param params:
        :return: Message data
        """
        sequence = struct.pack('B', params['sequence'])  # b'\x01'
        net_addr = params['addr_short'][1] + params['addr_short'][0]  # b'\xfd\xff'
        profile_id = params['profile_id'][1] + params['profile_id'][0]  # b'\x16\xc2'  PROFILE_ID_ALERTME (reversed)
        num_input_clusters = struct.pack('B', len(params['in_cluster_list']) / 2)  # b'\x00'
        input_cluster_list = params['in_cluster_list']  # b''
        num_output_clusters = struct.pack('B', len(params['out_cluster_list']) / 2)  # b'\x01'
        output_cluster_list = params['out_cluster_list'][1] + params['out_cluster_list'][0]  # b'\xf0\x00'  CLUSTER_ID_AM_STATUS (reversed)
        # TODO Finish this off! At the moment this does not support multiple clusters, it just supports one!

        data = sequence + net_addr + profile_id + num_input_clusters + input_cluster_list + num_output_clusters + output_cluster_list
        return data

    def generate_match_descriptor_response(self, params):
        """
        Generate Match Descriptor Response
        If a descriptor match is found on the device, this response contains a list of endpoints that
        support the request criteria.

        Field Name                 Size       Description
        ----------                 ----       -----------
        Sequence                   1          Frame Sequence
        Status                     1          Response Status
        Network Address            2          Indicates the 16-bit address of the responding device.
        Length                     1          The number of endpoints on the remote device that match the request criteria.
        Match List                 Variable   List of endpoints on the remote that match the request criteria.

        Example:
            b'\x04\x00\x00\x00\x01\x02'

        :param params:
        :return: Message data
        """
        sequence = struct.pack('B', params['sequence'])  # b'\x04'
        status = ZDP_STATUS_OK  # b'\x00'
        net_addr = params['addr_short'][1] + params['addr_short'][0]  # b'\x00\x00'
        length = struct.pack('B', len(params['endpoint_list']))  # b'\x01'
        match_list = params['endpoint_list']  # b'\x02'

        data = sequence + status + net_addr + length + match_list
        return data








