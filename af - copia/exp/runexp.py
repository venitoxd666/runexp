import sys
import os
import time
import warnings
import rich
import subprocess
import io
import win32clipboard
import msvcrt

DEBUG = False

RUNEXP_HELP = """
\[Usage]: runexp [[yellow]-h[/yellow]] [[yellow]-nc[/yellow]][[yellow]-e[/yellow]] [[yellow]--isexp[/yellow]] [[yellow]-c[/yellow]] [green]programName[/green] [[yellow]argument0[/yellow],[[yellow]argument1[/yellow],[yellow]...[/yellow]]]

[red]Version  [/red]: [green]1.3.0[/green]
[red]Changelog[/red]:
   [yellow]1.0.0[/yellow]: basic runexp behaviour
   [yellow]1.1.0[/yellow]: added "-c" option and "-h" option. Bug found searching for exp programs
   [yellow]1.2.0[/yellow]: added this changelog.
        [yellow]1.2.1[/yellow]: added "-e" to show errno of program.
        [yellow]1.2.2[/yellow]: added accesible debug and added the "--isexp" option
        [yellow]1.2.3[/yellow]: added "--history" option.
        [yellow]1.2.4[/yellow]: FINALLY REMOVED THAT FUCKING BUG (in exachange of portability)
        [yellow]1.2.5[/yellow]: changed usage to quit 'list' since it's a whole new application. Check runexp list -h for it's help and usage
        [yellow]1.2.6[/yellow]: code rewritten. x10-x20 times cleaner, no external change to user
        [yellow]1.2.7[/yellow]: CD Works!!!
        [yellow]1.2.8[/yellow]: Reworked code, more estability with argument order.
        [yellow]1.2.9[/yellow]: Reworked code, more general stability and many bug fixes (with interactive shell).
        [yellow]1.2.10[/yellow]: Reworked code, "-nc" added (experimental)
        [yellow]1.2.11[/yellow]: Added support for Up arrow to go to the last command.
    [yellow]1.3.0[/yellow]: Mayor input improvements. ( Input coloring (beta),autocompletition)

BUGS:
    · argument order may generate problems
    · CD with ./Something does not work.
    · CTRL + C may cause a crash.

Options:
  [yellow]-h[/yellow]            Show this help message and exit
  [yellow]-c[/yellow]            runs a interactive shell that handles [[red]"cmd.exe"[/red], [red]"runexp.exe"[/red]] (this allows you to run easily multiple exp commands)
  [yellow]-e[/yellow]            runs the program followed by this option and prints the errno.
  [yellow]--isexp[/yellow]       prints if the following program is a exp command or a shell command and execute it.
  [yellow]-nc[/yellow]           suppress coloring.

in Interactive Shell Mode ([yellow]-c[/yellow])
run:
    [red]exit[/red]          Exit the program
    [red]-h[/red]            Prints this message
    [red]-c[/red]            Enter another Shell Mode runexp instance.
    [red]-e[/red]            Print Programs errno.
    [red]--isexp[/red]       prints if the following program is a exp command or a shell command and executes it.
    [red]--history[/red]     prints execution history.
    [red]-nc[/red]           supress coloring.
"""

