import logging
import struct
import copy

# ZigBee Addressing
BROADCAST_LONG = b'\x00\x00\x00\x00\x00\x00\xff\xff' 
BROADCAST_SHORT = b'\xff\xfd'

# ZigBee Profile IDs
PROFILE_ID_ZDP     = b'\x00\x00'  # ZigBee Device Profile
PROFILE_ID_HA      = b'\x01\x04'  # HA Device Profile
PROFILE_ID_LL      = b'\xc0\x5e'  # Light Link Profile
PROFILE_ID_ALERTME = b'\xc2\x16'  # AlertMe Private Profile

# ZigBee Endpoints
ENDPOINT_ZDO       = b'\x00'      # ZigBee Device Objects Endpoint
ENDPOINT_ALERTME   = b'\x02'      # AlertMe / Iris Endpoint

# ZDP Status
ZDP_STATUS_OK         = b'\x00'
ZDP_STATUS_INVALID    = b'\x80'
ZDP_STATUS_NOT_FOUND  = b'\x81'

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
CLUSTER_ID_AM_SECURITY  = b'\x05\x00'

# AlertMe Cluster Commands
CLUSTER_CMD_AM_SECURITY        = b'\x00'  # Security Event (Sensors)
CLUSTER_CMD_AM_STATE_REQ       = b'\x01'  # State Request (SmartPlug)
CLUSTER_CMD_AM_STATE_CHANGE    = b'\x02'  # Change State (SmartPlug)
CLUSTER_CMD_AM_STATE_RESP      = b'\x80'  # Switch Status Update
CLUSTER_CMD_AM_PWR_DEMAND      = b'\x81'  # Power Demand Update
CLUSTER_CMD_AM_PWR_CONSUMPTION = b'\x82'  # Power Consumption & Uptime Update
CLUSTER_CMD_AM_PWR_UNKNOWN     = b'\x86'  # Unknown British Gas Power Meter Update
CLUSTER_CMD_AM_MODE_REQ        = b'\xfa'  # Mode Change Request
CLUSTER_CMD_AM_STATUS          = b'\xfb'  # Status Update
CLUSTER_CMD_AM_VERSION_REQ     = b'\xfc'  # Version Information Request
CLUSTER_CMD_AM_RSSI            = b'\xfd'  # RSSI Range Test Update
CLUSTER_CMD_AM_VERSION_RESP    = b'\xfe'  # Version Information Response

# At the moment I am not sure what/if the following dictionary will be used?
# It is here to describe the relationship between Cluster ID and Cmd.
# One day this dict may be used by the process_message() function and link with the parse_xxxxx() functions?
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
        'name': 'Relay State Request',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_SWITCH,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda params: generate_switch_state_request(params)
        }
    },
    'switch_state_update': {
        'name': 'Relay State Update',
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
    'status_update': {
        'name': 'Status Update',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_STATUS,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda params: generate_status_update(params)
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
    'power_consumption_update': {
        'name': 'Power Consumption Update',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_POWER,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda params: generate_power_consumption_update(params)
        }
    },
    'button_press': {
        'name': 'Button Press',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_BUTTON,
            'src_endpoint': ENDPOINT_ALERTME,
            'dest_endpoint': ENDPOINT_ALERTME,
            'data': lambda params: generate_button_press(params)
        }
    },
    'security_init': {
        'name': 'Security Initialization',
        'frame': {
            'profile': PROFILE_ID_ALERTME,
            'cluster': CLUSTER_ID_AM_SECURITY,
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

        # If 'data' is a lambda, then call it and replace with the return value
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


def generate_version_info_update(params):
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
    preamble = b'\tq'
    cluster_cmd = CLUSTER_CMD_AM_VERSION_RESP
    payload = struct.pack('H', params['Version']) \
              + b'\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0b' \
              + params['Manufacturer'] \
              + '\n' + params['Type'] \
              + '\n' + params['ManufactureDate']

    data = preamble + cluster_cmd + payload
    return data


def parse_version_info_update(data):
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
    # We therefore have to calculate the length of the string which we then use in the unpack.
    l = len(data) - 22
    ret = dict(zip(
        ('ClusterCmd', 'Version', 'ManuString'),
        struct.unpack('< 2x s H 17x %ds' % l, data)
    ))

    # Break down the version string into its component parts
    # AlertMe.com\nSmartPlug\n2013-09-26
    ret['ManuString'] = str(ret['ManuString'].decode()) \
        .replace('\t', '\n') \
        .replace('\r', '\n') \
        .replace('\x0e', '\n') \
        .replace('\x0b', '\n') \
        .replace('\x06', '\n') \
        .replace('\x04', '\n') \
        .replace('\x12', '\n')
    (ret['Manufacturer'], ret['Type'], ret['ManufactureDate']) = ret['ManuString'].split('\n')

    # Delete not required keys
    del ret['ManuString']
    del ret['ClusterCmd']

    return ret


def generate_range_update(params):
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
    preamble = b'\t+'
    cluster_cmd = CLUSTER_CMD_AM_RSSI
    payload = struct.pack('B 1x', params['RSSI'])

    data = preamble + cluster_cmd + payload
    return data


def parse_range_info_update(data):
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
        ('cluster_cmd', 'RSSI'),
        struct.unpack('< 2x s B 1x', data)
    ))
    rssi = values['RSSI']
    return {'RSSI' : rssi}


