import rich
import argparse
import os, sys
import win32api
import win32con
import win32file

DEFAULT = "VFNNRN"

HELP  = """
[yellow]-m[/yellow] | [yellow]--mode[/yellow] usage:
    -m mode
    where mode is a bunch of letters that follows the same pattern as ls. (following the same order)
    not all modes works, 
        [red] · Encrypted[/red]
        [red] · Virtual[/red]
    cannot be set,
    "-" use default attribute there
    example:
        # it's a folder (V for visible)
        [yellow]-m[/yellow] [green]VD [/green]
        # temporal file
        [yellow]-m[/yellow] [green]VF--T[/green]

note if creating more than 1 file, the files must be listed and divided by ","
Example:
    touch file, file1 -> created file and file1
    touch file,file1  -> created file and file1
    touch file file1  -> created file named "file file1"
    
"""


def make_mode(file,mode_str:str):
    full_mode_str = ""
    mode_str = mode_str.upper()
    for i in range(len(DEFAULT)):
        if(i >= len(mode_str)):
            full_mode_str += DEFAULT[i:]
            break
        if(mode_str[i] == '-'):
            full_mode_str += DEFAULT[i]
            continue
        full_mode_str += mode_str[i]

    if not(os.path.exists(file)) and full_mode_str[1] != 'D':
        try:
            os.makedirs(os.path.dirname(file))
        except (OSError,ValueError) as e:
            pass
        open(file,'w').close()
    elif(not(os.path.exists(file))):
        os.makedirs(file)
    mode = 0
    if(full_mode_str[0] == 'H'):
        # win32api.SetFileAttributes(file, win32api.GetFileAttributes(file) |  win32con.FILE_ATTRIBUTE_HIDDEN)
        mode = mode | win32con.FILE_ATTRIBUTE_HIDDEN 

    if(full_mode_str[2] == 'S'):
        # win32api.SetFileAttributes(file, win32api.GetFileAttributes(file) | win32con.FILE_ATTRIBUTE_SYSTEM)
        mode = mode | win32con.FILE_ATTRIBUTE_SYSTEM

    if(full_mode_str[3] == 'E'):
        # win32api.SetFileAttributes(file, win32api.GetFileAttributes(file) |  win32con.FILE_ATTRIBUTE_ENCRYPTED)
        rich.print("[yellow]Warning[/yellow]:File attribute \"ENCRYPTED\" cannot be applied (may be applied, should not.)")
        mode = mode | win32con.FILE_ATTRIBUTE_ENCRYPTED

    if(full_mode_str[4] == 'T'):
        # win32api.SetFileAttributes(file, win32api.GetFileAttributes(file) |  win32con.FILE_ATTRIBUTE_TEMPORARY)
        mode = mode | win32con.FILE_ATTRIBUTE_TEMPORARY

    if(full_mode_str[5] == 'V'):
        # win32api.SetFileAttributes(file, win32api.GetFileAttributes(file) |  win32con.FILE_ATTRIBUTE_VIRTUAL)
        rich.print("[yellow]Warning[/yellow]:File attribute \"VIRTUAL\" cannot be applied (may be applied, should not.)")
        mode = mode | win32con.FILE_ATTRIBUTE_VIRTUAL
    win32api.SetFileAttributes(file, mode)

    if(mode & win32con.FILE_ATTRIBUTE_ENCRYPTED):
        print("Encrypting..")
        # win32file.EncryptFile(file)
        # TODO: encrypt call

        rich.print("[red]Failed[/red]")
        return 1

    return 0

argp = argparse.ArgumentParser(prog="touch")

def print_help():
    argparse.ArgumentParser.print_help(argp)
    rich.print(HELP)


argp.print_help = print_help

argp.add_argument(
    "file", nargs='+'
)
argp.add_argument(
    '-m','--mode',dest='mode',
    default=DEFAULT
)


if __name__ == '__main__':
    opts = argp.parse_args()
    opts.file = ' '.join(opts.file)
    
    opts.file = opts.file.split(',')
    
    files = []
    for file in opts.file:
        if(file.startswith(" ")):
            files.append(file[1:])
            continue
        files.append(file)
    
    if len(files) > 1:
        for file in files:
            errno = make_mode(file, opts.mode)
            if(errno):
                sys.exit(errno)
        sys.exit(0)
    else:
        sys.exit(make_mode(opts.file[0], opts.mode))

