import rich
import sys

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