from functools import partial
from re import search, compile as re_compile, IGNORECASE
from typing import List, Dict, Optional

from requests import Session
from bs4 import BeautifulSoup


_SESSION_KEY = re_compile(r"sessionKey='?(\d*)", IGNORECASE).search
_VARS = re_compile(r"var\s+(\w+)\s*=\s*'(.*?)';", IGNORECASE).findall


Soup = partial(BeautifulSoup, features='lxml')


class DLink2750U:

    _name = _mac_address = None

    def __init__(self, ip_address: str, auth=('admin', 'admin')):
        self.ip_address = ip_address
        self.url = f'http://{ip_address}/'
        self.auth = auth
        self.session = Session()

    def get(self, path: str) -> str:
        return self.session.request(
            'GET', self.url + path, auth=self.auth).content.decode()

    @property
    def name(self) -> str:
        if self._name is None:
            self.device_info_summary()
        return self._name

    def __repr__(self):
        return f'<{self.name}@{self.ip_address}>'

    @property
    def mac_address(self) -> str:
        if self._mac_address is None:
            self.device_info_summary()
        return self._mac_address

    def device_info_summary(self) -> Dict[str, Optional[str]]:
        info_html = self.get('info.html')
        soup = Soup(info_html)

        info = {}
        for row in soup.find_all('tr'):
            try:
                key, value = row.find_all('td')
                info[key.text[:-1]] = value.text
            except ValueError:  # len(td) == 1 or row is empty
                pass
        variables = dict(_VARS(info_html))
        if variables['dfltGw'] != '&nbsp':
            info['Default Gateway'] = variables['dfltGw']
        else:
            info['Default Gateway'] = variables['dfltGwIfc']
        self._name = info['BoardID'] = search(
            r'<td>(DSL-[^<]*)</td>', info_html)[1]
        self._mac_address = info['MAC Address']
        # todo:
        #    Software Version
        #    Bootloader (CFE) Version
        #    DSL PHY and Driver Version
        #    Wireless Driver Version
        #    ... (See info.html)
        return info

    def wan_info(self) -> Dict[str, Dict[str, str]]:
        """Return a dict from interface name to interface info."""
        rows = Soup(self.get('wancfg.cmd?action=view')).find('table').find_all(
            'tr')
        keys = [hd.text for hd in rows[0].find_all('td')[1:]]
        info = {}
        for row in rows[1:]:
            tds = row.find_all('td')
            info[tds[0].text] = {
                k: tds[i].text for i, k in enumerate(keys, 1)}
        return info

    def wireless_stations(self) -> List[Dict[str, str]]:
        rows = Soup(self.get('wlstationlist.cmd')).find_all('tr')
        keys = [i.string for i in rows[0].find_all('td')]
        return [
            dict(zip(keys, [i.string for i in row.find_all('td')]))
            for row in rows[1:]]

    def reboot(self) -> None:
        """Reboot the modem."""
        self.get('rebootinfo.cgi?')

    def ping(self, ip_address: str) -> str:
        pingtrace_html = self.get('pingtrace.html')
        ping_result = self.get(
            'pingtrace.cmd'
            '?action=ping'
            f'&address={ip_address}'
            f'&sessionKey={_SESSION_KEY(pingtrace_html)[1]}')
        return Soup(ping_result).find('textarea').string
