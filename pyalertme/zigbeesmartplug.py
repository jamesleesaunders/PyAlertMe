import logging
from pyalertme.zigbee import *
from pyalertme.zigbeenode import ZigBeeNode
import struct
import time
import binascii
import threading

class ZigBeeSmartPlug(ZigBeeNode):

    def __init__(self, callback=None):
        """
        SmartPlug Constructor

        """
        ZigBeeNode.__init__(self, callback)

        # Type Info
        self.type = 'SmartPlug'
        self.version = 12345
        self.manu = 'PyAlertMe'
        self.manu_date = '2017-01-01'


        # Set continual updates to every 5 seconds
        self._schedule_interval = 5

        # Attributes - Relay State and Power Values
        self.relay_state = False
        self.power_demand = 0
        self.power_consumption = 0

    def _schedule_event(self):
        """
        The _schedule_event function is called by the _schedule_loop() thread function called at regular intervals.

        """
        self.send_message(self.generate_power_demand_update(), self.hub_addr_long, self.hub_addr_short)

    def process_message(self, message):
        """
        Process incoming message

        :param message: Dict of message
        :return:
        """
        super(ZigBeeSmartPlug, self).process_message(message)

        # ZigBee Explicit Packets
        if message['id'] == 'rx_explicit':
            profile_id = message['profile']
            cluster_id = message['cluster']
            source_addr_long = message['source_addr_long']
            source_addr_short = message['source_addr']

            if profile_id == PROFILE_ID_ALERTME:
                # AlertMe Profile ID
                cluster_cmd = message['rf_data'][2:3]

                if cluster_id == CLUSTER_ID_AM_SWITCH:
                    if cluster_cmd == CLUSTER_CMD_AM_STATE_REQ:
                        # State Request
                        # b'\x11\x00\x01\x01'
                        self._logger.debug('Switch Relay State is: %s', self.relay_state)
                        self.send_message(self.generate_relay_state_update(), source_addr_long, source_addr_short)

                    elif cluster_cmd == CLUSTER_CMD_AM_STATE_CHANGE:
                        # Change State
                        # b'\x11\x00\x02\x01\x01' On
                        # b'\x11\x00\x02\x00\x01' Off
                        params = parse_switch_state_request(message['rf_data'])
                        self.relay_state = params['relay_state']
                        self.send_message(self.generate_relay_state_update(), source_addr_long, source_addr_short)
                        self._callback('Attribute', self.id, 'relay_state', 1)

                    else:
                        self._logger.error('Unrecognised Cluster Command: %r', cluster_cmd)

                # else:
                    # self._logger.error('Unrecognised Cluster ID: %r', cluster_id)

            # else:
                # self._logger.error('Unrecognised Profile ID: %r', profile_id)

    def generate_relay_state_update(self):
        """
        Generate State Message

        :return: Message of switch state
        """
        return get_message('switch_state_update', {'relay_state': self.relay_state})

    def generate_power_demand_update(self):
        """
        Generate Power Demand Update

        :return: Message
        """
        return get_message('power_demand_update', {'power_demand': self.power_demand})

