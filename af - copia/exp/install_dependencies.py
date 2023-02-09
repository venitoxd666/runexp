import os

if(os.system("python -c \"import sys\nif(sys.version_info[0]!=3):sys.exit(1)\"")):
    raise RuntimeError("Python Must be Python 3")
os.system("python -m pip install rich")
os.system("python -m pip install PyInstaller")
os.system("python -m pip install pywin32")
os.system("python -m pip install anytree")
os.system("python -m pip install maskpass")
os.system("python -m pip install windows-curses")