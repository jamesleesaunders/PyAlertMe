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

def receive_message(message):
    if message and 'command' in message:
        pp.pprint(message['parameter'])

def xbee_error(error):
    print('XBee Error: %s', error)


XBEE_PORT = '/dev/tty.usbserial-DN018OI6'
XBEE_BAUD = 9600
ser = serial.Serial(XBEE_PORT, XBEE_BAUD)
zb = ZigBee(ser=ser, callback=receive_message, error_callback=xbee_error, escaped=True)

# Get Addresses
print ("Sending MY")
zb.at( command='MY', frame=0x01) # Short Address
time.sleep(3)

print ("Sending SH")
zb.at(command='SH', frame=0x02) # Long Address High
time.sleep(3)

print ("Sending SL")
zb.at(command='SL', frame=0x03) # Long Address Low
time.sleep(3)

zb.halt()
ser.close()
