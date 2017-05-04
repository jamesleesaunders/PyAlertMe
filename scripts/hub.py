#!/usr/bin/python
# coding: utf-8

# Filename:    hub.py
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

        nodes = hub_obj.get_nodes()
        pp.pprint(nodes)
        print("Select device:\n")
        node_id = raw_input("")

        while True:
            pp.pprint(hub_obj.list_messages())
            print("Select command:\n")
            action = raw_input("")
            message = hub_obj.get_message(action)
            addresses = hub_obj.node_id_to_addrs(node_id)
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
