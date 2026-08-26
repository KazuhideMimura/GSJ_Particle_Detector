from datetime import datetime

ORGANIZATION_NAME = "AIST"
APPLICATION_NAME = "GSJ Particle Detector"
PACKAGE_NAME = "gsjpd"

VERSION = 1
RELEASE = [0, 4]
PRE_RELEASE = ""

BUILD = datetime.now().strftime("%m%d%H%M")

__version__ = ".".join(map(str, [VERSION] + RELEASE))

if PRE_RELEASE:
    __version__ += f"{PRE_RELEASE}"

__build__ = __version__
if BUILD:
    __build__ += f"+{BUILD}"
