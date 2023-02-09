import sys,os
import subprocess
from runexp import RunExp



def _executer(expname, argv, runexp:RunExp):
    pth = os.path.join(runexp.af_path(), expname + '.py')
    pth_core = os.path.join(runexp.af_path(), '_nocolor_core' + '.py')

    popen = subprocess.Popen(
        args = ['python', pth_core, expname, *argv],
        cwd=runexp.cd
    )
    popen.wait()
    return popen.returncode

# ... execution

errno = RunExp(executer=_executer).run(
    exec=sys.argv[1] if len(sys.argv) > 1 else "",
    argv=sys.argv[2:] if len(sys.argv) > 2 else [],
    command_str=" ".join(sys.argv[1:] if len(sys.argv) > 1 else [])
)


sys.exit(errno)
