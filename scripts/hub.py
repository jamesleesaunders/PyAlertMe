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
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
logger.addHandler(sh)

# Create debug file handler and set level to debug
fh = logging.FileHandler("debug.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

# Serial Configuration
XBEE_PORT = '/dev/tty.usbserial-DN018OI6' # MacBook Serial Port
XBEE_BAUD = 9600
ser = serial.Serial(XBEE_PORT, XBEE_BAUD)

def callback(node_id, attrib_name, value):
    print("Node ID: " + node_id + "  Attribute: " + attrib_name + "  Value: " + str(value))

hub_obj = Hub(callback)
hub_obj.start(ser)

# Kick off discovery thread
# hubObj.discovery()

# Actions Phase
while True:
    try:
        time.sleep(0.001)

        nodes = hub_obj.get_nodes()
        pp.pprint(nodes)
        print("Select device:\n")
        node_id = raw_input("")

        while True:
            pp.pprint(hub_obj.list_actions())
            print("Select command:\n")
            action = raw_input("")
            message = hub_obj.get_action(action)

            dest_addr_long = nodes[node_id]['addr_long']
            dest_addr_short = nodes[node_id]['addr_short']

            pp.pprint(dest_addr_long)
            pp.pprint(dest_addr_short)
            hub_obj.send_message(message, dest_addr_long, dest_addr_short)

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
