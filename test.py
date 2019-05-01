from unittest import main, TestCase

from __init__ import DLink2750U
from test_config import auth, ip_address


modem = DLink2750U(ip_address, auth)


class DLink2750UTest(TestCase):

    def test_name(self):
        self.assertTrue(modem.name.startswith('DSL-'))

    def test_repr(self):
        self.assertEqual(repr(modem), f'<{modem.name}@{modem.ip_address}>')

    def test_device_info_summary(self):
        device_info = modem.device_info_summary()
        self.assertIn('MAC Address', device_info)
        self.assertIn('BoardID', device_info)

    def test_wan_info(self):
        wan_info = modem.wan_info()
        self.assertIs(type(wan_info), dict)
        for interface, interface_info in wan_info.items():
            self.assertIs(type(interface), str)
            self.assertIs(type(interface_info), dict)
            for k, v in interface_info.items():
                self.assertIs(type(k), str)
                self.assertIs(type(v), str)

    def test_wireless_stations(self):
        stations = modem.wireless_stations()
        self.assertIs(type(stations), list)
        for station in stations:
            self.assertIs(type(station), dict)
            for k, v in station.items():
                self.assertIs(type(k), str)
                self.assertIs(type(v), str)


if __name__ == '__main__':
    main()
