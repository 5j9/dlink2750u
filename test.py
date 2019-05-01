from unittest import main, TestCase
from unittest.mock import patch, call

from dlink2750u import DLink2750U
from test_config import auth, ip_address


modem = DLink2750U(ip_address, auth)


class DLink2750UTest(TestCase):

    def test_name(self):
        modem_ = DLink2750U('192.168.1.1', auth)  # make that _name is None
        self.assertIsNone(modem_._name)
        self.assertTrue(modem_.name.startswith('DSL-'))
        self.assertEqual(modem_.name, modem_._name)

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

    def test_reboot(self):
        with patch.object(modem, 'get') as get_mock:
            modem.reboot()
        self.assertEqual(get_mock.mock_calls, [call('rebootinfo.cgi?')])

    def test_wireless_stations(self):
        stations = modem.wireless_stations()
        self.assertIs(type(stations), list)
        for station in stations:
            self.assertIs(type(station), dict)
            for k, v in station.items():
                self.assertIs(type(k), str)
                self.assertIs(type(v), str)

    def test_ping(self):
        with patch.object(modem, 'get', side_effect=[
            "var sessionKey='12345678';",
            "var sessionKey='12345678';<textarea>pingresult</textarea>"
        ]) as get_mock:
            self.assertEqual(modem.ping('1.1.1.1'), 'pingresult')
        self.assertEqual(get_mock.mock_calls, [
            call('pingtrace.html'), call(
                "pingtrace.cmd"
                "?action=ping"
                "&address=1.1.1.1"
                "&sessionKey=12345678")])


if __name__ == '__main__':
    main()
