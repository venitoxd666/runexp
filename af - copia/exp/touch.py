import rich
import argparse
import os, sys
import win32api
import win32con
import runexp

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


def make_mode(file,mode_str:str, opts):
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
    folder = 0
    if not(os.path.exists(file)) and full_mode_str[1] != 'D':
        try:
            os.makedirs(os.path.dirname(file))
        except (OSError,ValueError) as e:
            pass
        open(file,"w").close()
    elif(not(os.path.exists(file))):
        folder = 1
        os.makedirs(file)
    
    if(opts.content and not(folder)):
        with open(file, opts.write_mode) as f:
            f.write(" ".join(opts.content))
    mode = 0
    if(full_mode_str[0] == 'H'):
        # win32api.SetFileAttributes(file, win32api.GetFileAttributes(file) |  win32con.FILE_ATTRIBUTE_HIDDEN)
        mode = mode | win32con.FILE_ATTRIBUTE_HIDDEN 

    if(full_mode_str[2] == 'S'):
        # win32api.SetFileAttributes(file, win32api.GetFileAttributes(file) | win32con.FILE_ATTRIBUTE_SYSTEM)
        mode = mode | win32con.FILE_ATTRIBUTE_SYSTEM

    if(full_mode_str[3] == 'E'):
        # win32api.SetFileAttributes(file, win32api.GetFileAttributes(file) |  win32con.FILE_ATTRIBUTE_ENCRYPTED)
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
        _file_argv = f"-f {file}"
        if(folder):
            _file_argv = f'-d {file}'
        runexp.RunExp().exec_from_command(
            f"encrypt "+_file_argv+' -m '+opts.encryption_method
        )
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
argp.add_argument(
    '-c', '--content',
    dest = "content",
    nargs = '+',
    default = "",
    help="Content to be in the file"
)

argp.add_argument(
    '-wm', 
    '--write-mode',
    dest="write_mode",
    default="a",
    choices=['a','w'],
    help="Write mode, \"w\" to overwrite, \"a\" to add."
)
argp.add_argument(
    '-em',
    '--encryption-method',
    dest='encryption_method',
    default="ntg",
    help="Encryption method to use. (to call encrypt with)"
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
            mode = opts.mode
            if('=' in file):
                file, mode = file.split('=',1)
            errno = make_mode(file, mode, opts)
            if(errno):
                sys.exit(errno)
        sys.exit(0)
    else:
        sys.exit(make_mode(opts.file[0], opts.mode,opts))

