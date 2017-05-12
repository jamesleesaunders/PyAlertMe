import logging
import struct
import copy

# Zigbee Profile IDs
ZDP_PROFILE_ID     = b'\x00\x00'  # Zigbee Device Profile
HA_PROFILE_ID      = b'\x01\x04'  # HA Device Profile
LL_PROFILE_ID      = b'\xc0\x5e'  # Light Link Profile
ALERTME_PROFILE_ID = b'\xc2\x16'  # AlertMe Private Profile

# Zigbee Addressing
BROADCAST_LONG = b'\x00\x00\x00\x00\x00\x00\xff\xff'
BROADCAST_SHORT = b'\xff\xfe'

messages = {
    'version_info_request': {
        'name': 'Version Info Request',
        'frame': {
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xf6',
            'profile': ALERTME_PROFILE_ID,
            'data': lambda params: generate_version_info_request(params)
        }
    },
    'version_info_update': {
        'name': 'Version Info Update',
        'frame': {
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xf6',
            'profile': ALERTME_PROFILE_ID,
            'data': lambda params: generate_version_info_update(params)
        }
    },
    'switch_state_request': {
        'name': 'Switch State Request',
        'frame': {
            'profile': ALERTME_PROFILE_ID,
            'cluster': b'\x00\xee',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': lambda params: generate_switch_state_request(params)
        }
    },
    'switch_state_update': {
        'name': 'Switch State Update',
        'frame': {
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xee',
            'profile': ALERTME_PROFILE_ID,
            'data': lambda params: generate_switch_state_update(params)
        }
    },
    'mode_change_request': {
       'name': 'Mode Change Request',
       'frame': {
           'profile': ALERTME_PROFILE_ID,
           'cluster': b'\x00\xf0',
           'src_endpoint': b'\x00',
           'dest_endpoint': b'\x02',
           'data': lambda params: generate_mode_change_request(params)
       }
    },
    'range_info_update': {
        'name': 'Range Info Update',
        'frame': {
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xf6',
            'profile': ALERTME_PROFILE_ID,
            'data': lambda params: generate_range_update(params)
        }
    },
    'power_demand_update': {
        'name': 'Power Demand Update',
        'frame': {
            'profile': ALERTME_PROFILE_ID,
            'cluster': b'\x00\xef',
            'src_endpoint': b'\x02',
            'dest_endpoint': b'\x02',
            'data': lambda params: generate_power_demand_update(params)
        }
    },
    'missing_link': {
        'name': 'Missing Link',
        'frame': {
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'cluster': b'\x00\xf0',
            'profile': ALERTME_PROFILE_ID,
            'data': lambda params: generate_missing_link(params)
        }
    },
    'security_init': {
        'name': 'Security Initialization',
        'frame': {
            'profile': ALERTME_PROFILE_ID,
            'cluster': b'\x05\x00',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x02',
            'data': lambda params: generate_security_init(params)
        }
    },
    'active_endpoint_request': {
        'name': 'Active Endpoints Request',
        'frame': {
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x00',
            'cluster': b'\x00\x05',
            'profile': ZDP_PROFILE_ID,
            'data': b'\x00\x00'
        }
    },
    'match_descriptor_request': {
        'name': 'Match Descriptor Request',
        'frame': {
            'profile': ZDP_PROFILE_ID,
            'cluster': b'\x00\x06',
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x00',
            'data': b'\x03\xfd\xff\x16\xc2\x00\x01\xf0\x00'
        }
    },
    'match_descriptor_response': {
        'name': 'Match Descriptor Response',
        'frame': {
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x00',
            'cluster': b'\x80\x06',
            'profile': ZDP_PROFILE_ID,
            'data': b'\x00\x00\x00\x00\x01\x02'
        }
    },
    'routing_table_request': {
        'name': 'Management Routing Table Request',
        'frame': {
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x00',
            'cluster': b'\x00\x32',
            'profile': ZDP_PROFILE_ID,
            'data': b'\x12\x01'
        }
    },
    'permit_join_request': {
        'name': 'Management Permit Join Request',
        'frame': {
            'src_endpoint': b'\x00',
            'dest_endpoint': b'\x00',
            'cluster': b'\x00\x36',
            'profile': ZDP_PROFILE_ID,
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
    cluster_cmd = b'\xfe'
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
    cluster_cmd = b'\xfd'
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
    cluster_cmd = b'\x81'
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


def generate_switch_state_request(params=None):
    """
    Generate Switch State Change request data.
    This message is sent FROM the Hub TO the SmartPlug requesting state change.

    :param params: Parameter dictionary of relay state
    :return: Message data
    """
    if params is None:
        params = {}
    data = b'\x11\x00\x01\x01'
    if 'State' in params.keys():
        if params['State'] == 1:
            # On
            data = b'\x11\x00\x02\x01\x01'
        elif params['State'] == 0:
            # Off
            data = b'\x11\x00\x02\x00\x01'
        elif params['State'] == '':
            # Check
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
    cluster_cmd = b'\x80'
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
        return 1
    elif data == b'\x11\x00\x02\x00\x01':
        return 0
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
    if (state & 0x01):
        ret['ReedSwitch']  = 'OPEN'
    else:
        ret['ReedSwitch']  = 'CLOSED'

    if (state & 0x04):
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














def temp_generate_active_endpoints_request(addr_short):
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

    :param addr_short:
    """
    data = b'\xaa' + addr_short[1] + addr_short[0]
    message = {
        'description': 'Active Endpoints Request',
        'profile': ZDP_PROFILE_ID,
        'cluster': b'\x00\x05',
        'src_endpoint': b'\x00',
        'dest_endpoint': b'\x00',
        'data': data
    }
    return message



def temp_generate_match_descriptor_request():
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
    """
    data = b'\x03\xfd\xff\x16\xc2\x00\x01\xf0\x00'
    message = {
        'description': 'Match Descriptor Request',
        'profile': ZDP_PROFILE_ID,
        'cluster': b'\x00\x06',
        'src_endpoint': b'\x00',
        'dest_endpoint': b'\x00',
        'data': data
    }
    return message


def temp_generate_match_descriptor_response(rf_data):
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

    :param rf_data:
    """
    data = rf_data[0:1] + b'\x00\x00\x00\x01\x02'
    message = {
        'description': 'Match Descriptor Response',
        'profile': ZDP_PROFILE_ID,
        'cluster': b'\x80\x06',
        'src_endpoint': b'\x00',
        'dest_endpoint': b'\x00',
        'data': data
    }
    return message