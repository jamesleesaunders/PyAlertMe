import pprint
import logging
from struct import unpack
from classes import Device

class SmartPlug(Device):
    specific_messages = {
        'plug_off': {
            'description'   : 'Switch Plug Off',
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xee',
            'profile'       : Device.ALERTME_PROFILE_ID,
            'data'          : b'\x11\x00\x02\x00\x01'
        },
        'plug_on': {
            'description'   : 'Switch Plug On',
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xee',
            'profile'       : Device.ALERTME_PROFILE_ID,
            'data'          : b'\x11\x00\x02\x01\x01'
        },
        'switch_status': {
            'description'   : 'Switch Status',
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xee',
            'profile'       : Device.ALERTME_PROFILE_ID,
            'data'          : b'\x11\x00\x01\x01'
        },
        'normal_mode': {
            'description'   : 'Restore Normal Mode',
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xee',
            'profile'       : Device.ALERTME_PROFILE_ID,
            'data'          : b'\x11\x00\xfa\x00\x01'
        },
        'range_test': {
            'description'   : 'Range Test',
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xee',
            'profile'       : Device.ALERTME_PROFILE_ID,
            'data'          : b'\x11\x00\xfa\x01\x01'
        },
        'locked_mode': {
            'description'   : 'Locked Mode',
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xee',
            'profile'       : Device.ALERTME_PROFILE_ID,
            'data'          : b'\x11\x00\xfa\x02\x01'
        },
        'silent_mode': {
            'description'   : 'Silent Mode',
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xee',
            'profile'       : Device.ALERTME_PROFILE_ID,
            'data'          : b'\x11\x00\xfa\x03\x01'
        }
    }

    def __init__(self, long_address, name='SmartPlug'):
        Device.__init__(self, long_address, name)
        self.type = 'SmartPlug'
        
        # Tack the specific messages onto the standard messages
        self.messages.update(self.specific_messages)

    def getState(self):
        return self.state

    def getUptime(self):
        return self.uptime

    def receiveSpecificMessage(self, message):
        profileId = message['profile']
        clusterId = message['cluster']

        if (profileId == self.ALERTME_PROFILE_ID):
            clusterCmd = message['rf_data'][2]

            if (clusterId == b'\x00\xef'):
                if (clusterCmd == b'\x81'):
                    self.power = self.parsePowerInfo(message['rf_data'])
                    self.logger.debug('Current Instantaneous Power: %s', self.power)

                elif (clusterCmd == b'\x82'):
                    usageInfo = self.parseUsageInfo(message['rf_data'])
                    self.uptime           = usageInfo['UpTime'];
                    self.usagewattseconds = usageInfo['UsageWattSeconds'];
                    self.usagewatthours   = usageInfo['UsageWattHours'];
                    self.logger.debug('Uptime: %s Usage: %s', self.uptime, self.usagewatthours)

                else:
                    self.logger.error('Unrecognised Cluster Command: %r', clusterCmd)

            elif (clusterId == b'\x00\xee'):
                if (clusterCmd == b'\x80'):
                    self.state = self.parseSwitchStatus(message['rf_data'])
                    self.logger.debug('Switch Status: %s', self.state)

                else:
                    self.logger.error('Unrecognised Cluster Command: %r', clusterCmd)

            elif (clusterId == '\x00\xf0'):
                if (clusterCmd == '\xfb'):
                    self.logger.debug('Mystery Cluster Command')
                    # Needs more investigation...

                else:
                    self.logger.error('Unrecognised Cluster Command: %r', clusterCmd)

            else:
                self.logger.error('Unrecognised Cluster ID: %r', clusterId)
                self.pp.pprint(message['rf_data'])

        else:
            self.logger.error('Unrecognised Profile ID: %r', profileId)
            self.pp.pprint(message['rf_data'])


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
        values = unpack('< 2x b b b', rf_data)
        if (values[2] & 0x01):
            return 1
        else:
            return 0
