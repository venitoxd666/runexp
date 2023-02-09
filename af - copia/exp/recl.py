import os
import sys
import warnings
import rich

HELP = """
runs the lastest avaible version of runexp as interactive. No matter what runexp version is installed
"""

if(len(sys.argv) > 1):
    if(sys.argv[1].lower() == '-h'):
        rich.print(HELP)
        sys.exit(0)
    warnings.warn(
        "recl arguments are ignored, recl is an alias to run the last version of runexp interactive console.",
        UserWarning)
try:
    sys.exit(os.system('runexp runexp -c'))
except KeyboardInterrupt:
    pass