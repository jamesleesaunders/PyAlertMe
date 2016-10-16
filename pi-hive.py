#! /usr/bin/python

# Filename:    pi-hive.py
# Description: Communicate with Hive/AlertMe devices via a XBee
# Author:      James Saunders [james@saunders-family.net]
# Copyright:   Copyright (C) 2016 James Saunders
# License:     MIT
# Version:     0.0.2"

from xbee import ZigBee
from struct import unpack
import serial
import logging
import time
import sys
from classes import *
import pprint
pp = pprint.PrettyPrinter(indent=4)
logger = logging.getLogger('pihive')

# ZigBee Profile IDs
ZDP_PROFILE_ID     = b'\x00\x00' # Zigbee Device Profile
ALERTME_PROFILE_ID = b'\xc2\x16' # AlertMe Private Profile

# ZigBee Addressing
BROADCAST_LONG  = b'\x00\x00\x00\x00\x00\x00\xff\xff'
BROADCAST_SHORT = b'\xff\xfe'

# Serial Configuration
XBEE_PORT = '/dev/tty.usbserial-A1014P7W' # MacBook Serial Port
# XBEE_PORT = '/dev/ttyUSB0' # Rasberry Pi Serial Port
XBEE_BAUD = 9600
serialPort = serial.Serial(XBEE_PORT, XBEE_BAUD)


def sendMessages(messages):
    if (len(messages) > 0):
        # Loop round each message in the list
        for message in messages:
            logger.debug('Device Type: %s Sent Message: %s', message['device_type'], message['description'])
            pp.pprint(message)
            # Send message to XBee
            zb.send(
                'tx_explicit',
                dest_addr_long = message['dest_addr_long'],
                dest_addr      = message['dest_addr'],
                src_endpoint   = message['src_endpoint'],
                dest_endpoint  = message['dest_endpoint'],
                cluster        = message['cluster'],
                profile        = message['profile'],
                data           = message['data']
            )
            # Wait between messages
            time.sleep(0.05)

devices = {}

def receiveMessage(message):
    # pp.pprint(message)

    # Grab the long address
    address = message['source_addr_long']
    mac = Base.prettyMac(message['source_addr_long'])

    # Have we already a device with this address?
    if ( not mac in devices ):
        # If not, create a new device object and add it to our list of discovered devices
        devices[mac] = Device(address, 'Unknown Device')
        # TODO: Add to a DB??

    # Has the generic device object managed to determine it is a more specific device type?
    if ( type(devices[mac]) == Device ) and ( devices[mac].getType() != None ):
        device_type = devices[mac].getType()

        # Create a more specific object
        if ( device_type == 'SmartPlug' ):
            devices[mac] = SmartPlug(address, device_type);

        elif ( device_type == 'Button Device' ):
            devices[mac] = Sensor(address, device_type);

        elif ( device_type == 'PIR Device' ):
            devices[mac] = Sensor(address, device_type);

        elif ( device_type == 'Alarm Detector' ):
            devices[mac] = Sensor(address, device_type);

        elif ( device_type == 'Keyfob Device' ):
            devices[mac] = Sensor(address, device_type);

        else:
            logger.error('Unrecognised Device Type: %s', type)
            devices[mac] = Device(address, device_type);

        # Print a few details about this new device
        print(devices[mac].getName())
        print(devices[mac].getType())
        print(Base.prettyMac(devices[mac].getAddress()))

    # Send our recieved message data to the device object
    devices[mac].receiveMessage(message);

    # Do we have any message waiting to be sent back to the device?
    reply = devices[mac].messageQueue();
    sendMessages(reply);

def listDevices():
    for key in devices:
        device = devices.get(key)
        if( device.associated == 1 ):
            print("Address: " + key + " Type: " + device.type  + " Name: " + device.name + "\n")

def xbeeError(error):
    print "XBee Error:", error

# Create ZigBee library API object, which spawns a new thread
zb = ZigBee(ser = serialPort, callback = receiveMessage, error_callback = xbeeError)


# Send out a broadcast every 10 seconds to provoke a response
messages = [{
        'device_name'    : 'Hub',
        'device_type'    : 'Hub',
        'description'    : 'Broacast Discover',
        'dest_addr_long' : BROADCAST_LONG,
        'dest_addr'      : BROADCAST_SHORT,
        'src_endpoint'   : b'\x00',
        'dest_endpoint'  : b'\x00',
        'cluster'        : '\x00\x32',
        'profile'        : ZDP_PROFILE_ID,
        'data'           : '\x12\x01'
}]
sendMessages(messages)
 
while True:
    try:
        time.sleep(0.001)

        listDevices();
        print("Select device:\n")
        mac = raw_input("")

        pp.pprint(devices[mac].listActions())
        print("Select command:\n")
        action = raw_input("")

        reply = devices[mac].getAction(action)
        sendMessages(reply);



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
zb.halt()
serialPort.close()
