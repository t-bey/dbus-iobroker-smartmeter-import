# dbus-iobroker-smartmeter-import
This service request smartmeter data from ioBroker and sends it to the Victron Venus OS D-Bus. This replaces a physical Victron energy meter.

## How-to install and configure
Copy the repo source to `/data/dbus-iobroker-smartmeter-import`.
Edit the config.ini file matching your environment.
Finally, run ones the install.sh script.

## Useful documentation
- Venus OS: Root Access https://www.victronenergy.com/live/ccgx:root_access   
- services and their paths on Venus OS D-Bus https://github.com/victronenergy/venus/wiki/dbus#grid-and-genset-meter   
- D-Bus API https://github.com/victronenergy/venus/wiki/dbus-api
- ioBroker.simple-api Adapter https://github.com/ioBroker/ioBroker.simple-api
