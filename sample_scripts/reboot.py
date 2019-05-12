from sys import path
path.append(__file__.rpartition('/')[0].rpartition('/')[0])
from dlink2750u import DLink2750U  # noqa: E402
from test.test_config import ip_address, auth  # noqa: E402
DLink2750U(ip_address=ip_address, auth=auth).reboot()
