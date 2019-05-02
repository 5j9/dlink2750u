from functools import partial
from re import search, compile as re_compile, IGNORECASE
from typing import List, Dict, Optional, Union

from requests import Session
from bs4 import BeautifulSoup

_SESSION_KEY = re_compile(rb"sessionKey='?(\d*)", IGNORECASE).search
_VARS = re_compile(rb"var\s+(\w+)\s*=\s*'(.*?)';", IGNORECASE).findall

Soup = partial(BeautifulSoup, features='lxml')


class DLink2750U:
    _name = _mac_address = None

    def __init__(self, ip_address: str, auth=('admin', 'admin')):
        self.ip_address = ip_address
        self.url = f'http://{ip_address}/'
        self.auth = auth
        self.session = Session()

    def get(self, path: Union[str, bytes]) -> bytes:
        return self.session.request(
            'GET', self.url + path, auth=self.auth).content

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
        if variables[b'dfltGw'] != b'&nbsp':
            info['Default Gateway'] = variables[b'dfltGw'].decode()
        else:
            info['Default Gateway'] = variables[b'dfltGwIfc'].decode()
        self._name = info['BoardID'] = search(
            rb'<td>(DSL-[^<]*)</td>', info_html)[1].decode()
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

    def _first_row_table(self, path: str) -> List[Dict[str, str]]:
        rows = Soup(self.get(path)).find_all('tr')
        keys = [i.text for i in rows[0].find_all('td')]
        return [dict(zip(
            keys, [i.text for i in row.find_all('td')])) for row in rows[1:]]

    def route_info(self):
        """Device Info -- Route

        Flags legend:
            U: up
            !: reject
            G: gateway
            H: host
            R: reinstate
            D: dynamic (redirect)
            M: modified (redirect)
        """
        return self._first_row_table('rtroutecfg.cmd?action=view')

    def arp(self) -> List[Dict[str, str]]:
        """Return the ARP table."""
        return self._first_row_table('arpview.cmd')

    def dhcp(self) -> List[Dict[str, str]]:
        """Return  Device Info -- DHCP Leases."""
        return self._first_row_table('dhcpinfo.html')

    def wan_services(self):
        """Wide Area Network (WAN) Service Setup."""
        setup = self._first_row_table('wancfg.cmd')
        for i in setup:
            del i['Remove'], i['Edit']
        return setup

    def wireless_stations(self) -> List[Dict[str, str]]:
        """Return authenticated wireless stations and their status."""
        return self._first_row_table('wlstationlist.cmd')

    def reboot(self) -> None:
        """Reboot the router."""
        self.get('rebootinfo.cgi?')

    def ping(self, ip_address: str) -> str:
        pingtrace_html = self.get('pingtrace.html')
        ping_result = self.get(
            'pingtrace.cmd'
            '?action=ping'
            f'&address={ip_address}'
            f'&sessionKey={skey(pingtrace_html)}')
        return Soup(ping_result).find('textarea').text

    def trace_route(self, ip_address: str, timeout: int = 30) -> str:
        from time import sleep, time
        t0 = time()
        html = self.get('pingtrace.html')
        html = self.get(
            'pingtrace.cmd'
            '?action=trace'
            '&start=1'
            f'&address={ip_address}'
            f'&sessionKey={skey(html)}')
        while b'Trace complete.' not in html:
            html = self.get(
                'pingtrace.cmd'
                '?action=trace'
                '&start=2'
                f'&sessionKey={skey(html)}')
            sleep(1)
            if time() - t0 > timeout:
                raise TimeoutError
        return Soup(html).find('textarea').text

    def backup(self, filename=None) -> Optional[bytes]:
        """Backup configurations of Broadband Router.

        Return backup as a string of bytes if filename is None.
        """
        backup = self.get('backupsettings.conf')
        if filename is None:
            return backup
        with open(filename, 'bw') as f:
            f.write(backup)


def skey(html: bytes) -> str:
    return _SESSION_KEY(html)[1].decode()
