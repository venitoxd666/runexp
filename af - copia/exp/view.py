import rich,builtins
import os
import sys


def equals(obj1, obj2):
    equals_chars = 0
    bigger_comparison = max(len(obj1), len(obj2))

    def get(obj, index):
        if(index >= len(obj)):
            return ""
        return obj[index]

    for i in range(bigger_comparison):
        equals_chars += (get(obj1, i) == get(obj2, i))

    return equals_chars/bigger_comparison

def open(*a ,**k):
    try:
        return builtins.open(*a,**k)
    except Exception as e:
        file = a[0]
        if(os.path.isdir(file)):
            rich.print(f"[red]ERROR[/red]: Cannot open Directories. ({file} is a directory)")
            sys.exit(1)
        
        basepath, file = os.path.dirname(file), os.path.split(file)[-1]
        basepath = os.path.join(os.getcwd(), basepath)

        for fl in os.listdir(basepath):
            if(os.path.isdir(os.path.join(basepath, fl))):
                continue
            
            if(equals(fl, file) >= 0.85):
                rich.print(f"[red]ERROR[/red]: Cannot open file {file}. ¿Did you mean {fl}?")
                sys.exit(1)

        rich.print(f"[red]ERROR[/red]: Could not open file: {file}")            
        sys.exit(1)

HELP = """
Usage: view FILE
       view hex FILE [-c COLUMN_SPAN[INT]]
       view force_unicode FILE
       view json FILE

Version: 1.1.4

Changelog:
    1.0.0: Added basic behaviour for reading and displaying files.
        1.1.0: Added support for other file formats.
            1.1.1: Added support for binary files.
            1.1.2: Added support for json files.
            1.1.3: Added support for forcing to display as unicode
            1.1.4: Added support for modifing the hex number of columns.

"""

COLS = 8

def hex_view(file):
    if(isinstance(file, str)):
        f = open(file, 'rb')
    else:
        f = file
    col = f.read(COLS)
    while(col):
        count = 0
        for char in col:
            w = hex(char)[2:]
            if len(w) < 2:
                w = '0' + w
            rich.print(' ',end="")
            rich.print(f'[cyan]{w}[/cyan]',end="")
            count += 1
        while(count < COLS):
            rich.print(" ", end ="")
            rich.print("[cyan]· [/cyan]",end = "")
            count += 1

        rich.print(" [red]|[/red] ", end= "")
        count = 0

        for char in col:
            w = int.to_bytes(char, 1, 'big')
            try:
                w = w.decode()
            except Exception as e:
                w = '·'
            if(w == '\n'):
                rich.print("\\n", end = "")
                count += 1
                continue
            rich.print(' ',end="")
            rich.print(w,end="")    
            count += 1
        while(count < COLS):
            rich.print(" ", end ="")
            rich.print("[cyan]·[/cyan]",end = "")
            count += 1

        rich.print()
        
        col = f.read(COLS)
    
    f.close()
    return 0

def view(argv):
    global COLS
    hexview = False
        
    if('-c' in argv):
        i = argv.index('-c') + 1
        if i >= len(argv) or not(argv[i].isdigit()):
            rich.print("[red]ERROR[/red]: Invalid -c syntax, expected int.")
        COLS = int(argv[i])
    if('-h' in argv):
        rich.print(HELP) 
        return 0
    try:
        if argv[0] == 'hex':
            hexview = True
            file = argv[1]
        elif(argv[0] == 'json'):
            file = argv[1]
            f = (open(file, 'rb'))
            try:
                rich.print_json(f.read().decode())
            except:
                f.seek(0)
                return hex_view(f)
            sys.stdout.write('\n')
            return 0
        elif(argv[0] == 'force_unicode'):
            file = argv[1]
            f = (open(file, 'rb'))
            char = f.read(1)
            result = str()
            while(char):
                try:
                    result += char.decode()            
                except Exception:
                    result += "▯"
                char = f.read(1)

            rich.print(result)
            return 0
        elif(argv[0] == 'nocolor'):
            file = argv[1]
            f = (open(file, 'r'))
            chunk = f.read(COLS)
            while(chunk):
                sys.stdout.write(chunk)
                chunk = f.read(COLS)
            return 0
        else:
            file = argv[0]

    except IndexError:
        rich.print(f"[red]ERROR[/red]: Invalid view syntax. Check view -h for help.")
        return 1

    if(hexview):
        return hex_view(file)
    f = (open(file, 'rb'))
    try:
        rich.print(f.read().decode())
    except Exception:
        f.seek(0)
        return hex_view(f)
    sys.stdout.write('\n')

if __name__ == '__main__':
    argv=  sys.argv[1:] if len(sys.argv) > 1 else []
    try:
        sys.exit(view(argv))
    except KeyboardInterrupt:
        pass