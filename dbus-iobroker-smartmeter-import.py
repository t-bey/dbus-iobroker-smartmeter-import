#!/usr/bin/env python

import platform
import logging
import sys
import os
from gi.repository import GLib
import time
import requests
import configparser
from dbus.mainloop.glib import DBusGMainLoop

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService

class DbusIoBrokerSmartMeterImportService:
    def __init__(self, serviceName, deviceInstance, paths, productName='SmartMeter reader', connection='SmartMeter data from ioBroker rest api'):
        self._dbusService = VeDbusService("%s.http_%02d" % (serviceName, deviceInstance))

        config = self._getConfig()
        self._ioBrokerKeyPowerTotal = config['DEFAULT']['ioBrokerPathPowerTotal']
        self._ioBrokerKeyPowerL1 = config['DEFAULT']['ioBrokerPathPowerL1']
        self._ioBrokerKeyPowerL2 = config['DEFAULT']['ioBrokerPathPowerL2']
        self._ioBrokerKeyPowerL3 = config['DEFAULT']['ioBrokerPathPowerL3']
        self._ioBrokerKeyGridSold = config['DEFAULT']['ioBrokerPathGridSold']
        self._ioBrokerKeyGridBought = config['DEFAULT']['ioBrokerPathGridBought']
        self._ioBrokerHost = config['DEFAULT']['ioBrokerHost']

        logging.debug("%s /DeviceInstance = %d" % (serviceName, deviceInstance))

        self._dbusService.add_path('/Mgmt/ProcessName', __file__)
        self._dbusService.add_path('/Mgmt/ProcessVersion', '0.1.4')
        self._dbusService.add_path('/Mgmt/Connection', connection)

        self._dbusService.add_path('/DeviceInstance', deviceInstance)
        # magic numbers found at https://www.sascha-curth.de/projekte/005_Color_Control_GX.html#experiment
        self._dbusService.add_path('/ProductId', 45069)
        self._dbusService.add_path('/DeviceType', 345)
        self._dbusService.add_path('/ProductName', productName)
        self._dbusService.add_path('/CustomName', productName)
        self._dbusService.add_path('/Latency', None)
        self._dbusService.add_path('/FirmwareVersion', 0.1)
        self._dbusService.add_path('/HardwareVersion', 0)
        self._dbusService.add_path('/Connected', 1)
        self._dbusService.add_path('/Role', 'grid')

        for path, settings in paths.items():
            self._dbusService.add_path(
                path, settings['initial'], gettextcallback=settings['textformat'], writeable=True)

        GLib.timeout_add(1000, self._update)

    def _getConfig(self):
        config = configparser.ConfigParser()
        config.read("%s/config.ini" % (os.path.dirname(os.path.realpath(__file__))))
        return config

    def _getIoBrokerSmartMeterData(self):
        url = "%s/getBulk/%s,%s,%s,%s,%s,%s" % (
            self._ioBrokerHost, self._ioBrokerKeyPowerTotal, self._ioBrokerKeyPowerL1, self._ioBrokerKeyPowerL2, self._ioBrokerKeyPowerL3, self._ioBrokerKeyGridBought, self._ioBrokerKeyGridSold
        )

        meterResponse = requests.request('GET', url, headers={})
        if not meterResponse:
            raise ConnectionError("no response from ioBroker - %s" % (url))

        responseData = meterResponse.json()

        if not responseData:
            raise ValueError('invalid JSON response')

        meterData = {}
        for data in responseData:
            meterData[data['id']] = data['val']

        return meterData

    def _update(self):
        try:
            meterData = self._getIoBrokerSmartMeterData()
            logging.debug(meterData)

            self._dbusService['/Ac/Power'] = meterData[self._ioBrokerKeyPowerTotal]
            self._dbusService['/Ac/L1/Power'] = meterData[self._ioBrokerKeyPowerL1]
            self._dbusService['/Ac/L2/Power'] = meterData[self._ioBrokerKeyPowerL2]
            self._dbusService['/Ac/L3/Power'] = meterData[self._ioBrokerKeyPowerL3]
        except Exception as e:
            logging.critical('Error at %s', '_update', exc_info=e)

        return True


def main():
    try:
        DBusGMainLoop(set_as_default=True)

        _kwh = lambda p, v : str(round(v, 2)) + ' KWh'
        _w = lambda p, v : str(round(v, 1)) + ' W'

        DbusIoBrokerSmartMeterImportService(
            serviceName='com.victronenergy.grid',
            deviceInstance=40,
            paths={
                '/Ac/Energy/Forward': {'initial': 0, 'textformat': _kwh},
                '/Ac/Energy/Reverse': {'initial': 0, 'textformat': _kwh},
                '/Ac/Power': {'initial': 0, 'textformat': _w},
                '/Ac/L1/Power': {'initial': 0, 'textformat': _w},
                '/Ac/L2/Power': {'initial': 0, 'textformat': _w},
                '/Ac/L3/Power': {'initial': 0, 'textformat': _w}
            })

        mainLoop = GLib.MainLoop()
        mainLoop.run()
    except (Exception, ValueError, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        logging.critical('Error at %s', 'main', exc_info=e)

if __name__ == '__main__':
    main()
