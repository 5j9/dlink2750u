
from functools import partial
from re import search, compile as re_compile, M
from typing import List, Dict, Optional, Tuple, Union

from requests import Session
from bs4 import BeautifulSoup

# var sessionKey='1234567890'; OR loc += '&sessionKey=1234567890';
_SESSION_KEY = re_compile(rb"sessionKey='?(\d+)", M).search
_VARS = re_compile(rb"^\s*var\s+(\w+)\s*=\s*'(.*?)';\s*(?://.*)?$", M).findall

Soup = partial(BeautifulSoup, features='lxml')


class DLink2750U:
    _name = _mac_address = None

    def __init__(self, ip_address: str, auth=('admin', 'admin')):
        self.ip_address = ip_address
        self.url = f'http://{ip_address}/'
        self.auth = auth
        self.session = Session()

    def get(self, path: str) -> bytes:
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
        js_vars = variables(info_html)
        if js_vars[b'dfltGw'] != b'&nbsp':
            info['Default Gateway'] = js_vars[b'dfltGw']
        else:
            info['Default Gateway'] = js_vars[b'dfltGwIfc']
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
        rows = Soup(self.get(
            'wancfg.cmd?action=view')).find('table').find_all('tr')
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

    def wan_services(self) -> List[Dict[str, str]]:
        """Wide Area Network (WAN) Service Setup."""
        setup = self._first_row_table('wancfg.cmd')
        for i in setup:
            del i['Remove'], i['Edit']
        return setup

    def ppp_wan_service_user_pass(
        self, service_id: Union[str, int]
    ) -> Tuple[str, str]:
        return self._user_pass_from_setup_edit(
            self._wan_service_setup_edit(service_id))

    @staticmethod
    def _user_pass_from_setup_edit(html: bytes) -> Tuple[str, str]:
        username, password = search(
            rb"^\s*pppUserName.value = '(.*?)';"
            rb"\s*pppPassword.value = '(.*?)';\r?$", html, M).groups()
        return username.decode(), password.decode()

    def _wan_service_setup_edit(self, service_id: Union[str, int]) -> bytes:
        # serviceId is always 1 for edit and 0 for add
        return self.get(
            f'wanL3Edit.cmd'
            f'?serviceId=1'
            f'&wanIfName=ppp{service_id}'
            f'&ntwkPrtcl=0')

    def ppp_wan_service_reapply(self, service_id) -> None:
        """Reapply wan service.

        This method can be used as faster alternative to reboot for
        trying to reconnect.
        """
        setup_edit = self._wan_service_setup_edit(service_id)
        username, password = self._user_pass_from_setup_edit(setup_edit)
        js_vars = variables(setup_edit)
        path = (
            'ntwksum2.cgi'
            f'?pppUserName={username}'
            f'&pppPassword={password}'
            f'&enblOnDemand={js_vars[b"onDemand"]}'
            f'&pppTimeOut={js_vars[b"timeOut"]}')
        if js_vars[b'supportkeepalive'] == '1':
            keep_alive_time = search(
                rb"time\.value='(\d+)';", setup_edit)[1].decode()
            path += (
                f'&keepalive={js_vars[b"keepalive"]}'
                f'&keepalivetime={keep_alive_time}')
        alive_max_fail = search(
            rb"maxfail\.value='(\d+)';", setup_edit)[1].decode()
        ppp_server_name = search(
            rb"pppServerName\.value\s*=\s*'(.*?)';", setup_edit)[1].decode()
        wan_setup_summary = self.get(
            path +
            f'&alivemaxfail={alive_max_fail}'
            f'&ManualPPPMTU={js_vars[b"pppManualmtu"]}'
            f'&pppMTU={js_vars[b"pppMTUValue"]}'
            f'&enblManualPpp={js_vars[b"buildManualPpp"]}'
            f'&useStaticIpAddress={js_vars[b"enblIpAddr"]}'
            f'&pppLocalIpAddress={js_vars[b"localIpAddr"]}'
            f'&pppIpExtension={js_vars[b"ipExtension"]}'
            f'&enblFirewall={js_vars[b"pppFirewall"]}'
            f'&enblNat={js_vars[b"enblNatoption"]}'
            f'&enblFullcone={js_vars[b"fullcone"]}'
            f'&NatIpaddr={js_vars[b"NatIp"]}'
            f'&pppAuthMethod={js_vars[b"authMethod"]}'
            f'&pppServerName={ppp_server_name}'
            f'&pppAuthErrorRetry={js_vars[b"pppAuthErrorRetry"]}'
            f'&enblPppDebug={js_vars[b"pppDebug"]}'
            f'&pppToBridge={js_vars[b"ppptobr"]}'
            f'&enblIgmp={js_vars[b"enableIgmp"]}'
            f'&sessionKey={skey(setup_edit)}')
        self.get('wancfg.cmd?action=add&sessionKey=' + skey(wan_setup_summary))

    def remove_wan_service(self, service: str):
        self.get(
            f'wancfg.cmd'
            f'?action=remove'
            f'&rmLst={service}'
            f'&sessionKey={skey(self.get("wancfg.cmd"))}')

    def wireless_stations(self) -> List[Dict[str, str]]:
        """Return authenticated wireless stations and their status."""
        return self._first_row_table('wlstationlist.cmd')

    def backup(self, filename=None) -> Optional[bytes]:
        """Backup configurations of Broadband Router.

        Return backup as a string of bytes if filename is None.
        """
        backup = self.get('backupsettings.conf')
        if filename is None:
            return backup
        with open(filename, 'bw') as f:
            f.write(backup)

    def reboot(self) -> None:
        """Reboot the router."""
        self.get('rebootinfo.cgi?')

    def ping(self, ip_address: str) -> str:
        return Soup(self.get(
            'pingtrace.cmd'
            '?action=ping'
            f'&address={ip_address}'
            f'&sessionKey={skey(self.get("pingtrace.html"))}'
        )).find('textarea').text

    def trace_route(self, ip_address: str, timeout: int = 30) -> str:
        from time import sleep, time
        t0 = time()
        html = self.get(
            'pingtrace.cmd'
            '?action=trace'
            '&start=1'
            f'&address={ip_address}'
            f'&sessionKey={skey(self.get("pingtrace.html"))}')
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


def skey(html: bytes) -> str:
    return _SESSION_KEY(html)[1].decode()


def variables(html: bytes) -> Dict[bytes, str]:
    return {k: v.decode() for k, v in _VARS(html)}
