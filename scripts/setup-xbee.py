#!/usr/bin/python
# coding: utf-8

# Filename:    setup-xbee.py
# Description: Configure XBee
# Author:      James Saunders [james@saunders-family.net]
# Copyright:   Copyright (C) 2017 James Saunders
# License:     MIT

import serial
from xbee import ZigBee
import pprint
import time

pp = pprint.PrettyPrinter(indent=4)

XBEE_PORT = '/dev/tty.usbserial-A1014P7W' # MacBook Serial Port
XBEE_BAUD = 9600
serialObj = serial.Serial(XBEE_PORT, XBEE_BAUD)
xbee = ZigBee(serialObj)

def wait():
    message = xbee.wait_read_frame()
    pp.pprint(message)
    while True:
        if message and 'command' in message:
            print(message['parameter'])
            break

# Get Addresses
xbee.at(frame='A', command='MY')
wait()
time.sleep(2)

xbee.at(frame='A', command='SH')
wait()
time.sleep(2)

xbee.at(frame='A', command='SL')
wait()
time.sleep(2)