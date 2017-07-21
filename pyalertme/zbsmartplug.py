import logging
from pyalertme.zbdevice import *
from random import randint

class ZBSmartPlug(ZBDevice):
    def __init__(self, serial, callback=None):
        """
        SmartPlug Constructor

        :param serial: Serial Object
        :param callback: Optional
        """
        ZBDevice.__init__(self, serial, callback)

        # Type Info
        self.type = 'ZBSmartPlug'
        self.version = 12345
        self.manu = 'PyAlertMe'
        self.manu_date = '2017-01-01'

        # Attributes
        self.switch_state = 0
        self.power_demand = 0
        self.power_consumption = 0

        # Set continual updates to every 5 seconds
        self._schedule_interval = 5

    def _schedule_event(self):
        """
        The _schedule_event function is called by the _schedule_loop() thread function called at regular intervals.

        """
        self.rssi = randint(0, 100)
        message = self.generate_message('range_update', {'rssi': self.rssi})
        self.send_message(message, self.hub_obj.addr_long, self.hub_obj.addr_short)

    def set_switch_state(self, switch_state):
        """
        This simulates the physical button being pressed
        :param switch_state:
        :return:
        """
        self.set_attribute('switch_state', switch_state)
        if self.associated:
            message = self.generate_message('switch_state_request', {'switch_state': self.switch_state})
            self.send_message(message, self.hub_obj.addr_long, self.hub_obj.addr_short)

        # Temporary code while testing power code...
        # Randomly set the power usage value.
        self.set_power_demand(randint(0, 100))

    def set_power_demand(self, power_demand):
        """
        Set Power Demand
        :param power_demand:
        :return:
        """
        self.set_attribute('power_demand', power_demand)
        if self.associated:
            message = self.generate_message('power_demand_update', {'power_demand': self.power_demand})
            self.send_message(message, self.hub_obj.addr_long, self.hub_obj.addr_short)
