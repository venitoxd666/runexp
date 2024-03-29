
# made for runexp list

import json
import os,sys,io
import rich
from rich.style import Style
from rich.traceback import install
import argparse

install()

ADDED_HELP = """
Version: 1.2.0 ([orange_red1]beta[/orange_red1])
Changelog:
    1.0.0: Added basic behaviour. (--nocolor | -nc already in support)
        1.0.1: Added -d | --path to change to custom directory. (Activate -p to run on the current directory)
        1.0.2: bugs fix
        1.0.3: Added --filter option (with limitations)
        1.0.4: Added lib support.
    1.2.0: Code rewritten, mayor improvements
        1.2.1: Added reconfiguration support, check list -c help for reconfiguration usage
"""

parser = argparse.ArgumentParser(
    prog = "runexp list",
    description="List all experimental features",
)

def _overwritten_print_help():
    argparse.ArgumentParser.print_help(parser)
    rich.print(ADDED_HELP)

parser.print_help = _overwritten_print_help
"""
parser.add_argument('--nocolor','-nc', action='store_true', dest="nocolor",help="Quit color representation")

parser.add_argument(
    '-d','--path',action= 'store', dest="path",default=None,
    help="Overwrite path to load the listing tree"
)

parser.add_argument(
    '-p',
    help="load the listing in the current directory",
    action="store_true",
    dest="_LoadInCurrentDirectory",
    default = False
)

parser.add_argument(
    '--filter',
    '-f',
    action='store',
    dest='filter',
    default="",
    help="Filter results."
)
"""

parser.add_argument(
    '-s',
    '--silent',
    action="store_true",
    dest = "is_silent",
    default = False,
    help = "Silent reconfiguration output (if any)."
)

parser.add_argument(
    "--nl", 
    type = int, 
    dest = "name_length", 
    default = 13,
    help = "modify the maximum name length, (modify paddings)."
)

parser.add_argument(
    '--dl', 
    type = int, 
    dest = "desc_length",
    default = 75,
    help = "modify the maximum description length, (modify paddings)."
)

parser.add_argument(
    '--tl', 
    type = int,
    dest = "type_length",
    default = 15,
    help = "modify the maximum type length, (modify paddings)"
)

parser.add_argument(
    '-r','--reconfig',
    '-c',
    type=str,
    action='store',
    default = False,
    help="Espcify what to update it's information",
    dest = "reconfig",
    nargs = '+'
)

parser.add_argument(
    '-u','--unique',
    action='store_true',
    dest="unique",
    help="When reconfiguration, just update the ones that there arent any information available"
)

parser.add_argument(
    '-i','--internals',
    action='store_true',
    dest='show_internals',
    help="When displaying and computing new exps, include internal machinery."
)

RECONFIG_HELP = """
Usage: list [-r|-c|--reconfig] \[help] [all [-i]] [rawlist [-i]] [displayunique [-i]] [EXP, [EXP...]]

[EXP, [EXP...]] list of all exp values to be updated.
\[all]           update info or all exps detected (use -s to reconfigure everything silently and -u for unique).
\[rawlist]       show the list of all detected exp.
\[displayunique] display all the exp that are not recorded by list.
"""

NAME_MAX_LENGTH = 13
DESCRIPTION_MAX_LENGTH = 75
TYPE_MAX_LENGTH = 15

class ListedExp(object):
    def __init__(self, name, frequency, description, type, color):
        self.name = name
        self.frequency = frequency
        self.description = description
        self.type = type
        self.color = color

class LCacheManager(object):
    def __init__(self, file):
        self.file = file
        self.exp  = {}
    
    def parse(self):
        for line in self.file.readlines():
            exp = json.loads(line)
            if not(exp.get('name')):
                continue
            self.exp[exp.get('name')] = ListedExp(
                exp.get('name'),
                exp.get('frequency','0/0'),
                exp.get('description','NONE'),
                exp.get('type','UNKNOWN'),
                exp.get('color', 'white')
            )
        return self

class LCacheWriter(object):
    def __init__(self, file):
        self.file = file

    def write(self, exp):
        line = json.dumps({
           'name':exp.name,
           'frequency':exp.frequency,
           'description':exp.description,
           'type':exp.type,
           'color':exp.color
        })
        self.file.write(line)
        self.file.write('\n')

