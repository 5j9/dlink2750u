from atexit import register
from typing import List, Dict, Optional

from selenium.webdriver import Firefox, FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import \
    presence_of_element_located

firefox_options = FirefoxOptions()
firefox_options.headless = True
browser = Firefox(options=firefox_options)
browser_get = browser.get
select_all = browser.find_elements_by_css_selector
select_one = browser.find_element_by_css_selector
wait = WebDriverWait(browser, 30)


class DLink2750U:

    _name = _mac_address = None

    def __init__(self, ip_address: str, auth=('admin', 'admin')):
        self.ip_address = ip_address
        username, password = auth
        url = f'http://{username}:{password}@{ip_address}/'

        def load(path: str) -> None:
            """Load path in browser."""
            browser_get(url + path)

        self.load = load

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
        self.load('info.html')

        info = {}
        for tr in select_all('tr'):
            tds = tr.find_elements_by_css_selector('td')
            if not tds:
                continue
            td1, td2 = tds
            info[td1.text[:-1]] = td2.text

        self._name = info['BoardID']
        self._mac_address = info['MAC Address']
        return info

    def wan_info(self) -> Dict[str, Dict[str, str]]:
        """Return a dict from interface name to interface info."""
        self.load('wancfg.cmd?action=view')
        trs = select_all('tr')
        keys = [
            td.text for td in trs[0].find_elements_by_css_selector('td')[1:]]
        info = {}
        for tr in trs[1:]:
            tds = tr.find_elements_by_css_selector('td')
            info[tds[0].text] = {
                k: tds[i].text for i, k in enumerate(keys, 1)}
        return info

    def wireless_stations(self) -> List[Dict[str, str]]:
        self.load('wlstationlist.cmd')
        trs = select_all('tr')
        keys = [td.text for td in trs[0].find_elements_by_css_selector('td')]
        return [dict(zip(keys, [
            td.text for td in tr.find_elements_by_css_selector(
                'td')])) for tr in trs[1:]]

    def reboot(self) -> None:
        """Reboot the modem."""
        self.load('rebootinfo.cgi?')

    def ping(self, ip_address: str) -> str:
        self.load('pingtrace.html')
        select_one('[name=IPAddr]').send_keys(ip_address)
        select_one('[value=Ping]').click()
        textarea = wait.until(presence_of_element_located(
            (By.CSS_SELECTOR, 'textarea')))
        return textarea.text


def at_exit():
    browser.quit()


register(at_exit)