class InputHandler(object):
    def __init__(self, runexp):
        self.runexp = runexp    
        self.buff = sys.stdout

    def write(self, *a):
        self.buff.write(*a)
    
    def flush(self):
        self.buff.flush()

    def _substract(self,a, b):
        return a[len(b):]

    def input(self, prompt = ""):
        buffer = ""
        cindex = 0
        fr = self.runexp.freq
        rec = ""
        
        state = []
        
        def _erase_rec():
            self.buff.write("\b \b" * len(rec))
            self.buff.flush()
        
        print(prompt, flush=True, end = "")
        while(1):
            fr, rec = self.runexp.get_recomendations(fr, buffer)
            rec = self._substract(rec, buffer)
            if(rec):
                self._print_rec(rec)
            char = msvcrt.getch()
            if(char == b"\xe0"):
                char = msvcrt.getch()
                if(char == b'H'):
                    _erase_rec()
                    self.buff.write("\b \b" * len(buffer))
                    try:
                        buffer = runexp.command_registry[-(cindex + 1)]
                    except IndexError:
                        buffer = ""
                        cindex = 0
                    else:
                        cindex += 1
                    self.buff.write(buffer)
                    self.buff.flush()
                    rec = ""
                    continue
                if(char == b'P'):
                    _erase_rec()
                    self.buff.write("\b \b" * len(buffer))
                    try:
                        buffer = runexp.command_registry[-(cindex)]
                    except IndexError:
                        buffer = ""
                        cindex = 0
                    else:
                        cindex -= 1
                    self.buff.write(buffer)
                    self.buff.flush()
                    rec = ""
                    continue
                continue
            if(char == b'\x03'):
                # Ctrl-C
                raise KeyboardInterrupt
            if(char == b'\r'):
                break
            if(char == b'\x16'):
                _erase_rec()
                self.buff.write("\b \b" * len(buffer))
                win32clipboard.OpenClipboard()
                buffer = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                self.buff.write(buffer)
                self.buff.flush()
                continue
            if (char == b'\t' and rec):
                _erase_rec()
                buffer += rec
                self.buff.write(rec)
                self.buff.flush()
                continue
            if (char == b'\x08'):
                if not len(buffer):
                    continue
                buffer = buffer[:-1]  
                _erase_rec()
                self.buff.write("\b \b")
                self.buff.flush()
                continue
            try:
                char = char.decode()
            except Exception as e:
                char = chr(char[0])
            buffer += char
            _erase_rec()
            if(char.isdigit()):
                self._print_colored(char, "cyan1")
            elif(char == "-"):
                self._print_colored(char, 'orange3')
                if (len(state) and state[-1] != 1) or not(len(state)):
                    state.append(1)

            elif(char == " "):
                if(len(state) and state[-1] == 1):
                    state = state[:-1]
                if(len(state) and state[-1] == 3):
                    state = state[:-1]
                self.buff.write(" ")
                self.buff.flush()
            elif(char == "\""):
                if(len(state) and state[-1] != 2) or not(len(state)):
                    state.append(2)
                self._print_colored("\"", 'green')
            else:
                try:
                    st = state[-1]
                except IndexError:
                    st = 0
                if not(st):
                    self.buff.write(char)
                elif(st == 1):
                    self._print_colored(char, 'red')
                elif(st == 2):
                    self._print_colored(char, 'green')
                elif(st == 3):
                    self._print_colored(char, 'blue')                    
            self.buff.flush()
        
        self.buff.write("\n")
        self.buff.flush()
        return buffer

    def _print_colored(self, str, color):        
        if (rich.print("\\//67", file = io.StringIO())):
            self.buff.write(str)
        else:
            rich.print(f"[{color}]{str}[/{color}]", flush = True, end="")
        
    def _print_rec(self, rec):
        if (rich.print("\\//67", file = io.StringIO())):
            self.buff.write(rec.upper())
        else:
            rich.print(f"[grey35]{rec}[/grey35]", end = "", flush = True)

def _decode_input(password_input, cache = {}):
    def _(res):
        if len(res) >= 30:
            cache[password_input] = res
        return res
        
    if(len(password_input) >= 30 and password_input in cache):
        return cache[password_input]

    try:
        return _(password_input.decode())
    except Exception as e:
        res = ""
        for char in password_input:
            try:
                res += int.to_bytes(char, 1, 'big').decode()
            except Exception as e:
                res += "▯"
        return _(res)
    
def _default(expname, argv,runexp:"RunExp"):
    popen = subprocess.Popen(
        args = ['python', os.path.join(runexp.af_path(), expname + '.py'), *argv],
        cwd=runexp.cd
    )
    popen.wait()
    return popen.returncode