def scan_for_exp(dir):
    res = []
    for i in os.listdir(dir):
        if not(i.split('.')[-1] == 'py'):
            continue
        if os.path.isdir(os.path.join(dir, i)):
            continue
        
        res.append('.'.join(i.split('.')[:-1]))

    return res

def prt(msg):
        if(opts.is_silent):
            return
        rich.print(msg)

def inp(msg):
    if(opts.is_silent):
        return "UNKNOWN"
    rich.print(msg, end = "")
    try:
        return input()
    except KeyboardInterrupt:
        print("^C")
        raise KeyboardInterrupt

def yes_no(msg):
    while(True):
        res = inp(f"{msg}[blue][Y/N][/blue]>>> ")
        res = list(res)
        while ' ' in res:res.remove(' ')
        res = ''.join(res)
        res = res.lower()
        if(res == 'unknown'):
            return "UNKNOWN"
        yes = ['y', '1', 'yes', 'si','sí']
        no = ['n', '0', 'no']
        if(res in yes):
            return 1
        elif(res in no):
            return 0
        prt("[red]ERROR;[/red] input not in yes or no parameters.")

def pre_init(dp,fp,opts):

    prt("[red]Welcome[/red] to the list initialization Wizard!")
    prt("[red]list[/red] is not correctly initialized for use")
    prt("Let's initialize it!\n")
    
    prt(f"We've located configuration at : \"[red]{fp}[/red]\"")

    prt(f"We are going to locate all installed [red]exp[/red] for you, but you'll need to tell us about them")
    
    listed = scan_for_exp(dp)
    
    prt(f"We found some!")

    writer = LCacheWriter(open(fp, 'w'))
    question_exps(listed, writer)

    return 0

def question_exps(listed, writer):
    for exp in listed:
        if exp.startswith('_') and not(opts.show_internals):
            continue
        prt(f"   · [red]{exp}[/red]")
        r = yes_no("      > Do you know this exp?")
        if(r == 'UNKNOWN' or not(r)):
            ep = ListedExp(exp, '0/0', 'NONE', 'UNKNOWN', 'white')
        else:
            description = inp("      > Can you give a one-line exp description (if not, leave blank): ") or 'NONE'
            type = inp("      > Can you give a type especification for the exp (if not, leave blank): ") or 'UNKNOWN'
            color = inp("      > Can you give this exp a especial color (if not, leave empty (=white)): ") or 'white'
            ep = ListedExp(exp,'0/0', description, type, color)
        
        writer.write(ep)
            
    writer.file.close()

def basic_print(dp):
    man = LCacheManager(open(dp, 'r'))

    man.parse()
    
    #rich.print("   [red]Name[/red]      [cyan]Description[/cyan]                                       [green]Type[/green]")
    
    return exc_print(man.exp)
    
def exc_print(exps):
    name_padding = (NAME_MAX_LENGTH - 4)//2
    
    description_padding = (DESCRIPTION_MAX_LENGTH - len("Description")) // 2
    
    type_padding = (TYPE_MAX_LENGTH - 4) // 2
    
    if name_padding > 1:
        rich.print(" "* name_padding + '[red]Name[/red]',end = "")
    else:
        rich.print(" " * NAME_MAX_LENGTH, end = "")
    if(description_padding > 1):
        rich.print(" "* description_padding + '[cyan]Description[/cyan]', end = "")
        rich.print(" "* (description_padding + 5),end = "")
    else:
        rich.print(" " * (name_padding + 4), end = "")
        rich.print(" " * (DESCRIPTION_MAX_LENGTH), end = "")
    
    if(type_padding > 1):
        rich.print(" " * type_padding + "[green]Type[/green]", end = "")
    else:
        rich.print(" " * (TYPE_MAX_LENGTH + description_padding), end = "")
    
    rich.print()
    
    rich.print("[red]" + "-" * NAME_MAX_LENGTH + '[/red]   [cyan]' + '-' * DESCRIPTION_MAX_LENGTH + '[/cyan]  [green]' + '-' * TYPE_MAX_LENGTH + '[/green]')

    _print_exps(exps)
    
