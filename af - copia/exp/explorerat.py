import os
from argparse import ArgumentParser

ap = ArgumentParser(
    prog = "explorerat",
    usage = "explorerat PATH",
    description="Open the windows file explorer at a given path"
)

ap.add_argument('path', help = "Path to the file explorer, \".\" to open it here.",nargs = '+')

def explorer_at(path):
    path = " ".join(path)
    if(path == '.'):
        path = os.getcwd()
    os.system(f"%SYSTEMROOT%\explorer.exe /e,\"{path}\"")

if __name__ == '__main__':
    try:
        opts = ap.parse_args()
    
        explorer_at(opts.path)
    except KeyboardInterrupt:
        pass