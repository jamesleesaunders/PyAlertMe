# PyAlertMe

Python AlertMe is a set of classes which, used in conjunction with a Digi XBee (Zigbee) module can be used to simulate an AlertMe (or Lowes Iris) hub, sensor or switch.

Possibly also British Gas Hive.


## XBee Setup
XBee Modem XB24-ZB, ZIGBEE Coordinator API, Version 21A7 (or better)

#### Co-ordinator
ZigBee Stack Profile (ZS): 2
* Encryption Enable (EE): 1
* Encryption Options (EO): 1
* Encryption Key (KY): 5a6967426565416c6c69616e63653039
* API Enable (AP): 2
* API Output Mode (AO): 3

#### Router
* ZigBee Stack Profile (ZS): 2
* Encryption Enable (EE): 1
* Encryption Options (EO): 0
* Encryption Key (KY): 5a6967426565416c6c69616e63653039 (possibly empty?)
* API Enable (AP): 2
* API Output Mode (AO): 3



## Packets

#### Range Test
```python
{
'profile': '\xc2\x16', 
'source_addr': '3\x1d', 
'dest_endpoint': '\x02', 
'rf_data': '\t\x00\xfd\xd0w', 
'source_endpoint': '\x02', 
'options': '\x01', 
'source_addr_long': '\x00\ro\x00\x03\xbb\xb9\xf8', 
'cluster': '\x00\xf6', 
'id': 'rx_explicit'
}
```
2017-04-16 23:14:20,046 DEBUG hub   Received RSSI Range Test Update
2017-04-16 23:14:20,046 DEBUG hub   Updating Node Attribute: RSSI Value: 208



```python
{
'profile': '\xc2\x16', 
'source_addr': '3\x1d', 
'dest_endpoint': '\x02', 
'rf_data': '\t+\xfd\xcfw', 
'source_endpoint': '\x02', 
'options': '\x01', 
'source_addr_long': '\x00\ro\x00\x03\xbb\xb9\xf8', 
'cluster': '\x00\xf6', 
'id': 'rx_explicit'
}
```
2017-04-16 23:14:22,017 DEBUG hub   Received RSSI Range Test Update
2017-04-16 23:14:22,017 DEBUG hub   Updating Node Attribute: RSSI Value: 207