def generate_power_demand_update(params):
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
    preamble = b'\tj'
    cluster_cmd = CLUSTER_CMD_AM_PWR_DEMAND
    payload = struct.pack('H', params['PowerDemand'])

    data = preamble + cluster_cmd + payload
    return data


def generate_power_consumption_update(params):
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
        'PowerConsumption': 19973,
        'UpTime': 33207
    }
    # At the moment this just generates a hard coded message.
    # Also see parse_power_consumption().
    data = b'\tn\x82\x05N\x00\x00\xb7\x81\x00\x00\x01'

    return data


def parse_power_demand(data):
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
    values = dict(zip(
        ('cluster_cmd', 'power_demand'),
        struct.unpack('< 2x s H', data)
    ))

    return {'PowerDemand': values['power_demand']}


def parse_power_unknown(data):
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
    return {'PowerDemand': value}


def parse_power_consumption(data):
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
    ret = {}
    values = dict(zip(
        ('cluster_cmd', 'powerConsumption', 'upTime'),
        struct.unpack('< 2x s I I 1x', data)
    ))
    ret['PowerConsumption'] = values['powerConsumption']
    ret['UpTime'] = values['upTime']

    return ret


def generate_mode_change_request(params):
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
    payload = b'\x00\x01' # Default normal if no mode

    mode = params['Mode']
    if mode == 'Normal':
        payload = b'\x00\x01'
    elif mode == 'RangeTest':
        payload = b'\x01\x01'
    elif mode == 'Locked':
        payload = b'\x02\x01'
    elif mode == 'Silent':
        payload = b'\x03\x01'
    else:
        logging.error('Invalid mode request %s', mode)

    data = preamble + cluster_cmd + payload
    return data


def generate_switch_state_request(params):
    """
    Generate Switch State Change request data.
    This message is sent FROM the Hub TO the SmartPlug requesting state change.

    Field Name                 Size       Description
    ----------                 ----       -----------
    Preamble                   2          Unknown Preamble TBC
    Cluster Command            1          Cluster Command - Change State (SmartPlug) (b'\x01' / b'\x02')
    Requested Relay State      2*         b'\x01' = Check Only, b'\x01\x01' = On, b'\x00\x01' = Off
                                          * Size = 1 if check only

    :param params: Parameter dictionary of relay state
    :return: Message data
    """
    preamble = b'\x11\x00'

    if 'RelayState' in params:
        cluster_cmd = CLUSTER_CMD_AM_STATE_CHANGE
        if params['RelayState']:
            payload = b'\x01\x01'  # On
        else:
            payload = b'\x00\x01'  # Off
    else:
        # Check Only
        cluster_cmd = CLUSTER_CMD_AM_STATE_REQ
        payload = b'\x01'

    data = preamble + cluster_cmd + payload
    return data


def parse_switch_state_request(data):
    """
    Process message, parse for relay state change request.
    This message is sent FROM the Hub TO the SmartPlug requesting state change.

    Field Name                 Size       Description
    ----------                 ----       -----------
    Preamble                   2          Unknown Preamble TBC
    Cluster Command            1          Cluster Command - Change State (SmartPlug) (b'\x02')
    Requested Relay State      2          b'\x01\x01' = On, b'\x00\x01' = Off

    :param data: Message data
    :return: Parameter dictionary of relay state
    """
    # Parse Switch State Request
    if data == b'\x11\x00\x02\x01\x01':
        return {'RelayState': 1}
    elif data == b'\x11\x00\x02\x00\x01':
        return {'RelayState': 0}
    else:
        logging.error('Unknown State Request')


def generate_switch_state_update(params):
    """
    Generate Switch State update message data.
    This message is sent TO the Hub FROM the SmartPlug advertising state change.

    Field Name                 Size       Description
    ----------                 ----       -----------
    Preamble                   2          Unknown Preamble TBC
    Cluster Command            1          Cluster Command - Switch Status Update (b'\x80')
    Relay State                2          b'\x07\x01' = On, b'\x06\x00' = Off

    :param params: Parameter dictionary of relay state
    :return: Message data
    """
    preamble = b'\th'
    cluster_cmd = CLUSTER_CMD_AM_STATE_RESP
    payload = b'\x07\x01' if params['RelayState'] else b'\x06\x00'

    data = preamble + cluster_cmd + payload
    return data


