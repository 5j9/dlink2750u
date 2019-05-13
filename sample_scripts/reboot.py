from pathlib import PurePath
from sys import path

path.insert(0, str(PurePath(__file__).parent.parent))
from dlink2750u import DLink2750U  # noqa: E402
from test.test_config import ip_address, auth  # noqa: E402


DLink2750U(ip_address=ip_address, auth=auth).reboot()
