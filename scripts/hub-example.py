#!/usr/bin/python
# coding: utf-8

# Filename:    hub-example.py
# Description: Communicate with Hive/AlertMe devices via a XBee
# Author:      James Saunders [james@saunders-family.net]
# Copyright:   Copyright (C) 2017 James Saunders
# License:     MIT

import serial
import logging
import time
import sys
sys.path.insert(0, '../')
from pyalertme import *
import pprint

pp = pprint.PrettyPrinter(indent=4)

logger = logging.getLogger('pyalertme')
logger.setLevel(logging.INFO)

# Specify log message format
formatter = logging.Formatter('%(asctime)s %(levelname)-3s %(module)-5s %(lineno)-3s %(message)s')

# Create console handler and set level to info
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(formatter)
logger.addHandler(sh)

# Create debug file handler and set level to debug
fh = logging.FileHandler("debug.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

# Serial Configuration
XBEE_PORT = '/dev/tty.usbserial-DN018OI6'
# XBEE_PORT = '/dev/cu.usbserial-DN02ZXKE'
# XBEE_PORT = '/dev/tty.usbserial-A1014P7W'
XBEE_BAUD = 9600
ser = serial.Serial(XBEE_PORT, XBEE_BAUD)

# Create Hub Object
hub_obj = ZBHub(ser)

# Kick Off Discovery
hub_obj.discovery()

# Actions Phase
while True:
    try:
        time.sleep(0.001)

        # List Devices
        device_list = hub_obj.list_devices()
        pp.pprint(device_list)
        node_id = raw_input("Select Device:")

        if node_id in device_list.keys():
            while True:
                # Select Message
                device_obj = hub_obj.devices[node_id]
                messages = hub_obj.list_messages()
                pp.pprint(messages)
                message_id = raw_input("Select Message:")

                if message_id in messages.keys():
                    # Select Parameters
                    params = {}
                    if 'expected_params' in messages[message_id].keys():
                        print("Message Parameters:")
                        for param_name in messages[message_id]['expected_params']:
                            param_value = raw_input("   %s: " % param_name)
                            params = {param_name: param_value}

                    # Send Message
                    message = hub_obj.generate_message(message_id, params)
                    addresses = device_obj.addr_tuple
                    hub_obj.send_message(message, *addresses)

                else:
                    break

    except KeyboardInterrupt:
        print("Keyboard Interrupt")
        break

    except:
        print("Unexpected Error:", sys.exc_info()[0], sys.exc_info()[1])

# Close up shop
print("Closing Serial Port")
hub_obj.halt()
