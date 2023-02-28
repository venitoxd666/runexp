
import sys
import shutil
import os
import rich

HELP = """
Usage: del PATH [PATH2, [PATH3...]] [-d]
where PATH is an existing PATH to a directory or file.
that file will be [red]removed[/red] [red]forever[/red].
if "-d" enabled, then will try to remove directories
"""

if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
    for i in range(1, len(sys.argv)):
        f = sys.argv[i]
        if(os.path.isdir(f) or '-d' in sys.argv):
            shutil.rmtree(f)
        else:
            os.remove(f)
else:
    rich.print(HELP)
