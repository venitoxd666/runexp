import os
import sys
from rich.traceback import install
import rich
import subprocess
import tempfile
import shutil

HELP = """
Transforms a EXP program into a shell program.

Usage: build_exp [-h] <exp>

Note:
    if there's already a build version of the EXP program, 
    it'll give you the option to overwrite it or 
    create a new with a diferent name.
"""

install()

def _ensure_valid_argv(argv):
    if(not(len(argv))):
        rich.print(HELP)
        return 1


def main():
    argv = sys.argv[:]
    argv = argv[1:] if len(argv) > 1 else []
    if(_ensure_valid_argv(argv)):
        return 0
    expname = argv[0].lower()
    if(expname=='-h' or expname=='--help'):
        rich.print(HELP)
        return 0

    if(not(is_exp(expname))):
        rich.print(f'[red]ERROR(ERRNO=1):[/red]{expname} was not a valid EXP found. Please check the spelling and try again.')
        return 1

    return build(expname)

def build(expname):
    return pyinstaller_call(expname)

def pyinstaller_call(expname):
    if(expname.lower() == 'runexp'):
        rich.print(f'[yellow]WARNING:[/yellow]runexp is a especial required especial program. Consider it before overwritting it.')
        
    with tempfile.TemporaryDirectory() as tempdir:
        newpath = os.path.join(os.environ.get('AF_PATH','C:\\added_path\\af\\'),expname + '.exe')
        while(os.path.exists(newpath)):
            res = ''
            rich.print("[red]ERROR[/red]: There's already an executable for that EXP installed,")
            rich.print("       Select one")
            rich.print("       [red]A[/red]: Abort, stop operation")
            rich.print("       [red]Y[/red]: Yes,   overwrite existing.")
            rich.print("       [red]N[/red]: No,    name the new name")
            while(not(res in ['y','n','a'])):
                res = input(">>> ").lower()
            
            if(res == 'a'):
                rich.print("[red]Quitting...[/red]")
                return 1

            if(res == 'y'):
                os.remove(newpath)
                break
                           
            if(res == 'n'):
                newpath = os.path.join(os.environ.get('AF_PATH','C:\\added_path\\af\\'),
                                       input("(\"Enter the new name for the executable\")>>> ")+ '.exe')
            

        process = subprocess.Popen(
            ['pyinstaller',os.path.join(os.environ.get('AF_PATH','C:\\added_path\\af\\'),'exp',expname + '.py'),'--onefile','--exclude-module','tkinter'],shell=True, stdout=subprocess.PIPE,
            cwd=tempdir)

        process.wait()
        
        if(process.returncode):
            rich.print("[red]ERROR[/red]: Error while building using pyinstaller, check if it's installed, if not, check the output at ./build_exp_error_output.txt")
            with open('./build_exp_error_output.txt','wb') as f:
                f.write(process.stdout)
            return process.returncode
        
        shutil.move(
            os.path.join(tempdir, 'dist',expname + '.exe'),
            newpath
        )
    return 0

def is_exp(expname):
    path = os.path.join(os.environ.get('AF_PATH','C:\\added_path\\af\\'),'exp',expname + '.py')
    return os.path.exists(
        path
    ) and os.path.isfile(path)
    
if __name__ == '__main__':
    sys.exit(main())

