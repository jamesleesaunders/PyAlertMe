import logging
from pyalertme.zb import *
from pyalertme.zbdevice import ZBDevice
import struct
import time
import binascii
import threading

class ZBSensor(ZBDevice):

    def __init__(self, serial, callback=None):
        """
        Sensor Constructor

        :param serial: Serial Object
        :param callback: Optional
        """
        ZBDevice.__init__(self, serial, callback)

        # Type Info
        self.type = 'ZBSensor'
        self.version = 12345
        self.manu = 'PyAlertMe'
        self.manu_date = '2017-01-01'

        # Attributes
        self.tamper_state = 0
        self.triggered = 0