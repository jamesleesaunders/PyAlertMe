import logging
import struct
import copy

# Zigbee Addressing
BROADCAST_LONG = b'\x00\x00\x00\x00\x00\x00\xff\xff' 
BROADCAST_SHORT = b'\xff\xfe'

# Zigbee Profile IDs
PROFILE_ID_ZDP     = b'\x00\x00'  # Zigbee Device Profile
PROFILE_ID_HA      = b'\x01\x04'  # HA Device Profile
PROFILE_ID_LL      = b'\xc0\x5e'  # Light Link Profile
PROFILE_ID_ALERTME = b'\xc2\x16'  # AlertMe Private Profile

# Zigbee Endpoints
ENDPOINT_ZDO       = b'\x00'      # ZigBee Device Objects Endpoint
ENDPOINT_ALERTME   = b'\x02'      # Alertme/Iris Endpoint

# ZDO Clusters
CLUSTER_ID_ZDO_NETWORK_ADDRESS_REQ   = b'\x00\x00'   # Network (16-bit) Address Request
CLUSTER_ID_ZDO_NETWORK_ADDRESS_RESP  = b'\x80\x00'   # Network (16-bit) Address Response
CLUSTER_ID_ZDO_NODE_DESCRIPTOR_RESP  = b'\x802'      # Node Descriptor Response
CLUSTER_ID_ZDO_SIMPLE_DESCRIPTOR_REQ = b'\x00\x04'   # Simple Descriptor Request
CLUSTER_ID_ZDO_ACTIVE_ENDPOINTS_REQ  = b'\x00\x05'   # Active Endpoints Request
CLUSTER_ID_ZDO_ACTIVE_ENDPOINTS_RESP = b'\x80\x05'   # Active Endpoints Response
CLUSTER_ID_ZDO_MATCH_DESCRIPTOR_REQ  = b'\x00\x06'   # Match Descriptor Request
CLUSTER_ID_ZDO_MATCH_DESCRIPTOR_RESP = b'\x80\x06'   # Match Descriptor Response
CLUSTER_ID_ZDO_DEVICE_ANNOUNCE       = b'\x00\x13'   # Device Announce Message
CLUSTER_ID_ZDO_MGNT_ROUTING_REQ      = b'\x00\x32'   # Management Routing Request
CLUSTER_ID_ZDO_PERMIT_JOIN_REQ       = b'\x00\x36'   # Permit Join Request
CLUSTER_ID_ZDO_MGNT_NETWORK_UPDATE   = b'\x80\x38'   # Management Network Update Notify

# AlertMe Clusters
CLUSTER_ID_AM_SWITCH    = b'\x00\xee'
CLUSTER_ID_AM_POWER     = b'\x00\xef'
CLUSTER_ID_AM_STATUS    = b'\x00\xf0'
CLUSTER_ID_AM_TAMPER    = b'\x00\xf2'
CLUSTER_ID_AM_BUTTON    = b'\x00\xf3'
CLUSTER_ID_AM_DISCOVERY = b'\x00\xf6'
CLUSTER_ID_SECURITY     = b'\x05\x00'

# AlertMe Cluster Commands
CLUSTER_CMD_AM_STATE_REQ       = b'\x01'  # State Request (SmartPlug)
CLUSTER_CMD_AM_STATE_CHANGE    = b'\x02'  # Change State (SmartPlug)
CLUSTER_CMD_AM_STATE_RESP      = b'\x80'  # Switch Status Update
CLUSTER_CMD_AM_PWR_DEMAND      = b'\x81'  # Power Demand Update
CLUSTER_CMD_AM_PWR_CONSUMPTION = b'\x82'  # Power Consumption & Uptime Update
CLUSTER_CMD_AM_MODE_REQ        = b'\xfa'  # Mode Change Request
CLUSTER_CMD_AM_STATUS          = b'\xfb'  # Status Update
CLUSTER_CMD_AM_RSSI            = b'\xfd'  # RSSI Range Test Update
CLUSTER_CMD_AM_VERSION         = b'\xfe'  # Received Version Information

