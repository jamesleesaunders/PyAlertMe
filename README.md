# PyAlertMe #

[![Build Status](https://travis-ci.org/jamesleesaunders/PyAlertMe.svg?branch=master)](https://travis-ci.org/jamesleesaunders/PyAlertMe)
[![codecov](https://codecov.io/gh/jamesleesaunders/PyAlertMe/branch/master/graph/badge.svg)](https://codecov.io/gh/jamesleesaunders/PyAlertMe)

PyAlertMe is a set of classes which, when used in conjunction with a Digi XBee (ZigBee) module, can be used to simulate an AlertMe (Lowes Iris, Hive, British Gas Safe and Secure) Hub, SmartPlug or Sensor.

## Use ##
#### Hub ####
```python
# Setup Serial
XBEE_PORT = '/dev/tty.usbserial-DN018OI6'
XBEE_BAUD = 9600
ser = serial.Serial(XBEE_PORT, XBEE_BAUD)

# Define Callback (Optional)
def callback(type, node_id, field, value):
    if type == 'Attribute':
        print("Attribute Update\n\tNode ID: " + node_id + "  Field: " + field + "  Value: " + str(value))
    elif type == 'Node':
        print("Node Update\n\tNode ID: " + node_id + "  Field: " + field + "  Value: " + str(value))

# Create Hub Object
hub_obj = Hub(callback)
hub_obj.start(ser)
```
Example output:
```
2017-08-30 21:51:21,138 INFO zbhub 134 New Device 00:0d:6f:00:00:1b:6a:6a Fully Associated
Attribute Update [Node ID: 00:0d:6f:00:00:1b:6a:6a	Field: manu	Value: AlertMe.com]
Attribute Update [Node ID: 00:0d:6f:00:00:1b:6a:6a	Field: type	Value: Door/Window sensor]
Attribute Update [Node ID: 00:0d:6f:00:00:1b:6a:6a	Field: version	Value: 55979]
Attribute Update [Node ID: 00:0d:6f:00:00:1b:6a:6a	Field: manu_date	Value: 2008-04-17]
{   '00:0d:6f:00:00:1b:6a:6a': {   'manu': 'AlertMe.com',
                                   'type': 'Door/Window sensor',
                                   'version': 55979},
    '00:0d:6f:00:00:1b:76:ea': {   'manu': 'AlertMe.com',
                                   'type': 'Lamp',
                                   'version': 1905},
    '00:0d:6f:00:00:78:61:c0': {   'manu': 'AlertMe.com',
                                   'type': 'Button Device',
                                   'version': 34667},
    '00:0d:6f:00:03:bb:b9:f8': {   'manu': 'AlertMe.com',
                                   'type': 'SmartPlug',
                                   'version': 9586}}
Select Device:Attribute Update [Node ID: 00:0d:6f:00:03:bb:b9:f8	Field: power_demand	Value: 0]
Attribute Update [Node ID: 00:0d:6f:00:03:bb:b9:f8	Field: trigger_state	Value: 0]
Attribute Update [Node ID: 00:0d:6f:00:03:bb:b9:f8	Field: temperature	Value: 99.05]
Attribute Update [Node ID: 00:0d:6f:00:03:bb:b9:f8	Field: tamper_state	Value: 1]
Attribute Update [Node ID: 00:0d:6f:00:00:1b:6a:6a	Field: manu	Value: AlertMe.com]
Attribute Update [Node ID: 00:0d:6f:00:00:1b:6a:6a	Field: type	Value: Door/Window sensor]
Attribute Update [Node ID: 00:0d:6f:00:00:1b:6a:6a	Field: version	Value: 55979]
Attribute Update [Node ID: 00:0d:6f:00:00:1b:6a:6a	Field: manu_date	Value: 2008-04-17]
Attribute Update [Node ID: 00:0d:6f:00:03:bb:b9:f8	Field: power_demand	Value: 0]
```

The hub supports the following devices:
* SmartPlug
* Power Clamp
* Button Device
* PIR Device
* Door/Window sensor
* Alarm Detector
* Keyfob Device
* Beacon
* Lamp

#### SmartPlug ####
```python
# Setup Serial
XBEE_PORT = '/dev/tty.usbserial-DN018OI6'
XBEE_BAUD = 9600
ser = serial.Serial(XBEE_PORT, XBEE_BAUD)

# Create SmartPlug Object
device_obj = SmartPlug()
device_obj.start(ser)
```

## XBee Setup ##
Configure XBee as follows:
XBee Modem XB24-ZB, ZIGBEE Coordinator API, Version 21A7 (or better).
Alternatively use you can use [scripts/setup-xbee.py](scripts/setup-xbee.py) to configure the Xbee. 

#### Coordinator (Hub) ####
* ZigBee Stack Profile (ZS): 2
* Encryption Enable (EE): 1
* Encryption Options (EO): 1
* Encryption Key (KY): 5a6967426565416c6c69616e63653039
* API Enable (AP): 2
* API Output Mode (AO): 3

#### Router (Device) ####
* ZigBee Stack Profile (ZS): 2
* Encryption Enable (EE): 1
* Encryption Options (EO): 0
* Encryption Key (KY): None
* API Enable (AP): 2
* API Output Mode (AO): 3

## Example Use ##
See [examples/hub-example.py](examples/hub-example.py) for example Hub.
See [examples/smartplug-example.py](examples/smartplug-example.py) for example SmartPlug.

## Credits ##
Huge thanks to Desert Home http://www.desert-home.com/2014/02/raspberry-pi-and-lowes-iris-smart-switch.html from which this project originates from.
