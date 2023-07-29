import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
# noinspection PyUnresolvedReferences
from local import *  # noqa: E402, F403

SITEURL = "https://blog.mrcsd.com"