# At the moment I am not sure what/if the following dict will be used?
# It is here to describe the relationship between Cluster ID and Cmd.
# One day this dict may be used by the process_message() function and link with the parse_xxxxx() functions?
alertme_cluster_cmds = {
    CLUSTER_ID_AM_SWITCH: {
        CLUSTER_CMD_AM_STATE_REQ: "State Request (SmartPlug)",
        CLUSTER_CMD_AM_STATE_CHANGE: "Change State (SmartPlug)",
        CLUSTER_CMD_AM_STATE_RESP: "Switch Status Update"
    },
    CLUSTER_ID_AM_POWER: {
        CLUSTER_CMD_AM_PWR_DEMAND: "Power Demand Update",
        CLUSTER_CMD_AM_PWR_CONSUMPTION: "Power Consumption & Uptime Update"
    },
    CLUSTER_ID_AM_STATUS: {
        CLUSTER_CMD_AM_MODE_REQ: "Mode Change Request",
        CLUSTER_CMD_AM_STATUS: "Status Update"
    },
    CLUSTER_ID_AM_TAMPER: {},
    CLUSTER_ID_AM_BUTTON: {},
    CLUSTER_ID_AM_DISCOVERY: {
        CLUSTER_CMD_AM_RSSI: "RSSI Range Test Update",
        CLUSTER_CMD_AM_VERSION: "Received Version Information"
    },
    CLUSTER_ID_SECURITY: {}
}

messages = {
    'version_info_request': {
        'name': 'Version Info Request',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_DISCOVERY,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda params: generate_version_info_request(params)
        }
    },
    'version_info_update': {
        'name': 'Version Info Update',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_DISCOVERY,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda params: generate_version_info_update(params)
        }
    },
    'range_info_update': {
        'name': 'Range Info Update',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_DISCOVERY,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda params: generate_range_update(params)
        }
    },
    'switch_state_request': {
        'name': 'Switch State Request',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_SWITCH,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda params: generate_switch_state_request(params)
        }
    },
    'switch_state_update': {
        'name': 'Switch State Update',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_SWITCH,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda params: generate_switch_state_update(params)
        }
    },
    'mode_change_request': {
       'name': 'Mode Change Request',
       'frame': {
           'profile': PROFILE_ID_ALERTME,
           'cluster': CLUSTER_ID_AM_STATUS,
           'src_endpoint': ENDPOINT_ALERTME,
           'dest_endpoint': ENDPOINT_ALERTME,
           'data': lambda params: generate_mode_change_request(params)
       }
    },
    'missing_link': {
        'name': 'Missing Link',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_STATUS,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda params: generate_missing_link(params)
        }
    },
    'power_demand_update': {
        'name': 'Power Demand Update',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_POWER,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda params: generate_power_demand_update(params)
        }
    },
    'security_init': {
        'name': 'Security Initialization',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_SECURITY,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda params: generate_security_init(params)
        }
    },
    'active_endpoints_request': {
        'name': 'Active Endpoints Request',
        'frame': {
            'profile': PROFILE_ID_ZDP,
            'cluster': CLUSTER_ID_ZDO_ACTIVE_ENDPOINTS_REQ,
            'src_endpoint': ENDPOINT_ZDO,
            'dest_endpoint': ENDPOINT_ZDO,
            'data': lambda params: generate_active_endpoints_request(params)
        }
    },
    'match_descriptor_request': {
        'name': 'Match Descriptor Request',
        'frame': {
            'profile': PROFILE_ID_ZDP,
            'cluster': CLUSTER_ID_ZDO_MATCH_DESCRIPTOR_REQ,
            'src_endpoint': ENDPOINT_ZDO,
            'dest_endpoint': ENDPOINT_ZDO,
            'data': lambda params: generate_match_descriptor_request(params)
        }
    },
    'match_descriptor_response': {
        'name': 'Match Descriptor Response',
        'frame': {
            'profile': PROFILE_ID_ZDP,
            'cluster': CLUSTER_ID_ZDO_MATCH_DESCRIPTOR_RESP,
            'src_endpoint': ENDPOINT_ZDO,
            'dest_endpoint': ENDPOINT_ZDO,
            'data': lambda params: generate_match_descriptor_response(params)
        }
    },
    'routing_table_request': {
        'name': 'Management Routing Table Request',
        'frame': {
            'profile': PROFILE_ID_ZDP,
            'cluster': CLUSTER_ID_ZDO_MGNT_ROUTING_REQ,
            'src_endpoint': ENDPOINT_ZDO,
            'dest_endpoint': ENDPOINT_ZDO,
            'data': b'\x12\x01'
        }
    },
    'permit_join_request': {
        'name': 'Management Permit Join Request',
        'frame': {
            'profile': PROFILE_ID_ZDP,
            'cluster': CLUSTER_ID_ZDO_PERMIT_JOIN_REQ,
            'src_endpoint': ENDPOINT_ZDO,
            'dest_endpoint': ENDPOINT_ZDO,
            'data': b'\xff\x00'
        }
    }
}


