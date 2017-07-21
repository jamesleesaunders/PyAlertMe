#!/usr/bin/python
# coding: utf-8

# Filename:    smartplug-example.py
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
formatter = logging.Formatter('%(asctime)s %(levelname)-3s %(module)-5s %(lineno)-3s %(message)s')

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
# XBEE_PORT = '/dev/tty.usbserial-DN018OI6'
XBEE_PORT = '/dev/cu.usbserial-DN0302BW'
# XBEE_PORT = '/dev/tty.usbserial-A1014P7W'
XBEE_BAUD = 9600
ser = serial.Serial(XBEE_PORT, XBEE_BAUD)


def callback(self, attr_name, attr_value):
    print("Attribute Update [Node ID: " + self.id + "\tField: " + attr_name + "\tValue: " + str(attr_value) + "]")

# Create Hub Object
device_obj = ZBSmartPlug(ser)

# Actions Phase
while True:
    try:
        time.sleep(0.001)
        state = int(raw_input(""))
        device_obj.set_switch_state(state)

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
device_obj.halt()
