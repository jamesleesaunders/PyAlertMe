import pprint
from struct import unpack
from classes import Device

class Button(Device):

    def __init__(self, zb, address, name='Button'):
        Device.__init__(self, zb, address, name)
        self.type          = 'Button Device'
        self.zb            = zb
        self.name          = name
        self.long_address  = address

        self.state         = None

    def getState(self):
        return self.state

    def getUptime(self):
        return self.uptime

    def receiveSpecificMessage(self, message):
        pp = pprint.PrettyPrinter(indent=4)

        profileId = message['profile']
        clusterId = message['cluster']

        if (profileId == self.ALERTME_PROFILE_ID):
            # AlertMe Profile ID
            clusterCmd = message['rf_data'][2]

            # SmartPlug Specific
            if (clusterId == '\x00\xef'):
                if (clusterCmd == '\x81'):
                    self.power = self.parsePowerInfo(message['rf_data'])
                    print "\tCurrent Instantaneous Power:", self.power

                elif (clusterCmd == '\x82'):
                    usageInfo = self.parseUsageInfo(message['rf_data'])
                    self.uptime           = usageInfo['UpTime'];
                    self.usagewattseconds = usageInfo['UsageWattSeconds'];
                    self.usagewatthours   = usageInfo['UsageWattHours'];
                    print "\tUsage Stats:"
                    print "\tUp Time (seconds):", self.uptime
                    print "\tUsage (watt-seconds):", self.usagewattseconds
                    print "\tUsage (watt-hours):", self.usagewatthours

                else:
                    print "Minor Error: Unrecognised Cluster Command"

            elif (clusterId == '\x00\xee'):
                if (clusterCmd == '\x80'):
                    self.state = self.parseSwitchStatus(message['rf_data'])
                    print "Switch Status"
                    print "\tSwitch is:", self.state

                else:
                    print "Minor Error: Unrecognised Cluster Command"

            else:
                print "Minor Error: Unrecognised Cluster ID"

        else:
            print "Minor Error: Unrecognised Profile ID"








    @staticmethod
    def parsePowerInfo(rf_data):
        # Parse for Current Instantaneous Power value
        values = dict(zip(
            ('clusterCmd', 'Power'),
            unpack('< 2x s H', rf_data)
        ))
        ret = values['Power']

        return ret

    @staticmethod
    def parseUsageInfo(rf_data):
        # Parse Usage Stats
        ret = {} 
        values = dict(zip(
            ('clusterCmd', 'Usage', 'UpTime'),
            unpack('< 2x s I I 1x', rf_data)
        ))
        ret['UpTime']           = values['UpTime']
        ret['UsageWattSeconds'] = values['Usage']
        ret['UsageWattHours']   = values['Usage'] * 0.000277778

        return ret

    @staticmethod
    def parseSwitchStatus(rf_data):
        # Parse Switch Status
        if (ord(rf_data[3]) & 0x01):
            return 1
        else:
            return 0