def get_message(message_id, params=None):
    """
    Get message

    :param message_id: Message ID
    :param params: Optional
    :return:
    """
    if params is None or params == '':
        params = {}

    if message_id in messages.keys():
        # Make a copy of the message
        message = copy.deepcopy(messages[message_id])
        data = message['frame']['data']

        # If data is a lambda then call it and replace with return value
        if callable(data):
            message['frame']['data'] = data(params)

        # Return processed message
        return message['frame']

    else:
        raise Exception('Message does not exist')

        
def list_messages():
    """
    List messages

    :return:
    """
    actions = {}
    for id, message in messages.items():
        actions[id] = message['name']
    return actions


def generate_version_info_request(params=None):
    """
    Generate Version Info Request
    This message is sent FROM the Hub TO the SmartPlug requesting version information.

    :param params: Parameter dictionary (none required)
    :return: Message data
    """
    data = b'\x11\x00\xfc'
    return data


def generate_version_info_update(params):
    """
    Generate Version Info Update
    This message is sent TO the Hub FROM the SmartPlug advertising version information.

    :param params: Parameter dictionary of version info
    :return: Message data
    """
    checksum = b'\tq'
    cluster_cmd = CLUSTER_CMD_AM_VERSION
    payload = struct.pack('H', params['Version']) \
              + b'\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0b' \
              + params['Manufacturer'] \
              + '\n' + params['Type'] \
              + '\n' + params['ManufactureDate']
    data = checksum + cluster_cmd + payload

    return data


def parse_version_info_update(data):
    """
    Process message, parse for version information:
    Type, Version, Manufacturer and Manufacturer Date

    :param data: Message data
    :return: Parameter dictionary of version info
    """
    # The version string is variable length. We therefore have to calculate the
    # length of the string which we then use in the unpack
    l = len(data) - 22
    values = dict(zip(
        ('cluster_cmd', 'hw_version', 'string'),
        struct.unpack('< 2x s H 17x %ds' % l, data)
    ))

    # Break down the version string into its component parts
    ret = {}
    ret['Version'] = values['hw_version']
    ret['String']  = str(values['string'].decode()) \
        .replace('\t', '\n') \
        .replace('\r', '\n') \
        .replace('\x0e', '\n') \
        .replace('\x0b', '\n') \
        .replace('\x06', '\n') \
        .replace('\x04', '\n') \
        .replace('\x12', '\n')

    ret['Manufacturer']    = ret['String'].split('\n')[0]
    ret['Type']            = ret['String'].split('\n')[1]
    ret['ManufactureDate'] = ret['String'].split('\n')[2]
    del ret['String']

    return ret


def generate_range_update(params):
    """
    Generate range message

    :param params: Parameter dictionary of RSSI value
    :return: Message data
    """
    checksum = b'\t+'
    cluster_cmd = CLUSTER_CMD_AM_RSSI
    payload = struct.pack('B 1x', params['RSSI'])
    data = checksum + cluster_cmd + payload

    return data


def parse_range_info_update(data):
    """
    Process message, parse for RSSI range test value

    :param data: Message data
    :return: Parameter dictionary of RSSI value
    """
    values = dict(zip(
        ('cluster_cmd', 'RSSI'),
        struct.unpack('< 2x s B 1x', data)
    ))
    rssi = values['RSSI']
    return {'RSSI' : rssi}


