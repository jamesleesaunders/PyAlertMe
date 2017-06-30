import logging
from xbee import ZigBee
from pyalertme.zigbee import *
from pyalertme.device import Device
import struct
import time
import binascii
import threading

class ZigBeeDevice(Device):

    def __init__(self, serial, callback=None):
        """
        Base Constructor

        :param serial: Serial Object
        :param callback: Optional
        """
        Device.__init__(self, callback)

        # Start up Serial and ZigBee
        self._serial = serial
        self._xbee = ZigBee(ser=self._serial, callback=self.receive_message, error_callback=self.xbee_error, escaped=True)

        # Fire off messages to discover own addresses
        self.read_addresses()
        self._addr_long_list = [b'', b'']
        self.addr_long = None
        self.addr_short = None

        # Type Info
        self.type = 'ZigBeeDevice'
        self.version = 12345
        self.manu = 'PyAlertMe'
        self.manu_date = '2017-01-01'

        # Scheduler Thread
        self._started = True
        self._schedule_thread = threading.Thread(target=self._schedule_loop)
        self._schedule_interval = 2
        self._schedule_thread.start()

        # ZDO Sequence
        self.zdo_sequence = 1

    def __str__(self):
        return self.type

    def halt(self):
        """
        Halt Device
        Close XBee and Serial

        :return:
        """
        self._started = False         # This should kill the updates thread
        self._schedule_thread.join()  # Wait for updates thread to finish
        self._xbee.halt()
        self._serial.close()

    def _schedule_loop(self):
        """
        Continual Updates Thread calls the _updates() function every at intervals set in self._schedule_interval.

        """
        while self._started:
            if self.associated:
                self._schedule_event()

                # The following for loop is being used in place of a simple
                # time.sleep(self._schedule_interval)
                # This is done so we can interrupt the thread quicker.
                for i in range(self._schedule_interval * 10):
                    if self._started:
                        time.sleep(0.1)

    def _schedule_event(self):
        """
        The _schedule_event() function is called by the _schedule_loop() thread function called at regular intervals.

        """
        self._logger.debug('Continual Update')

    def xbee_error(self, error):
        """
        On XBee error this function is called

        :param error:
        :return:
        """
        self._logger.critical('XBee Error: %s', error)

    def read_addresses(self):
        """
        Work out own address

        """
        self._logger.debug('Requesting own addresses')
        self._xbee.send('at', command='MY')
        time.sleep(0.05)
        self._xbee.send('at', command='SH')
        time.sleep(0.05)
        self._xbee.send('at', command='SL')
        time.sleep(0.05)

    def send_message(self, message, dest_addr_long, dest_addr_short):
        """
        Send message to XBee

        :param message: Dict message
        :param dest_addr_long: 48-bits Long Address
        :param dest_addr_short: 16-bit Short Address
        :return:
        """
        # Tack on destination addresses
        message['dest_addr_long']  = dest_addr_long
        message['dest_addr'] = dest_addr_short

        self._logger.debug('Sending Message: %s', message)
        self._xbee.send('tx_explicit', **message)

    def receive_message(self, message):
        """
        Receive message from XBee
        Calls process message

        :param message: Dict of message
        :return:
        """
        self._logger.debug('Received Message: %s', message)
        self.process_message(message)

    def process_message(self, message):
        """
        Process incoming message

        :param message: Dict of message
        :return:
        """
        # AT Packets
        if message['id'] == 'at_response':
            if message['command'] == 'MY':
                self.addr_short = message['parameter']
            if message['command'] == 'SH':
                self._addr_long_list[0] = message['parameter']
            if message['command'] == 'SL':
                self._addr_long_list[1] = message['parameter']
            # If we have worked out both the High and Low addresses then calculate the full addr_long
            if self._addr_long_list[0] and self._addr_long_list[1]:
                self.addr_long = b''.join(self._addr_long_list)

        # ZigBee Explicit Packets
        if message['id'] == 'rx_explicit':
            profile_id = message['profile']
            cluster_id = message['cluster']

            if profile_id == PROFILE_ID_ZDP:
                # ZigBee Device Profile ID
                self._logger.debug('Received ZigBee Device Profile Packet')

            elif profile_id == PROFILE_ID_ALERTME:
                # AlertMe Profile ID
                self._logger.debug('Received AlertMe Specific Profile Packet')

            elif profile_id == PROFILE_ID_HA:
                # HA Profile ID
                self._logger.debug('Received HA Profile Packet')

            else:
                self._logger.error('Unrecognised Profile ID: %r', profile_id)


