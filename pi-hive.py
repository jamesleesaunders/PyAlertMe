#! /usr/bin/python

# Filename:    pi-hive.py
# Description: Communicate with a Hive SmartPlug via a XBee
# Author:      James Saunders [james@saunders-family.net]
# Copyright:   Copyright (C) 2016 James Saunders
# License:     MIT
# Version:     0.0.1"

from xbee import ZigBee
from struct import unpack
import serial
import time
import sys
from classes import *
import pprint
pp = pprint.PrettyPrinter(indent=4)

# Serial Configuration
XBEE_PORT = '/dev/tty.usbserial-A1014P7W' # MacBook Serial Port
# XBEE_PORT = '/dev/ttyUSB0' # Rasberry Pi Serial Port
XBEE_BAUD = 9600
serialPort = serial.Serial(XBEE_PORT, XBEE_BAUD)
zb = ZigBee(ser = serialPort)

# ZigBee Profile IDs
ZDP_PROFILE_ID = '\x00\x00' # Zigbee Device Profile
ALERTME_PROFILE_ID = '\xc2\x16' # AlertMe Private Profile

# ZigBee Addressing
BROADCAST_LONG = '\x00\x00\x00\x00\x00\x00\xff\xff'
BROADCAST_SHORT = '\xff\xfe'





def sendMessage(destLongAddr, destShortAddr, srcEndpoint, destEndpoint, clusterId, profileId, data):
    zb.send('tx_explicit',
        dest_addr_long = destLongAddr,
        dest_addr = destShortAddr,
        src_endpoint = srcEndpoint,
        dest_endpoint = destEndpoint,
        cluster = clusterId,
        profile = profileId,
        data = data
    )





# Discovery 60 seconds
t_start = time.time()
t_end = time.time() + (30 * 15)
devicecount = 0
devices = {}
discovered_devices = {}

while time.time() < t_end:
    # Send out a broadcast every 10 seconds to provoke a response
    if ( time.time() == t_start + (10 * 15) ):
        data = '\x12' + '\x01'
        sendMessage(BROADCAST_LONG, BROADCAST_SHORT, '\x00', '\x00', '\x00\x32', ZDP_PROFILE_ID, data)
    
    # Wait for frame
    message = zb.wait_read_frame()
    pp.pprint(message)

    address = message['source_addr_long']
    if (not address in discovered_devices):

        # Do we already know about this device? If not create a new object for it...
        if (not address in devices):
            devices[address] = Device(zb, address)

        # Send our message data to the device
        devices[address].receiveMessage(message);

        # If we have identified the device type we are almost there! 
        if (devices[address].getType()):
            # Ask user to name the device...
            print "What do you want to name this device:"
            name = raw_input("")
        
            # Create a more specific object
            if ( devices[address].getType() == 'SmartPlug' ):
                discovered_devices[address] = SmartPlug(zb, address, name);

            if ( devices[address].getType() == 'Button Device' ):
                discovered_devices[address] = Button(zb, address, name);

            if ( devices[address].getType() == 'PIR Device' ):
                discovered_devices[address] = PIR(zb, address, name);

            # Add to the DB..?

            # Print a few details about this new device
            print discovered_devices[address].getName()
            print discovered_devices[address].getType()
            print Base.prettyMac(discovered_devices[address].getAddress())

            devicecount = devicecount + 1

# Close up shop
print "Closing Serial Port"
zb.halt()
serialPort.close()