def max_length(obj, ml):
        if(ml == 0):
            return ""
        plain = io.StringIO()
        style = Style(color = 'white', bgcolor = 'black')
        console = rich.console.Console(style = style, file = plain)
        console.print(obj, end = "")
        real_length = len(plain.getvalue())
        if real_length > ml:
            obj = plain.getvalue()[:ml - 3] + '...'
        return obj + ' ' * (ml - real_length)

def _print_exps(exps):
    for expn in exps.keys():
        exp = exps[expn]
        name = f'[{exp.color}]' + max_length(exp.name, NAME_MAX_LENGTH) + f'[/{exp.color}]'
        description = max_length(exp.description, DESCRIPTION_MAX_LENGTH)
        type = f'[{exp.color}]' + max_length(exp.type, TYPE_MAX_LENGTH) + f'[/{exp.color}]'
        if DESCRIPTION_MAX_LENGTH == 0:        
            rich.print(" " + name + " | " + type)
            continue
        rich.print(" " + name + " | " + description + " | " + type)

def display_unique(dr, opts, lscf):
    data = LCacheManager(open(
        lscf,
        'r'
    )).parse()
    all_exps = scan_for_exp(dr)    

    exps = data.exp
    data.file.close()

    expnames = list(exps.keys())
    
    for expn in all_exps:
        if expn.startswith('_') and not(opts.show_internals):
            continue
        if expn in expnames:
            expnames.remove(expn)
            continue
        exps[expn] = ListedExp(expn, '0/0', 'NORECORD','NORECORD','yellow')
    
    exc_print(exps)

        
def rawlist(dr, opts, lscf):
    listed = scan_for_exp(dr)
    for expn in listed:
        if expn.startswith('_') and not(opts.show_internals):
            continue

        rich.print(f'[red]{expn}[/red] at [green]\"{os.path.join(dr, expn + ".py")}\"[/green]')

    return 0

def update_config(dr, lscf, rcfg):
    exps = scan_for_exp(dr)

    man  = LCacheManager(open(lscf, 'r')).parse()
    
    _exps = {}
    
  
    for expname in rcfg:
        if not expname in exps:
            rich.print(f"[red]ERROR[/red]: {expname} is not a valid EXP")
        _exps[expname] = man.exp.get(
            expname, ListedExp(expname, '0/0', 'NORECORD','NORECORD','yellow')
        )
    
    
    rich.print(f"Original status:")
    exc_print(_exps)    

    rich.print("Updating config for:")

    writer = LCacheWriter(open(lscf, 'w'))

    for exp in man.exp:
        if not(exp in rcfg):
            writer.write(man.exp[exp])
    
    question_exps(rcfg, writer)
    
    return 0

        
def reconfig(dr, opts, lscf):
    rcfg = opts.reconfig
    cmd = rcfg[0].lower()
    if cmd == 'help':
        rich.print(RECONFIG_HELP)
        return 0
    
    if(cmd == 'displayunique'):
        return display_unique(dr, opts, lscf)
    
    if(cmd == 'all'):
        return pre_init(dr, lscf,opts)
    
    if(cmd == 'rawlist'):
        return rawlist(dr, opts, lscf)
    
    return update_config(dr, lscf, rcfg)
    

def main(dir,opts):
    global NAME_MAX_LENGTH, DESCRIPTION_MAX_LENGTH, TYPE_MAX_LENGTH
    listCacheFile = os.path.join(dir, 'data','lcache')
    
    if opts.name_length > 0:
        NAME_MAX_LENGTH        = max(opts.name_length,3)
    else:
        NAME_MAX_LENGTH        = 0
    if(opts.desc_length > 0):
        DESCRIPTION_MAX_LENGTH = max(opts.desc_length,3)
    else:
        DESCRIPTION_MAX_LENGTH = 0
    if(opts.type_length > 0):
        TYPE_MAX_LENGTH        = max(opts.type_length,3)
    else:
        TYPE_MAX_LENGTH        = 0
    
    
    if opts.reconfig:    
        return reconfig(dir, opts, listCacheFile)
    
    if not(os.path.exists(listCacheFile)):
        return pre_init(dir,listCacheFile,opts)

    basic_print(listCacheFile)

    return 0

if __name__ == '__main__':
    opts = parser.parse_args()
    ## raise NotImplementedError
    try:
        sys.exit(main(os.path.dirname(__file__),opts))
    except KeyboardInterrupt:
        sys.exit(0)