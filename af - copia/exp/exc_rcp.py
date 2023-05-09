import runpy
import sys
import os

file = sys.argv[1]
rest = sys.argv[2:] if len(sys.argv) > 1 else []

sys.path.append(os.getcwd())

runpy.run_path(file)