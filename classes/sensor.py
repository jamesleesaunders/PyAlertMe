import pprint
import logging
from struct import unpack
from classes import Device

class Sensor(Device):
    specific_messages = {
        'sensor_speacial': {
            'description'   : 'Sensor Special',
            'src_endpoint'  : b'\x00',
            'dest_endpoint' : b'\x02',
            'cluster'       : b'\x00\xee',
            'profile'       : Device.ALERTME_PROFILE_ID,
            'data'          : b'\x11\x00\x02\x00\x01'
        }
    }

    def __init__(self, long_address, name='Sensor'):
        Device.__init__(self, long_address, name)
        self.type = 'Sensor'

        # Tack the specific messages onto the standard messages
        self.messages.update(self.specific_messages)


    def receiveSpecificMessage(self, message):
        profileId = message['profile']
        clusterId = message['cluster']

        if (profileId == self.ALERTME_PROFILE_ID):
            if (clusterId == b'\x05\x00'):
                self.logger.debug('Security Event')
                # Security Cluster
                # When the switch first connects, it come up in a state that needs
                # initialization, this command seems to take care of that.
                # So, look at the value of the data and send the command.

                if (message['rf_data'][3:7] == b'\x15\x00\x39\x10'):
                    print "Sending Initialization"
                    #self.zb.send('tx_explicit',
                    #    dest_addr_long = message['source_addr_long'],
                    #    dest_addr      = message['source_addr'],
                    #    src_endpoint   = message['dest_endpoint'],
                    #    dest_endpoint  = message['source_endpoint'],
                    #    cluster        = b'\x05\x00',
                    #    profile        = b'\xc2\x16',
                    #    data           = b'\x11\x80\x00\x00\x05'
                    #)

                # The switch state is in byte [3] and is a bitfield
                # bit 0 is the magnetic reed switch state
                # bit 3 is the tamper switch state
                switchState = ord(message['rf_data'][3])
                if (switchState & 0x01):
                    self.logger.debug('Reed Switch Open')
                else:
                    self.logger.debug('Reed Switch Closed')

                if (switchState & 0x04):
                    self.logger.debug('Tamper Switch Closed')
                else:
                    self.logger.debug('Tamper Switch Open')

            elif (clusterId == b'\x00\xf0'):
                clusterCmd = message['rf_data'][2]
                if (clusterCmd == b'\xfb'):
                    vals = self.parseStatusUpdate(message['rf_data'])
                    self.logger.debug('Status Update: %s', vals)
                else:
                    self.logger.error('Unrecognised Cluster Cmd: %r', clusterCmd)

            elif (clusterId == b'\x00\xf3'):
                vals = self.parseButtonPress(message['rf_data'])
                self.logger.debug('Button Press: %s', vals)

            else:
                self.logger.error('Unrecognised Cluster ID: %r', clusterId)
                self.pp.pprint(message['rf_data'])

        else:
            self.logger.error('Unrecognised Profile ID: %r', profileId)
            self.pp.pprint(message['rf_data'])






    @staticmethod
    def parseButtonPress(rf_data):
        ret = {}
        if rf_data[2] == b'\x00':
            ret['State'] = 0
        elif rf_data[2] == b'\x01':
            ret['State'] = 1
        else:
            ret['State'] = None
        ret['Counter'] = unpack('<H', rf_data[5:7])[0]
        return ret

    @staticmethod
    def parseStatusUpdate(rf_data):
        ret = {}
        status = rf_data[3]
        if (status == b'\x1c'):
            # Power Switch
            ret['Type']    = 'Power Switch'
            # Never found anything useful in this

        elif (status == b'\x1d'):
            # Key Fob
            ret['Type']    = 'Key Fob'
            ret['Temp_F']  = float(unpack("<h", rf_data[8:10])[0]) / 100.0 * 1.8 + 32
            ret['Counter'] = unpack('<I', rf_data[4:8])[0]

        elif (status == b'\x1e') or (status == b'\x1f'):
            # Door Sensor
            ret['Type']    = 'Door Sensor'
            if (ord(rf_data[-1]) & 0x01 == 1):
                ret['ReedSwitch']   = 'open'
            else:
                ret['ReedSwitch']   = 'closed'

            if (ord(rf_data[-1]) & 0x02 == 0):
                ret['TamperSwith'] = 'open'
            else:
                ret['TamperSwith'] = 'closed'

            if (status == b'\x1f'):
                ret['Temp_F'] = float(unpack("<h", rf_data[8:10])[0]) / 100.0 * 1.8 + 32
            else:
                ret['Temp_F'] = None

        else:
            self.logger.error('Unrecognised Device Status')

        return ret
