import rich
import shutil
import os
import sys

HELP = """
usage: runexp esexp [-h] BUILDED_EXP
Erases a builded EXP

"""

def _runexp_path():
    return os.environ.get('AF_PATH',
                          'C:\\added_path\\af\\')

def main(argv):
    if(argv[0].lower()=='-h' or argv[0].lower()=='--help'):
        rich.print(HELP)
        return 0
    
    path = os.path.join(_runexp_path(), argv[0] + '.exe')
    if(not(os.path.exists(path))):
        rich.print(f"[red]ERROR[/red]: Could not find anything at {argv[0]}")
        return 1
    if(not(os.path.isfile(path))):
        rich.print(f'[red]ERROR[/red]: Could not find a file at {argv[0]}')
    
    os.remove(path)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:] if len(sys.argv) > 1 else []))