class RunExp(object):
    def __init__(self, executer = _default):
        self.cd = os.getcwd()
        self.history = []
        self.debug = False
        self.interactive_run = True
        self.executer = executer
        self.command_registry = []
        self.freq = {}
        self.inp = InputHandler(self)
    
    def _argv(self,argv):
        return argv[1:] if len(argv) >= 2 else []
    
    def get_recomendations(self, filtered, command):
        if(command == ''):
            return filtered, ""
        order = []
        for cmd in filtered:
            if not(cmd.startswith(command)):
                continue
            order.append({"cmd":cmd, "freq":filtered[cmd]})
        new_filtered = {}
        for obj in order:
            if(len(obj['cmd'])/len(command) >= 0.4):
                new_filtered[obj['cmd']] = obj['freq']


        best = {"cmd":"", "freq":0}
        for cmd in new_filtered:
            if(new_filtered[cmd] > best['freq']):
                best = {"cmd":cmd, "freq":new_filtered[cmd]}

        return new_filtered, best['cmd']

    def upd_freq(self, cmd):
        if cmd in self.freq.keys():
            self.freq[cmd] += 1
            return
        self.freq[cmd] = 1
    
    def interactive(self):
        last_ki = 0
        while(isinstance(self.interactive_run,bool)):
            try:
                command = self.inp.input(f'(RUNEXP){self.cd}> ')
            except (KeyboardInterrupt,EOFError):
                print("^C")
                if(last_ki):
                    return 0
                last_ki = 1
                continue
            
            last_ki = 0
    
            command_split = self.split_command(command)
            if not(len(command_split)):
                continue
            
            self.command_registry.append(command)
            self.upd_freq(command)
    
            self.execute_command(command_split,command_split,command)
            
        errno = self.interactive_run
        self.interactive_run = True
        return errno
    
    def execute_command(self, argv,argc,cmd_str):
        executable = argv[0]
        argv = self._argv(argv)
        if(executable == 'exit'):
            errno = 0
            if(len(argv)):
                try:
                    errno = int(argv[0])
                except ValueError:
                    pass

            self.interactive_run = errno
            return
        self.main(argc,cmd_str = cmd_str)

    def is_exp(self,expname):
        p = (os.path.join(self.af_path(),expname + '.py'))
        res= os.path.exists(p) and os.path.isfile(p)
        if(self.debug):
            print(f"Is {expname} a exp? Search={p}, Res={res}")
        return res
    
    def af_path(self):
        return os.path.join(os.environ.get('AF_PATH','C:/added_path/af'),'exp')

    def get_exec_type(self,exec):
        if(self.is_exp(exec)):
            return 'EXP'
        return 'SHELL'

    def __cd_to_history(self,_, path,errno = 0):
        self.history.append({
                'string':'cd '+path,
                'type':'SHELL',
                'errno':errno
        })

    def exec_cd(self, argv, cmd_str):
        if('.' in cmd_str):
            warnings.warn('CD might not work using ./ or things with \".\"')
        path = ""
        if(argv == []):
            print(self.cd)
            if(cmd_str):
                self.__cd_to_history(cmd_str, path)
            return 0
        errno = 0
        if(argv[0] == 'LOCAL'):
            argv[0] = self.af_path()
        a = subprocess.Popen(['cd',*argv,'&&','cd'],shell=True, stdout=subprocess.PIPE,cwd=self.cd)
        a.wait()
        errno = a.returncode
        path = a.stdout.read()[:-2].decode()
        if(os.path.exists(path) and os.path.isdir(path)):
            self.cd = path
        self.__cd_to_history(cmd_str, path,errno)
        return errno

    def run_nocolor(self, argv, cmd_str):        
        errno = self.run('nocolor', argv, command_str=cmd_str)
        return errno

    def run(self,exec, argv,command_str = ""):
        argc = len(argv)
        a = [exec]
        a.extend(argv)
        if(a[0] == '-c'):
            print("Entering interactive mode")
            return self.interactive()
        
        if(a[0] == '-h'):
            try:
                if(rich.print("\\//67", file=io.StringIO())):
                    rich.print(RUNEXP_HELP)
                    return 0
            except Exception as e:
                pass
            rich.print(RUNEXP_HELP[1:])
            return 0
        
        if(a[0] == 'debug' and argc == 1):
            self.debug = True
            return 0
    
        if(a[0] == '--isexp'):
            return self.his_exp_run(self._argv(a),cmd_str=command_str)
        
        if(a[0] == '-e'):
            return self.run_with_errno_print(self._argv(a),cmd_str=command_str)
        
        if(a[0] == '-nc'):
            return self.run_nocolor(self._argv(a), cmd_str=command_str)
        
        if(a[0] == '--history'):
            for obj in self.history:
                rich.print(f"Command[[red]\"{obj['string']}\"[/red]]=[green]{obj['type']}[/green] (Exited with [red]ERRNO={obj['errno']}[/red])")
            self.history.append({'string':'--history','type':'SHELL','errno':0})
            return 0
        
        if(a[0]=='--numofcommands'):
            rich.print(f"NumberOfCommands({len(self.history)})")
            return 0
        
        type = self.get_exec_type(exec)

        if(type == 'EXP'):
            errno = self.executer(exec, argv,self)
            self.history.append({
                'string':command_str or 'NORECORD',
                'type':type,
                'errno':errno
            })
        else:
            full_argv = [exec]

            if(exec == 'cd'):
                return self.exec_cd(argv, command_str)
            if(exec == ''):
                return 0

            full_argv.extend(argv)

            if(self.debug):
                print("Final Execution:",full_argv)
            try:
                popen = subprocess.Popen(
                    full_argv, cwd=self.cd,stdout = sys.stdout,shell=True
                )
                popen.wait()
                errno = popen.returncode
            except KeyboardInterrupt:
                print("^C")
                errno = 1
            self.history.append({
                'string':command_str or 'NORECORD',
                'type':type,
                'errno':popen.returncode
            })


        return errno

    def split_command(self, cmd):
        """an Advanced command splitting function to make arguments better

        Args:
            cmd (str): command to be splitted

        Returns:
            List[str]: list of arguments.
        """
        res = []
        curr = ""
        in_coutes = False
        for c in cmd:
            if(in_coutes):
                if(c=="\""):
                    in_coutes = False
                    continue
                curr += c
                continue
            
            if(c=="\""):
                in_coutes = True
                continue
            
            if(c == ' ' or c == '\t'):
                res.append(curr)
                curr = ""
                continue
            curr += c
        
        if(curr):
            res.append(curr)
        
        while ('' in res):
            res.remove('')
        
        return res
    
    def his_exp_run(self, argv,cmd_str=""):
        errno = self.run(argv[0] if len(argv) else '', self._argv(argv),command_str=cmd_str)
        obj = self.history[-1] if len(self.history) else {'string':'NOCOMMAND','type':'NOCOMMAND','errno':0}
        rich.print(f"Command[[red]\"{obj['string']}\"[/red]]=[green]{obj['type']}[/green]")
        return errno
    
    def run_with_errno_print(self, argv,cmd_str=""):
        errno = self.run(argv[0] if len(argv) else '', self._argv(argv),command_str=cmd_str)
        obj = self.history[-1] if len(self.history) else {'string':'NOCOMMAND','type':'NOCOMMAND','errno':0}
        
        rich.print(f"Command[[red]\"{obj['string']}\"[/red]]={'[green]SUCCES[/green]' if errno == 0 else '[red]ERROR[/red]'};    [red]({hex(errno)})[/red]")
        return errno
    
    def main(self, argv,cmd_str = ""):
        argc = len(argv)
        if(self.debug):
            print("Executing:",argv)
        
        if(argc < 1):
            rich.print(f'[red]Error: required at least 1 argument. (ARGC={argc}, ARGV={argv},ERRNO=1)[/red]')
            return 1       
        try:
            return self.run(argv[0], self._argv(argv),command_str= cmd_str)
        except KeyboardInterrupt:
            print("^C")
            return 1

if __name__ == '__main__':
    runexp = RunExp()
    runexp.main(runexp._argv(sys.argv))