"""Reapply ppp0 if there is no internet connection."""

from pathlib import PurePath
from sys import path
from time import sleep, localtime

path.insert(0, str(PurePath(__file__).parent.parent))
from dlink2750u import DLink2750U, skey  # noqa: E402
from test.test_config import ip_address, auth  # noqa: E402


router = DLink2750U(ip_address=ip_address, auth=auth)

ppp_user, ppp_pass = router.ppp_wan_service_user_pass('0')


def reapply():
    get = router.get
    session_key = skey(
        get('wanL3Edit.cmd?serviceId=1&wanIfName=ppp0&ntwkPrtcl=0'))
    session_key = skey(get(
        f'ntwksum2.cgi'
        f'?pppUserName={ppp_user}'
        f'&pppPassword={ppp_pass}'
        f'&enblOnDemand=0'
        f'&pppTimeOut=0'
        f'&keepalive=0'
        f'&keepalivetime=0'
        f'&alivemaxfail=5'
        f'&ManualPPPMTU=0'
        f'&pppMTU=1492'
        f'&enblManualPpp=0'
        f'&useStaticIpAddress=0'
        f'&pppLocalIpAddress=0.0.0.0'
        f'&pppIpExtension=0'
        f'&enblFirewall=1'
        f'&enblNat=1'
        f'&enblFullcone=0'
        f'&NatIpaddr=0.0.0.0'
        f'&pppAuthMethod=1'
        f'&pppServerName='
        f'&pppAuthErrorRetry=0'
        f'&enblPppDebug=0'
        f'&pppToBridge=0'
        f'&enblIgmp=0'
        f'&sessionKey={session_key}'))
    get(f'wancfg.cmd?action=add&sessionKey={session_key}')


if __name__ == '__main__':
    while True:
        connection_status = router.wan_info()['ppp0']['Status']
        if connection_status != 'Connected':
            reapply()
            lt = localtime()
            print(
                f'{lt.tm_hour}:{lt.tm_min}:'
                f' reapplied, ppp0 status: {connection_status}')
        sleep(60)