def generate_power_demand_update(params):
    """
    Generate Power Demand Update message data

    :param params: Parameter dictionary of power demand value
    :return: Message data
    """
    checksum = b'\tj'
    cluster_cmd = CLUSTER_CMD_AM_PWR_DEMAND
    payload = struct.pack('H', params['PowerDemand'])
    data = checksum + cluster_cmd + payload
    return data


def generate_mode_change_request(params):
    """
    Generate Mode Change Request
    Available Modes: 'Normal', 'RangeTest', 'Locked', 'Silent'

    :param params: Parameter dictionary of requested mode
    :return: Message data
    """
    mode = params['Mode']
    data = b''
    if mode == 'Normal':
        data = b'\x11\x00\xfa\x00\x01'
    elif mode == 'RangeTest':
        data = b'\x11\x00\xfa\x01\x01'
    elif mode == 'Locked':
        data = b'\x11\x00\xfa\x02\x01'
    elif mode == 'Silent':
        data = b'\x11\x00\xfa\x03\x01'
    else:
        logging.error('Invalid mode request %s', mode)

    return data


def parse_power_demand(data):
    """
    Process message, parse for power demand value.

    :param data: Message data
    :return: Parameter dictionary of power demand value
    """
    values = dict(zip(
        ('cluster_cmd', 'power_demand'),
        struct.unpack('< 2x s H', data)
    ))

    return {'PowerDemand': values['power_demand']}


def parse_power_consumption(data):
    """
    Process message, parse for power consumption value.

    :param data: Message data
    :return: Parameter dictionary of usage stats
    """
    ret = {}
    values = dict(zip(
        ('cluster_cmd', 'powerConsumption', 'upTime'),
        struct.unpack('< 2x s I I 1x', data)
    ))
    ret['PowerConsumption'] = values['powerConsumption']
    ret['UpTime'] = values['upTime']

    return ret


def generate_switch_state_request(params):
    """
    Generate Switch State Change request data.
    This message is sent FROM the Hub TO the SmartPlug requesting state change.

    :param params: Parameter dictionary of relay state
    :return: Message data
    """
    if 'State' in params:
        if params['State']:
            # On
            data = b'\x11\x00\x02\x01\x01'
        else:
            # Off
            data = b'\x11\x00\x02\x00\x01'
    else:
        # Check Only
        data = b'\x11\x00\x01\x01'

    return data


def generate_switch_state_update(params):
    """
    Generate Switch State update message data.
    This message is sent TO the Hub FROM the SmartPlug advertising state change.

    :param params: Parameter dictionary of relay state
    :return: Message data
    """
    checksum = b'\th'
    cluster_cmd = CLUSTER_CMD_AM_STATE_RESP
    payload = b'\x07\x01' if params['State'] else b'\x06\x00'
    data = checksum + cluster_cmd + payload
    return data


def parse_switch_state_request(data):
    """
    Process message, parse for relay state change request.
    This message is sent FROM the Hub TO the SmartPlug requesting state change.

    :param data: Message data
    :return: Parameter dictionary of relay state
    """
    # Parse Switch State Request
    if data == b'\x11\x00\x02\x01\x01':
        return {'State': 1}
    elif data == b'\x11\x00\x02\x00\x01':
        return {'State': 0}
    else:
        logging.error('Unknown State Request')


def parse_switch_state_update(data):
    """
    Process message, parse for switch status.
    This message is sent TO the Hub FROM the SmartPlug advertising state change.

    :param data: Message data
    :return: Parameter dictionary of switch status
    """
    values = struct.unpack('< 2x b b b', data)
    if values[2] & 0x01:
        return {'State': 1}
    else:
        return {'State': 0}


def parse_tamper_state(data):
    """
    Process message, parse for Tamper Switch State Change

    :param data: Message data
    :return: Parameter dictionary of tamper status
    """
    ret = {}
    if ord(data[3]) == 0x02:
        ret['TamperSwitch'] = 'OPEN'
    else:
        ret['TamperSwitch'] = 'CLOSED'

    return ret


