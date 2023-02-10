import requests
import sys,os
import rich
from hashlib import sha256

HELP = """
[Usage]: runexp update [[yellow]-h[/yellow]] EXP

Updates the EXP given (if possible.)
"""

def af_path():
    return os.path.join(os.environ.get('AF_PATH','C:/added_path/af'),'exp')


def _update(expname):
    req = requests.get(
        f"https://raw.githubusercontent.com/venitoxd666/runexp/main/af%20-%20copia/exp/{expname}.py"
    )
    if(req.status_code != 200):
        rich.print("[red]ERROR[/red]: Invalid request status: %s" % req.status_code)
    try:
        shall_replace = 1
        with open(os.path.join(af_path(), expname + '.py'), 'r') as f:
            current_hash = sha256(f).hexdigest()
            if(sha256(req.text).hexdigest() == current_hash):
                shall_replace = 0

    except Exception as e:
        shall_replace = 2
        
    if not(shall_replace):
        rich.print("Already in last version")
        return
    
    if(shall_replace == 2):
        rich.print("Installing new EXP...")
    
    sys.stdout.write("[%s]" % (" " * 100))
    sys.stdout.flush()
    sys.stdout.write("\b" * (100+1)) # return to start of line, after '['
    step = len(req.text)//100 + 1
    with open(os.path.join(af_path(), expname + '.py'), 'w') as f:
        for index, char in enumerate(req.text):
            if(index % step == 0):
                sys.stdout.write("-")
                sys.stdout.flush()
            try:
                if(char == '\r'):
                    continue
                f.write(char)
            except KeyboardInterrupt:
                pass
    sys.stdout.write("\n")

def main():
    if ((len(sys.argv) != 2)):
        rich.print(f"[red]ERROR[/red]: Expected 2 arguments.")
        sys.exit(1)

    if(sys.argv[1] == '-h'):
        rich.print(HELP)
        return 0
    
    _update(sys.argv[1])
    
if __name__ == "__main__":
    main()
