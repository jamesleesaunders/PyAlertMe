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


commands = {
    'Addresses': {
        'Short Address':        {'command':'MY', 'param': None},
        'Long Address High':    {'command':'SH', 'param': None},
        'Long Address Low':     {'command':'SL', 'param': None}
    },
    'Setup': {
        'ZigBee Stack Profile': {'command': 'ZS', 'parameter': b'\x02'},
        'Encryption Enable':    {'command': 'EE', 'parameter': b'\x01'},
        'Encryption Options':   {'command': 'EO', 'parameter': b'\x01'},
        'Encryption Key':       {'command': 'KY', 'parameter': b'\x5A\x69\x67\x42\x65\x65\x41\x6C\x6C\x69\x61\x6E\x63\x65\x30\x39'},
        'API Enable':           {'command': 'AP', 'parameter': b'\x02'},
        'API Output Mode':      {'command': 'AO', 'parameter': b'\x03'}
    },
}


def receive_message(message):
    if message and 'command' in message:
        pp.pprint(message)

def xbee_error(error):
    print('XBee Error: %s', error)


XBEE_PORT = '/dev/tty.usbserial-DN018OI6'
XBEE_BAUD = 9600
ser = serial.Serial(XBEE_PORT, XBEE_BAUD)
zb = ZigBee(ser=ser, callback=receive_message, error_callback=xbee_error, escaped=True)


commandset = 'Addresses'
print "Running", commandset, "...."
for name, command in commands[commandset].iteritems():
    print "Sending", name
    zb.at(**command)
    time.sleep(3)

zb.halt()
ser.close()
