# PyAlertMe #

Python AlertMe is a set of classes which, used in conjunction with a Digi XBee (Zigbee) module can be used to simulate an AlertMe (or Lowes Iris) hub, sensor or switch.

Possibly also British Gas Hive?

## Use ##
### Hub ###
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
### SmartPlug ###
```python
# Setup Serial
XBEE_PORT = '/dev/tty.usbserial-DN018OI6'
XBEE_BAUD = 9600
ser = serial.Serial(XBEE_PORT, XBEE_BAUD)

# Create SmartPlug Object
device_obj = Hub()
device_obj.start(ser)
```

## XBee Setup
Configure XBee as follows:
XBee Modem XB24-ZB, ZIGBEE Coordinator API, Version 21A7 (or better)

### Coordinator (Hub) ###
ZigBee Stack Profile (ZS): 2
* Encryption Enable (EE): 1
* Encryption Options (EO): 1
* Encryption Key (KY): 5a6967426565416c6c69616e63653039
* API Enable (AP): 2
* API Output Mode (AO): 3

### Router (Device) ###
* ZigBee Stack Profile (ZS): 2
* Encryption Enable (EE): 1
* Encryption Options (EO): 0
* Encryption Key (KY): None
* API Enable (AP): 2
* API Output Mode (AO): 3