def parse_button_press(data):
    """
    Process message, parse for button press status

    :param data: Message data
    :return: Parameter dictionary of button status
    """
    ret = {}
    if data[2] == b'\x00':
        ret['State'] = 0
    elif data[2] == b'\x01':
        ret['State'] = 1

    ret['Counter'] = struct.unpack('<H', data[5:7])[0]

    return ret


def parse_security_state(data):
    """
    Process message, parse for security state

    :param data: Message data
    :return: Parameter dictionary of security state
    """
    ret = {}
    # The switch state is in byte [3] and is a bitfield
    # bit 0 is the magnetic reed switch state
    # bit 3 is the tamper switch state
    state = ord(data[3])
    if state & 0x01:
        ret['ReedSwitch']  = 'OPEN'
    else:
        ret['ReedSwitch']  = 'CLOSED'

    if state & 0x04:
        ret['TamperSwitch'] = 'CLOSED'
    else:
        ret['TamperSwitch'] = 'OPEN'

    return ret


def parse_status_update(data):
    """
    Process message, parse for status update

    :param data: Message data
    :return: Parameter dictionary of state
    """
    ret = {}
    status = data[3]
    if status == b'\x1b':
        # Power Clamp
        # Unknown
        pass

    elif status == b'\x1c':
        # Power Switch
        # Unknown
        pass

    elif status == b'\x1d':
        # Key Fob
        ret['TempFahrenheit'] = float(struct.unpack("<h", data[8:10])[0]) / 100.0 * 1.8 + 32
        ret['Counter'] = struct.unpack('<I', data[4:8])[0]

    elif status == b'\x1e' or status == b'\x1f':
        # Door Sensor
        ret['TempFahrenheit'] = float(struct.unpack("<h", data[8:10])[0]) / 100.0 * 1.8 + 32
        if ord(data[-1]) & 0x01 == 1:
            ret['ReedSwitch']  = 'OPEN'
        else:
            ret['ReedSwitch']  = 'CLOSED'

        if ord(data[-1]) & 0x02 == 0:
            ret['TamperSwitch'] = 'OPEN'
        else:
            ret['TamperSwitch'] = 'CLOSED'

    else:
        logging.error('Unrecognised Device Status %r  %r', status, data)

    return ret


def generate_missing_link(params=None):
    """
    Generate Missing Link. Not sure what this is yet?

    :param params: Parameter dictionary (none required)
    :return: Message data
    """
    data = b'\x11\x39\xfd'
    return data


def generate_security_init(params=None):
    """
    Generate Security Init. Keeps security devices joined?

    :param params: Parameter dictionary (none required)
    :return: Message data
    """
    data = b'\x11\x80\x00\x00\x05'
    return data


def generate_active_endpoints_request(params):
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

    :param params: addr_short
    """
    addr_short = params['AddressShort']
    data = b'\xaa' + addr_short[1] + addr_short[0]
    return data


def generate_match_descriptor_request(params=None):
    """
    Generate Match Descriptor Request
    Broadcast or unicast transmission used to discover the device(s) that supports
    a specified profile ID and/or clusters.

    Field Name       Size (bytes)   Description
    Network Address  2              16-bit address of a device in the network whose
                                    power descriptor is being requested.
    Profile ID       2              Profile ID to be matched at the destination.
    Number of Input  1              The number of input clusters in the In Cluster
    Clusters                        List for matching. Set to 0 if no clusters supplied.
    Input Cluster    2*             List of input cluster IDs to be used for matching.
    List
    Number of Output 1              The number of output clusters in the Output Cluster
    Clusters                        List for matching. Set to 0 if no clusters supplied.
    Output Cluster   2*             List of output cluster IDs to be used for matching.
    List
                      * Number of Input Clusters

    :param params:
    """
    data = b'\x03\xfd\xff\x16\xc2\x00\x01\xf0\x00'
    return data


def generate_match_descriptor_response(params):
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

    :param params: rf_data
    """
    rf_data = params['rf_data']
    data = rf_data[0:1] + b'\x00\x00\x00\x01\x02'
    return data

