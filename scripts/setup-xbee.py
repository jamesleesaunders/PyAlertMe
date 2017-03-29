"""
Set the XBee sensor parameters.
"""

import serial
import struct
from xbee import ZigBee
from pprint import pprint

def byte(s):
    return struct.pack('>B', s)

def short(s):
    return struct.pack('>H', s)

ser = serial.Serial('/dev/ttyUSB0')
xb = ZigBee(ser)

def wait():
    r = xb.wait_read_frame()
    if r and 'command' in r:
        print r['command']
    
    if r and 'status' in r and r['status'] != byte(0x00):
        pprint(r)

# target a particular device
dest = struct.pack('>Q',0x0013a2004031f790)
# broadcast
#dest = struct.pack('>Q',0x00000000FFFF)


# Some description of the sensor here
# http://www.digi.com/wiki/developer/index.php/XBee_Sensors

# enable analog input for light, temperature, and humidity
xb.remote_at(command='D1', parameter=byte(0x02), dest_addr_long=dest)
wait()

xb.remote_at(command='D2', parameter=byte(0x02), dest_addr_long=dest)
wait()

xb.remote_at(command='D3', parameter=byte(0x02), dest_addr_long=dest)
wait()

# wiki says to enable digital input on the battery monitoring pin
xb.remote_at(command='P1', parameter=byte(0x03), dest_addr_long=dest)
wait()


# set up sleep

# set child timeout on local router (3*SP*SN)
xb.at(command='SP', parameter=short(0x03e8))
wait()
xb.at(command='SN', parameter=short(0x60))
wait()

# set power level (0 -8dBm,  1 -4 dBm, 2 -2 dBm, 3 -0 dBm, 4 +2 dBm)
xb.remote_at(command='PL', parameter=byte(0x04), dest_addr_long=dest)
wait()

# in units of 10ms
# range of 0x20 - 0xAF0
#xb.remote_at(command='SP', parameter=short(0x03e8), dest_addr_long=dest)
xb.remote_at(command='SP', parameter=short(0x03e8), dest_addr_long=dest)
#xb.remote_at(command='SP', parameter=b'\x07\xd0', dest_addr_long=dest)
wait()
# number of sleep periods (sleep = SP * SN)
xb.remote_at(command='SN', parameter=short(0x01), dest_addr_long=dest)
wait()

# sleep entire time
xb.remote_at(command='SO', parameter=byte(0x04), dest_addr_long=dest)
wait()

# set wake time
# in units of 1ms
xb.remote_at(command='ST', parameter=short(0x0fa0), dest_addr_long=dest)
wait()

# send sensor readings every x ms once awake
# in units of 1ms
xb.remote_at(command='IR', parameter=short(0x03e8), dest_addr_long=dest)
wait()

# enable cyclic sleep
xb.remote_at(command='SM', parameter=byte(0x04), dest_addr_long=dest)
wait()

