import requests
import sys,os
import rich
from hashlib import sha256

HELP = """
[Usage]: runexp update [[yellow]-h[/yellow]] [[yellow]-a[/yellow]] EXP

Updates the EXP given (if possible.)
( when -a activated, ignores the rest of the argv and just updates everything)
"""

def af_path():
    return os.path.join(os.environ.get('AF_PATH','C:/added_path/af'),'exp')

SPI_SETDESKWALLPAPER = 20 

def _update(expname):
    
    req = requests.get(
        f"https://raw.githubusercontent.com/venitoxd666/runexp/main/af%20-%20copia/exp/{expname}.py"
    )
    if(req.status_code != 200):
        rich.print("[red]ERROR[/red]: Invalid request status: %s" % req.status_code)
    req_text = req.text.replace("\r\n", "\n")
    try:
        shall_replace = 0
        
        with open(os.path.join(af_path(), expname + '.py'), 'r', encoding='utf-8') as f:
            
            f.seek(0)
            shall_replace = f.read() != req_text

    except Exception as e:
        shall_replace = 2
        
    if not(shall_replace):
        rich.print("Already in last version")
        return
    
    if(shall_replace):
        rich.print("Installing new EXP...")
    
    sys.stdout.write("[%s]" % (" " * 100))
    sys.stdout.flush()
    sys.stdout.write("\b" * (100+1)) # return to start of line, after '['
    step = len(req_text)//100 + 1
    with open(os.path.join(af_path(), expname + '.py'), 'w', encoding='utf-8') as f:
        for index, char in enumerate(req_text):
            if(index % step == 0):
                sys.stdout.write("-")
                sys.stdout.flush()
            try:
                f.write(char)
            except KeyboardInterrupt:
                # cant interrupt the installation process as that would mean the file hasnt copied correctly.
                f.write(char)
    sys.stdout.write("\n")
    

def main():
    if ((len(sys.argv) != 2)):
        rich.print(f"[red]ERROR[/red]: Expected 2 arguments.")
        sys.exit(1)

    if(sys.argv[1] == '-h'):
        rich.print(HELP)
        return 0
    
    if(sys.argv[1].lower() == '-a'):
        for file in os.listdir(af_path()):
            if not(os.path.isfile(os.path.join(af_path(), file))):
                continue
                
            rich.print(f"Updating [{file[:-3]}]")

            _update(file[:-3])

        sys.exit(0)
    
    _update(sys.argv[1])
    
if __name__ == "__main__":
    main()
