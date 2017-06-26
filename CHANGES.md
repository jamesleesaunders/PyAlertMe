v0.0.1 - 21 Sep 2016
* Initial proof of concept.

v0.0.2 - 16 Oct 2016
* Adding support for AlertMe Sensor and Button devices.

v0.1.0 - 07 Jan 2017
* Don't create an object for every discovered device.

v0.1.1 - 14 Jan 2017
* Tidy up logging.

v0.1.2 - 28 Jan 2017
* Update README.md.
* Tidy up function names.

v0.1.3 - 08 Mar 2017
* Rename project from pi-hive to pyalertme.
* Adding support for Mathmos lamp.
* Added SQLite support.
* Fixed logging for discovery thread.
* Restructured folders into package structure, adding setup.py.

v0.1.4 - 18 Mar 2017
* Added callback function when attributes are changed.
* Fix setup.py and tests.
* Renaming folder from examples to scripts
* Added start() function.
* Improved node_id to address and vice versa resolution.

v0.1.5 - 28 Mar 2017
* Moved to use of generate_xxx functions to generate packets.
* Added Python Docs comment blocks to all class functions.
* Added new attribute history function.
* Fixed Version request.

v0.2.0 - 12 Apr 2017
* Added AT commands to work out own addresses.
* Mode escaped=True.
* Adding Generate Match Descriptor Request.
* New setup-xbee.py script to auto configure module.

v0.2.1 - 19 Apr 2017
* Fix Issue #19 Removed SQLite DB code - it was over complicating the class and would be superfluous if the developer wanted to use a different DB like MySQL.
* Fix Issue #26 Combining Type Req / Hardware Join 1 & Range Test / Hardware Join 2. 
* Partially addressed #5. Device.py now has facility to send updates at regular intervals using Threads.
* Improvements to SmartPlug class.
* Improvements to Current Instantaneous Power and RSSI messages.
* Simpler terminology 'Power Demand' and 'Power Consumption'.
* Making more use of callback.
* Further PEP formatting.

v0.2.2 - 08 May 2017
* New messages.py - Moving all parse* and generate* functions to this file.
* Making use of lambda functions to generate messages.
* New unit tests.
* Adding Codecov and TravisCI support.
* New regular updates thread for keep alives etc.
* Improving thread quit speed.
* Moved tests folder in package... again.

v0.3.0 - 26 Jun 2017
* Hub device list is now a list of device objects rather than a simple dict.
* Making more use of device objects - not only ate they used to create new devices but also in the hub.
* Zigbee message improvements.
