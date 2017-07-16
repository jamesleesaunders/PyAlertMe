from pyalertme.node import Node
from pyalertme.zb import ZB
import time
import threading

class ZBNode(Node, ZB):
    def __init__(self, serial, callback=None):
        """
        Base Constructor

        :param serial: Serial Object
        :param callback: Optional
        """
        Node.__init__(self, callback)
        ZB.__init__(self, serial)

        # Type Info
        self.type = 'ZBNode'
        self.version = 12345
        self.manu = 'PyAlertMe'
        self.manu_date = '2017-01-01'

        # Scheduler Thread
        self._started = True
        self._schedule_thread = threading.Thread(target=self._schedule_loop)
        self._schedule_interval = 2
        self._schedule_thread.start()

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
