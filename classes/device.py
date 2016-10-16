import pprint
import logging
import sys
from struct import unpack

class Device(object):
    # ZigBee Profile IDs
    ZDP_PROFILE_ID     = b'\x00\x00' # Zigbee Device Profile
    ALERTME_PROFILE_ID = b'\xc2\x16' # AlertMe Private Profile

    # ZigBee Addressing
    BROADCAST_LONG  = b'\x00\x00\x00\x00\x00\x00\xff\xff'
    BROADCAST_SHORT = b'\xff\xfe'

    pp = pprint.PrettyPrinter(indent=4)

    messages = {
        'endpoint_request': {
            'description'   : 'Active Endpoint Request',
            'src_endpoint'  : b'\x00', 
            'dest_endpoint' : b'\x00', 
            'cluster'       : b'\x00\x05', 
            'profile'       : ZDP_PROFILE_ID, 
            'data'          : b'\x00\x00'
        },
        'match_descriptor' : {
            'description'   : 'Match Descriptor',
            'src_endpoint'  : b'\x00', 
            'dest_endpoint' : b'\x00',
            'cluster'       : b'\x80\x06', 
            'profile'       : ZDP_PROFILE_ID, 
            'data'          : b'\x00\x00\x00\x00\x01\x02'
        },
        'hardware_join_1' : {
            'description'   : 'Hardware Join Messages 1',
            'src_endpoint'  : b'\x00', 
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xf6',
            'profile'       : ALERTME_PROFILE_ID, 
            'data'         : b'\x11\x01\xfc'
        },
        'hardware_join_2' : {
            'description'   : 'Hardware Join Messages 2',
            'src_endpoint'  : b'\x00', 
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xf0',
            'profile'       : ALERTME_PROFILE_ID, 
            'data'          : b'\x19\x01\xfa\x00\x01'
        },
        'version_info' : {
            'description'   : 'Version Request',
            'src_endpoint'  : b'\x00', 
            'dest_endpoint' : b'\x02', 
            'cluster'       : b'\x00\xf6', 
            'profile'       : ALERTME_PROFILE_ID, 
            'data'          : b'\x11\x00\xfc\x00\x01'
        }
    }

    def __init__(self, long_address, name="Generic Device"):
        self.type          = None
        self.name          = name
        self.long_address  = long_address
        self.short_address = None
        self.associated    = 0
        self.outgoing_messages = []
        self.incoming_messages = []

        self.logger = logging.getLogger('pihive')

    def getType(self):
        return self.type
  
    def getName(self):
        return self.name

    def getAddress(self):
        return self.long_address

    def listActions(self):
        actions = {};
        for id, message in self.messages.items():
            actions[id] = message['description']
        return actions

    def getAction(self, type):
        self.sendMessage(type)
        return self.messageQueue();

    def sendMessage(self, type):
        # Get the message from the dictionary
        message = self.messages[type]

        # Append addresses
        message['dest_addr_long'] = self.long_address
        message['dest_addr']      = self.short_address
        message['device_name']    = self.name 
        message['device_type']    = self.type 

        # Add to outgoing messages
        self.logger.debug('Sent message: %s', type)
        self.outgoing_messages.append(message)

    def receiveMessage(self, message):
        # Add incoming message to queue
        self.incoming_messages.append(message)

        # Call to process messages
        # TODO: I have not worked out yet if I want to do something more clever
        # with the 'incoming_messages' list. For now it is a little superfulous.
        self.processMessage(self.incoming_messages.pop())

    def messageQueue(self):
        # Take a copy of the outgoing messsages
        messages = list(self.outgoing_messages)

        # Empty the outgoing messages list
        self.outgoing_messages[:] = []

        # Return the copied message list
        return messages
       
    def processMessage(self, message):
        if (message['id'] == 'rx_explicit'):
            # We are only interested in Zigbee Explicit packets.
            # Ignore Route Record Indicator packets etc.
        
            # Pilfer any relevant data from the message...
            self.short_address = message['source_addr']

            profileId = message['profile']
            clusterId = message['cluster']

            if (profileId == self.ZDP_PROFILE_ID):
                # Zigbee Device Profile ID

                if (clusterId == b'\x13'):
                    # Device Announce Message.
                    # Due to timing problems with the switch itself, we don't
                    # respond to this message, we save the response for later after the
                    # Match Descriptor request comes in. You'll see it down below.
                    self.logger.debug('Device Announce Message')

                elif (clusterId == b'\x80\x00'):
                    # Possibly Network (16-bit) Address Response.
                    # Not sure what this is? Only seen on the Hive ActivePlug?
                    # See: http://www.desert-home.com/2015/06/hacking-into-iris-door-sensor-part-4.html
                    self.logger.debug('Network (16-bit) Address Response')

                elif (clusterId == b'\x80\x05'):
                    # Active Endpoint Response.
                    # This message tells us what the device can do, but it isn't
                    # constructed correctly to match what the switch can do according
                    # to the spec. This is another message that gets it's response
                    # after we receive the Match Descriptor below.
                    self.logger.debug('Active Endpoint Response')

                elif (clusterId == b'\x802'):
                    # Route Record Broadcast Response.
                    self.logger.debug('Route Record Broadcast Response. MAC Address: %e', message['source_addr_long'])

                elif (clusterId == b'\x00\x06'): 
                    # Match Descriptor Request.
                    # This is the point where we finally respond to the switch.
                    # Several messages are sent to cause the switch to join with
                    # the controller at a network level and to cause it to regard
                    # this controller as valid.

                    # First send the Active Endpoint Request
                    self.logger.debug('Sent Active Endpoint Request')
                    self.sendMessage('endpoint_request')

                    # Now send the Match Descriptor Response
                    self.logger.debug('Sent Match Descriptor')
                    self.sendMessage('match_descriptor')

                    # Now there are two messages directed at the hardware code (rather than the network code).
                    # The switch has to receive both of these to stay joined.
                    self.sendMessage('hardware_join_1')
                    self.sendMessage('hardware_join_2')
                    self.logger.debug('Sent Hardware Join Messages')
                   
                    # We are fully associated!
                    logging.debug('Device Associated')
                    self.associated = 1;

                else:
                    self.logger.error('Unrecognised Cluster ID: %e', clusterId)
 
            elif (profileId == self.ALERTME_PROFILE_ID):
                # AlertMe Profile ID

                # Python 2 / 3 hack
                if( hasattr(bytes(), 'encode') ):
                    clusterCmd = message['rf_data'][2]
                else:
                    clusterCmd = bytes([message['rf_data'][2]])

                if (clusterId == b'\x00\xf6'):
                    if (clusterCmd == b'\xfe'):
                        verInfo = self.parseVersionInfo(message['rf_data'])
                        self.type    = verInfo['Type'];
                        self.date    = verInfo['Date'];
                        self.manu    = verInfo['Manu'];
                        self.version = verInfo['Version'];
                        self.associated = 1;
                        self.logger.debug('Version Information: %s %s', self.manu, self.type)

                    elif (clusterCmd == b'\xfd'):
                        self.rssi = self.parseRangeInfo(message['rf_data'])
                        self.logger.debug('Range Test RSSI Value: %s', self.rssi)

                    else:
                        self.logger.error('Unrecognised Cluster Command: %e', clusterCmd)

                elif (clusterId == b'\x00\xf2'):
                    self.tamper = self.parseTamper(message['rf_data'])
                    self.logger.debug('Tamper Switch Changed State: %s', self.tamper)

                else:
                    # Unknown message, pass onto specific message to process
                    self.receiveSpecificMessage(message)

            else:
                self.logger.error('Unrecognised Profile ID: %e', clusterId)

            # If we dont know what device type this is yet lets try and invoke it to tell us
            if(self.type is None):
                self.sendMessage('version_info')

    def receiveSpecificMessage(self, message):
        # Message to be handelled by specific device class (e.g. SmartPlug, Sensor etc.)
        self.logger.info('Specific message received by default device')

    def __str__(self):
        return "%s is a %s" % (self.name, self.type)


    @staticmethod
    def parseVersionInfo(rf_data):
        # The version string is variable length. We therefore have to calculate the 
        # length of the string which we then use in the unpack
        l = len(rf_data) - 22
        values = dict(zip(
            ('clusterCmd', 'Version', 'String'),
            unpack('< 2x s H 17x %ds' % l, rf_data)
        ))

        # Break down the version string into its component parts
        ret = {} 
        ret['Version'] = values['Version']
        ret['String']  = str(values['String'].decode()).replace('\t', '\n').replace('\r', '\n').replace('\x0e', '\n')
        ret['Manu']    = ret['String'].split('\n')[0]
        ret['Type']    = ret['String'].split('\n')[1]
        ret['Date']    = ret['String'].split('\n')[2]
        return ret

    @staticmethod
    def parseRangeInfo(rf_data):
        # Parse for RSSI Range Test value
        values = dict(zip(
            ('clusterCmd', 'RSSI'),
            unpack('< 2x s B 1x', rf_data)
        ))
        ret = values['RSSI']
        return ret

    @staticmethod
    def parseTamper(rf_data):
        # Parse Tamper Switch State Change
        if ord(rf_data[3]) == 0x02:
            return 1
        else:
            return 0
