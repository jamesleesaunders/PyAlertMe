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
logger.setLevel(logging.DEBUG)

# Specify log message format
formatter = logging.Formatter('%(asctime)s %(levelname)-3s %(module)-5s %(message)s')

# Create console handler and set level to info
sh = logging.StreamHandler()
sh.setLevel(logging.ERROR)
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

def callback(type, node_id, field, value):
    if type == 'Attribute':
        print("Attribute Update\n\tNode ID: " + node_id + "  Field: " + field + "  Value: " + str(value))
    elif type == 'Node':
        print("Node Update\n\tNode ID: " + node_id + "  Field: " + field + "  Value: " + str(value))

# Create Hub Object
hub_obj = Hub()
hub_obj.start(ser)

# Kick Off Discovery
hub_obj.discovery()

# Actions Phase
while True:
    try:
        time.sleep(0.001)

        # List Devices
        pp.pprint(hub_obj.list_devices())
        print("Select Device:\n")
        node_id = raw_input("")

        while True:
            device_obj = hub_obj.devices[node_id]
            pp.pprint(vars(device_obj))
            pp.pprint(device_obj.list_messages())

            # Select Message
            message_id = raw_input("Select Message: ")

            # Select Parameters
            params = {}
            if 'expected_params' in messages[message_id].keys():
                print("Message Parameters:")
                for param_name in messages[message_id]['expected_params']:
                    param_value = raw_input("   %s: " % param_name)
                    params = {param_name: param_value}

            # Send Message
            message = get_message(message_id, params)
            addresses = hub_obj.device_obj_to_addrs(device_obj)
            hub_obj.send_message(message, *addresses)

    except IndexError:
        print("No Command")

    except KeyboardInterrupt:
        print("Keyboard Interrupt")
        break

    except NameError as e:
        print("Name Error:")
        print(e.message.split("'")[1])

    except:
        print("Unexpected Error:", sys.exc_info()[0], sys.exc_info()[1])


# Close up shop
print("Closing Serial Port")
hub_obj.halt()