def parse_switch_state_update(data):
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
        return {'RelayState': 1}
    else:
        return {'RelayState': 0}


def generate_button_press(self):
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
        'ButtonState': 1,
        'Counter': 62552
    }
    # At the moment this just generates a hard coded message.
    # Also see parse_button_press().
    data = b'\t\x00\x01\x00\x01X\xf4\x00\x00'

    return data


def parse_button_press(data):
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
        ret['ButtonState'] = 0
    elif ord(data[2]) == 0x01:
        ret['ButtonState'] = 1

    ret['Counter'] = struct.unpack('<H', data[5:7])[0]

    return ret


def parse_tamper_state(data):
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
        ret['TamperState'] = 1  # Open
    else:
        ret['TamperState'] = 0  # Closed

    ret['Counter'] = struct.unpack('<H', data[4:6])[0]

    return ret


def parse_security_state(data):
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
        ret['TriggerState'] = 1  # Open
    else:
        ret['TriggerState'] = 0  # Closed

    if state & 0x04:
        ret['TamperState'] = 1  # Open
    else:
        ret['TamperState'] = 0  # Closed

    return ret


def generate_security_init(params=None):
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


def parse_status_update(data):
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
    type = data[3]
    if type == b'\x1b':
        # Power Clamp
        # Unknown
        pass

    elif type == b'\x1c':
        # Power Switch
        # Unknown
        pass

    elif type == b'\x1d':
        # Key Fob
        ret['Temperature'] = float(struct.unpack("<h", data[8:10])[0]) / 100.0 * 1.8 + 32
        ret['Counter'] = struct.unpack('<I', data[4:8])[0]

    elif type == b'\x1e' or type == b'\x1f':
        # Door Sensor
        ret['Temperature'] = float(struct.unpack("<h", data[8:10])[0]) / 100.0 * 1.8 + 32
        if ord(data[-1]) & 0x01 == 1:
            ret['TriggerState'] = 1  # Open
        else:
            ret['TriggerState'] = 0  # Closed

        if ord(data[-1]) & 0x02 == 0:
            ret['TamperState'] = 1  # Open
        else:
            ret['TamperState'] = 0  # Closed

    else:
        logging.error('Unrecognised Device Status %r  %r', type, data)

    return ret


def generate_status_update(params):
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
        'TriggerState': 0,
        'Temperature': 106.574,
        'TamperState': 1
    }
    # At the moment this just generates a hard coded message.
    # The below is just one type of status update, see parse_status_update() for more.
    data = b'\t\r\xfb\x1f<\xf1\x08\x02/\x10D\x02\xcf\xff\x01\x00'

    return data


def generate_active_endpoints_request(params):
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
    sequence = struct.pack('B', params['Sequence'])                   # b'\xaa'
    net_addr = params['AddressShort'][1] + params['AddressShort'][0]  # b'\x9f\x88'

    data = sequence + net_addr
    return data


def generate_match_descriptor_request(params):
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
    sequence = struct.pack('B', params['Sequence'])                                  # b'\x01'
    net_addr = params['AddressShort'][1] + params['AddressShort'][0]                 # b'\xfd\xff'
    profile_id = params['ProfileId'][1] + params['ProfileId'][0]                     # b'\x16\xc2'  PROFILE_ID_ALERTME (reversed)
    num_input_clusters = struct.pack('B', len(params['InClusterList']) / 2)          # b'\x00'
    input_cluster_list = params['InClusterList']                                     # b''
    num_output_clusters = struct.pack('B', len(params['OutClusterList']) / 2)        # b'\x01'
    output_cluster_list = params['OutClusterList'][1] + params['OutClusterList'][0]  # b'\xf0\x00'  CLUSTER_ID_AM_STATUS (reversed)

    data = sequence + net_addr + profile_id + num_input_clusters + input_cluster_list + num_output_clusters + output_cluster_list
    return data


def generate_match_descriptor_response(params):
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
    sequence   = struct.pack('B', params['Sequence'])                   # b'\x04'
    status     = ZDP_STATUS_OK                                          # b'\x00'
    net_addr   = params['AddressShort'][1] + params['AddressShort'][0]  # b'\x00\x00'
    length     = struct.pack('B', len(params['EndpointList']))          # b'\x01'
    match_list = params['EndpointList']                                 # b'\x02'

    data = sequence + status + net_addr + length + match_list
    return data

