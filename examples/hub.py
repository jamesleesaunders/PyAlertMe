#!/usr/bin/python
# coding: utf-8

# Filename:    hub.py
# Description: Communicate with Hive/AlertMe devices via a XBee
# Author:      James Saunders [james@saunders-family.net]
# Copyright:   Copyright (C) 2017 James Saunders
# License:     MIT
# Version:     0.1.3

import serial
import logging
import time
import sys
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
XBEE_PORT = '/dev/tty.usbserial-A1014P7W' # MacBook Serial Port
XBEE_BAUD = 9600
serialObj = serial.Serial(XBEE_PORT, XBEE_BAUD)

hubObj = Hub(serialObj)

# Kick off discovery thread
hubObj.discovery()

# Actions Phase
while True:
    try:
        time.sleep(0.001)

        nodes = hubObj.get_nodes()
        pp.pprint(nodes)
        print("Select device:\n")
        node_id = raw_input("")

        while True:
            pp.pprint(hubObj.list_actions())
            print("Select command:\n")
            action = raw_input("")
            message = hubObj.get_action(action)

            dest_addr_long = nodes[int(node_id)]['AddressLong']
            dest_addr_short = b's\xba'
            pp.pprint(dest_addr_long)
            pp.pprint(dest_addr_short)
            hubObj.send_message(message, dest_addr_long, dest_addr_short)

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
hubObj.halt()
serialObj.close()
