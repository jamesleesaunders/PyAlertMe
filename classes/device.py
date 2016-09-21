import pprint
import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
from struct import unpack

class Device(object):

    # ZigBee Profile IDs
    ZDP_PROFILE_ID     = '\x00\x00' # Zigbee Device Profile
    ALERTME_PROFILE_ID = '\xc2\x16' # AlertMe Private Profile

    # ZigBee Addressing
    BROADCAST_LONG  = '\x00\x00\x00\x00\x00\x00\xff\xff'
    BROADCAST_SHORT = '\xff\xfe'

    def __init__(self, zb, address, name="Generic Device"):
        self.type          = None
        self.zb            = zb
        self.name          = name
        self.long_address  = address
        self.short_address = None

    def getType(self):
        return self.type
  
    def getName(self):
        return self.name

    def getAddress(self):
        return self.long_address

    def __str__(self):
        return "%s is a %s" % (self.name, self.address)

    def sendMessage(self, srcEndpoint, destEndpoint, clusterId, profileId, data):
        self.zb.send('tx_explicit',
            dest_addr_long = self.long_address,
            dest_addr = self.short_address,
            src_endpoint = srcEndpoint,
            dest_endpoint = destEndpoint,
            cluster = clusterId,
            profile = profileId,
            data = data
        )

    def receiveMessage(self, message):
        pp = pprint.PrettyPrinter(indent=4)

        if (message['id'] == 'rx_explicit'):
            # We are only interested in Zigbee Explicit packets.
            # Ignore Route Record Indicator packets etc.
        
            # Pilfer any relevant data from the message...
            self.short_address = message['source_addr']

            profileId = message['profile']
            clusterId = message['cluster']
 
            if (profileId == self.ZDP_PROFILE_ID):
                # Zigbee Device Profile ID

                if (clusterId == '\x13'):
                    # Device Announce Message.
                    # Due to timing problems with the switch itself, we don't
                    # respond to this message, we save the response for later after the
                    # Match Descriptor request comes in. You'll see it down below.
                    logging.debug('Device Announce Message')

                elif (clusterId == '\x80\x00'):
                    # Possibly Network (16-bit) Address Response.
                    # Not sure what this is? Only seen on the Hive ActivePlug?
                    # See: http://www.desert-home.com/2015/06/hacking-into-iris-door-sensor-part-4.html
                    logging.debug('Network (16-bit) Address Response')

                elif (clusterId == '\x80\x05'):
                    # Active Endpoint Response.
                    # This message tells us what the device can do, but it isn't
                    # constructed correctly to match what the switch can do according
                    # to the spec. This is another message that gets it's response
                    # after we receive the Match Descriptor below.
                    logging.debug('Active Endpoint Response')

                elif (clusterId == '\x802'):
                    # Route Record Broadcast Response.
                    logging.debug('Route Record Broadcast Response')
                    logging.debug('Plug MAC Address: %s', message['source_addr_long'])

                elif (clusterId == '\x00\x06'): 
                    # Match Descriptor Request.
                    # This is the point where we finally respond to the switch.
                    # Several messages are sent to cause the switch to join with
                    # the controller at a network level and to cause it to regard
                    # this controller as valid.

                    # First send the Active Endpoint Request
                    data = '\x00\x00'
                    self.sendMessage('\x00', '\x00', '\x00\x05', self.ZDP_PROFILE_ID, data)
                    logging.debug('Sent Active Endpoint Request')

                    # Now send the Match Descriptor Response
                    data = '\x00\x00\x00\x00\x01\x02'
                    self.sendMessage('\x00', '\x00', '\x80\x06', self.ZDP_PROFILE_ID, data)
                    logging.debug('Sent Match Descriptor')

                    # Now there are two messages directed at the hardware code (rather than the network code).
                    # The switch has to receive both of these to stay joined.
                    data = '\x11\x01\xfc'
                    self.sendMessage('\x00', '\x02', '\x00\xf6', self.ALERTME_PROFILE_ID, data)

                    data = '\x19\x01\xfa\x00\x01'
                    self.sendMessage('\x00', '\x02', '\x00\xf0', self.ALERTME_PROFILE_ID, data)
                    logging.debug('Sent Hardware Join Messages')
                    
                    # We are fully associated!
                    logging.debug('Device Associated')
                    self.associated = 1;

                else:
                    logging.error('Unrecognised Cluster ID')
 
            elif (profileId == self.ALERTME_PROFILE_ID):
                # AlertMe Profile ID
                clusterCmd = message['rf_data'][2]

                if (clusterId == '\x00\xf6'):
                    if (clusterCmd == '\xfe'):
                        verInfo = self.parseVersionInfo(message['rf_data'])
                        self.type    = verInfo['Type'];
                        self.date    = verInfo['Date'];
                        self.manu    = verInfo['Manu'];
                        self.version = verInfo['Version'];
                        logging.debug('Version Information: %s %s %s %s', verInfo['Manu'], verInfo['Type'], verInfo['Version'], verInfo['Date'])

                    elif (clusterCmd == '\xfd'):
                        self.rssi = self.parseRangeInfo(message['rf_data'])
                        logging.debug('Range Test RSSI Value: %s', self.rssi)

                    else:
                        logging.error('Unrecognised Cluster Command')

                else:
                    # Unknown message, pass onto specific message to process
                    self.receiveSpecificMessage(message)

            else:
                logging.error('Unrecognised Profile ID')

            # If we dont know what device type this is yet lets try and invoke it to tell us
            if(self.type is None):
                clusterCmd = '\xfc'
                databytes = '\x00\x01'
                data = '\x11\x00' + clusterCmd + databytes
                self.sendMessage('\x00', '\x02', '\x00\xf6', self.ALERTME_PROFILE_ID, data)

    def receiveSpecificMessage(self, message):
        # Message to be handelled by specific device class (e.g smartswitch)
        logging.error('Specific message received by default device')






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
        ret['String']  = values['String'].replace('\t', '\n').replace('\r', '\n')
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
