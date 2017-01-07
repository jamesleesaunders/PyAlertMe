#! /usr/bin/python

# Filename:    pi-hub.py
# Description: Communicate with Hive/AlertMe devices via a XBee
# Author:      James Saunders [james@saunders-family.net]
# Copyright:   Copyright (C) 2016 James Saunders
# License:     MIT
# Version:     0.0.3

import serial
import logging
import time
import sys
from classes import *
import pprint

pp = pprint.PrettyPrinter(indent=4)

logger = logging.getLogger('pihive')
logger.setLevel(logging.DEBUG)

# Speficy log message format
formatter = logging.Formatter('%(asctime)s %(levelname)-3s %(module)-5s %(message)s')

# create console handler and set level to info
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
logger.addHandler(sh)

# create debug file handler and set level to debug
fh = logging.FileHandler("debug.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)



# Serial Configuration
XBEE_PORT = '/dev/tty.usbserial-A1014P7W' # MacBook Serial Port
XBEE_BAUD = 9600
serialObj = serial.Serial(XBEE_PORT, XBEE_BAUD)

hubObj = Hub(serialObj)

# Discovery Phase
# Send out a broadcast every 30 seconds to provoke a response
timeout = time.time() + 10
while True:
    test = 0
    if time.time() > timeout:
        break

    message = hubObj.get_action('routing_table_request')
    hubObj.send_message(message, hubObj.BROADCAST_LONG, hubObj.BROADCAST_SHORT)
    hubObj.logger.debug('Discovery Phase')
    time.sleep(5.00)

# Actions Phase
while True:
    try:
        time.sleep(0.001)

        pp.pprint(hubObj.list_known_devices())
        print("Select device:\n")
        device_id = raw_input("")

        pp.pprint(hubObj.list_actions())
        print("Select command:\n")
        action = raw_input("")

        message = hubObj.get_action(action)
        devices = hubObj.list_known_devices()
        dest_addr_long = devices[device_id]['addr_long']
        dest_addr = devices[device_id]['addr_short']
        hubObj.send_message(message, dest_addr_long, dest_addr)

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
serial.close()
