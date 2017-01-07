#! /usr/bin/python

# Filename:    pi-smartplug.py
# Description: Communicate with Hive/AlertMe devices via a XBee
# Author:      James Saunders [james@saunders-family.net]
# Copyright:   Copyright (C) 2016 James Saunders
# License:     MIT
# Version:     0.0.3

from xbee import ZigBee
import serial
import logging
import time
import sys
from classes import *
import pprint

pp = pprint.PrettyPrinter(indent=4)
logger = logging.getLogger('pihive')
logger.setLevel(logging.DEBUG)

# Serial Configuration
XBEE_PORT = '/dev/tty.usbserial-A1014P7W' # MacBook Serial Port
XBEE_BAUD = 9600
serialObj = serial.Serial(XBEE_PORT, XBEE_BAUD)

deviceObj = SmartPlug(serialObj)

message = deviceObj.get_action('broadcast')
deviceObj.send_message(message, deviceObj.BROADCAST_LONG, deviceObj.BROADCAST_SHORT)
deviceObj.logger.debug('Discovery Phase: Sent Broadcast')

# Actions Phase
while True:
    try:
        time.sleep(0.001)

        print("Change plug state:\n")
        state = raw_input("")
        deviceObj.set_state(state)

    except IndexError:
        print "No Command"

    except KeyboardInterrupt:
        print "Keyboard Interrupt"
        break

    except NameError as e:
        print "Name Error:",
        print e.message.split("'")[1]

    except:
        print "Unexpected Error:", sys.exc_info()[0], sys.exc_info()[1]


# Close up shop
print("Closing Serial Port")
deviceObj.halt()
serialObj.close()
