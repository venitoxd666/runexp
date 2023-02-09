import os
import stat
import sys
import rich
import ntsecuritycon
import win32security
import argparse
import time
from anytree.exporter.jsonexporter import JsonExporter
from anytree import Node, RenderTree
from anytree import ContRoundStyle
MAX = 23

HELP = """
Linux LS Cheap copy.
Usage: [red]ls[/red]
       [red]ls[/red] [yellow]-l[/yellow] [dark_orange3][PATH][/dark_orange3] [dark_orange3][--hidden][/dark_orange3]
       [red]ls[/red] [yellow]-p[/yellow] [green]PATH[/green]
       [red]ls[/red] [yellow]-l[/yellow] [yellow]-p[/yellow] [dark_orange3][PATH][/dark_orange3]
       [red]ls[/red] [yellow]-t[/yellow] [dark_orange3]PATH[/dark_orange3] [[yellow]-s[/yellow] [dark_orange3]SAVEPATH[/dark_orange3]] [[dark_orange3]--security[/dark_orange3]] 
             PATH:(H for current)
       
prints also stat info using -l

Version: 1.2.1

Changelog:
    1.0.0: Added basic behaviour
    1.1.0: Added -l and improved functionality and help
        1.1.1: Added lots of -l improvements.
    1.2.0: Added -p functionality. Added support for -l -p, check below
        1.2.1: Added the -t functionality.
        
BUG:
    · ls -l --hidden PATH will simply not work. and will be the same as ls -l --hidden

L Output Interpret:
    [red]H[/red]-----     Hidden    
    [red]V[/red]-----     Visible
    -[green]F[/green]----     File
    -[green]D[/green]----     Directory
    --[yellow]S[/yellow]---     System
    --[yellow]N[/yellow]---     Normal
    ---[cyan]E[/cyan]--     Encrypted
    ---[cyan]N[/cyan]--     Normal
    ----[green1]T[/green1]-     Temporal (FILE_ATTRIBUTE_TEMPORARY, not common)
    ----[green1]R[/green1]-     Resident
    -----[pink1]V[/pink1]     Virtual
    -----[pink1]N[/pink1]     Normal

Maximum Name Length to be ended with \"...\": {MAX}

[red]ls[/red] [dark_orange3]-l[/dark_orange3] [dark_orange3]-p[/dark_orange3] will be the same as 

[magenta1]for[/magenta1] [green]OBJ[/green] [magenta1]in[/magenta1] [cyan]listdir[/cyan]([green]PATH[/green]):
    [red]ls[/red] [dark_orange3]-p[/dark_orange3] [green]OBJ[/green]

""".format(MAX=MAX)

MAX = min(MAX, 24)
FILL_CHAR = ' '

W_FLDIR = ntsecuritycon.FILE_LIST_DIRECTORY    # =                        1
W_FADFL = ntsecuritycon.FILE_ADD_FILE          # =                       10
W_FADSD = ntsecuritycon.FILE_ADD_SUBDIRECTORY  # =                      100
W_FRDEA = ntsecuritycon.FILE_READ_EA           # =                     1000
W_FWREA = ntsecuritycon.FILE_WRITE_EA          # =                    10000
W_FTRAV = ntsecuritycon.FILE_TRAVERSE          # =                   100000
W_FDLCH = ntsecuritycon.FILE_DELETE_CHILD      # =                  1000000
W_FRDAT = ntsecuritycon.FILE_READ_ATTRIBUTES   # =                 10000000
W_FWRAT = ntsecuritycon.FILE_WRITE_ATTRIBUTES  # =                100000000
W_DELET = ntsecuritycon.DELETE                 # =        10000000000000000
W_RDCON = ntsecuritycon.READ_CONTROL           # =       100000000000000000
W_WRDAC = ntsecuritycon.WRITE_DAC              # =      1000000000000000000
W_WROWN = ntsecuritycon.WRITE_OWNER            # =     10000000000000000000
W_SYNCH = ntsecuritycon.SYNCHRONIZE            # =    100000000000000000000
W_FGNEX = ntsecuritycon.FILE_GENERIC_EXECUTE   # =    100100000000010100000
W_FGNRD = ntsecuritycon.FILE_GENERIC_READ      # =    100100000000010001001
W_FGNWR = ntsecuritycon.FILE_GENERIC_WRITE     # =    100100000000100010110
W_GENAL = ntsecuritycon.GENERIC_ALL            # =    10000000000000000000000000000
W_GENEX = ntsecuritycon.GENERIC_EXECUTE        # =    100000000000000000000000000000
W_GENWR = ntsecuritycon.GENERIC_WRITE          # =    1000000000000000000000000000000
W_GENRD = ntsecuritycon.GENERIC_READ           # =    -10000000000000000000000000000000
W_DIRRD = W_FLDIR | W_FRDEA | W_FRDAT | W_RDCON | W_SYNCH
W_DIRWR = W_FADFL | W_FADSD | W_FWREA | W_FDLCH | W_FWRAT | W_DELET | \
    W_RDCON | W_WRDAC | W_WROWN | W_SYNCH
W_DIREX = W_FTRAV | W_RDCON | W_SYNCH
W_FILRD = W_FGNRD
W_FILWR = W_FDLCH | W_DELET | W_WRDAC | W_WROWN | W_FGNWR
W_FILEX = W_FGNEX
WIN_RWX_PERMS = [
    [W_FILRD, W_FILWR, W_FILEX],
    [W_DIRRD, W_DIRWR, W_DIREX]
]
WIN_FILE_PERMISSIONS = (
    "DELETE", "READ_CONTROL", "WRITE_DAC", "WRITE_OWNER",
    "SYNCHRONIZE", "FILE_GENERIC_READ", "FILE_GENERIC_WRITE",
    "FILE_GENERIC_EXECUTE", "FILE_DELETE_CHILD")
WIN_DIR_PERMISSIONS = (
    "DELETE", "READ_CONTROL", "WRITE_DAC", "WRITE_OWNER",
    "SYNCHRONIZE", "FILE_ADD_SUBDIRECTORY", "FILE_ADD_FILE",
    "FILE_DELETE_CHILD", "FILE_LIST_DIRECTORY", "FILE_TRAVERSE",
    "FILE_READ_ATTRIBUTES", "FILE_WRITE_ATTRIBUTES", "FILE_READ_EA",
    "FILE_WRITE_EA")
WIN_DIR_INHERIT_PERMISSIONS = (
    "DELETE", "READ_CONTROL", "WRITE_DAC", "WRITE_OWNER",
    "SYNCHRONIZE", "GENERIC_READ", "GENERIC_WRITE", "GENERIC_EXECUTE",
    "GENERIC_ALL")
WIN_ACE_TYPES = (
    "ACCESS_ALLOWED_ACE_TYPE", "ACCESS_DENIED_ACE_TYPE",
    "SYSTEM_AUDIT_ACE_TYPE", "SYSTEM_ALARM_ACE_TYPE")
WIN_INHERITANCE_TYPES = (
    "OBJECT_INHERIT_ACE", "CONTAINER_INHERIT_ACE",
    "NO_PROPAGATE_INHERIT_ACE", "INHERIT_ONLY_ACE",
    "INHERITED_ACE", "SUCCESSFUL_ACCESS_ACE_FLAG",
    "FAILED_ACCESS_ACE_FLAG")
SECURITY_NT_AUTHORITY = ('SYSTEM', 'NT AUTHORITY', 5)

FILE = 0
DIRECTORY = 1

OBJECT_TYPES = [FILE, DIRECTORY]

OWNER = 0
GROUP = 1
OTHER = 2

OWNER_TYPES = [OWNER, GROUP, OTHER]

READ = 0
WRITE = 1
EXECUTE = 2

OPER_TYPES = [READ, WRITE, EXECUTE]

STAT_MODES = [
    [stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR],
    [stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP],
    [stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH]
]

STAT_KEYS = (
    "S_IRUSR",
    "S_IWUSR",
    "S_IXUSR",
    "S_IRGRP",
    "S_IWGRP",
    "S_IXGRP",
    "S_IROTH",
    "S_IWOTH",
    "S_IXOTH"
)

def _get_mode(mode,fa,argv,pathname,nocolor= False):
    def _color_(str, color):
        if nocolor:
            return str
        return f"[{color}]{str}[/{color}]"

    attrs = _color_('V', 'red')
    isf = False
    pathname = 'white'
    if(fa & stat.FILE_ATTRIBUTE_HIDDEN):
        if not('--hidden' in argv):
            return None
        else:
            attrs = _color_('H', 'red')
            pathname = 'dark_khaki'


    if(stat.S_ISDIR(mode)):
        attrs += _color_('D', 'green')
        #attrs += '[green]D[/green]'
        
        pathname = 'cadet_blue'
        isf = True
    else:
        attrs += _color_("F", 'green')

    if(fa & stat.FILE_ATTRIBUTE_SYSTEM):
        attrs += _color_("S", 'yellow')
    else:
        attrs += _color_("N", 'yellow')

    if(fa & stat.FILE_ATTRIBUTE_ENCRYPTED):
        attrs += _color_("E", 'cyan')
    else:
        attrs += _color_("N", 'cyan')

    if(fa & stat.FILE_ATTRIBUTE_TEMPORARY):
        attrs += _color_("T", 'green1')
    else:
        attrs += _color_("R", 'green1')

    if(fa & stat.FILE_ATTRIBUTE_VIRTUAL):
        attrs += _color_("V", 'pink1')
    else:
        attrs += _color_("N", "pink1")

    return attrs,pathname,isf

ORDERS = ['B','KB','MB','GB','TB','PB']

def format_space(bytes):
    unit = 0
    while(bytes > 1024 and unit < len(ORDERS) - 1):
        unit += 1
        bytes = bytes / 1024

    return f'%.2f{ORDERS[unit]}' % bytes

def l_call(argv):
    path = os.getcwd()
    if(not(os.path.isdir(path))):
        path = os.path.dirname(path)
    if(len(argv)):
        if not(argv[0].startswith('-')):
            path = argv[0]
    if not(os.path.exists(path)):
        path = os.path.join(os.getcwd(), path)
    # load information.
    objects = []
    for obj in os.listdir(path):
        pathname = os.path.join(path, obj)
        mode = os.lstat(pathname).st_mode
        pack= _get_mode(mode,os.lstat(pathname).st_file_attributes ,argv,obj)
        if(pack):
            mood,_obj,isf = pack
            objects.append([mood,obj,_obj,os.path.getsize(pathname), os.path.getatime(pathname), os.path.getctime(pathname),isf])
    if len(objects) == 0:
        rich.print("[red]Empty[/red]")
        return 0
    # represent the information
    rich.print(" attr               Name                 Last acces time         Last change time          Size ")
    rich.print("------    ------------------------ ------------------------   ------------------------   ---------")
    for obj in objects:
        rich.print(obj[0], end="")
        rich.print(' ' * 4, end="")

        objname = obj[1]
        if(len(objname) > MAX):
            objname = objname[:MAX - 3] + '...'
        rich.print(f'[{obj[2]}]{objname}[/{obj[2]}]',end="")
        
        written = min(len(obj[1]),MAX)
        
        rich.print(FILL_CHAR * (25 - written), end = "")        
        rich.print(time.ctime(obj[4]) + ' [blue]|[/blue] ',end = "")
        rich.print(time.ctime(obj[5]) + ' [blue]|[/blue] ',end = "")
        if not(obj[-1]):
            rich.print(format_space(obj[3]),end = "")
        else:
            rich.print("[blue]~[/blue]",end="")
        rich.print("") # to the new line

def get_owner(secd):
    """Get the object owner."""
    o = secd.GetSecurityDescriptorOwner()
    if(o):
        return win32security.LookupAccountSid(None, o)
    else:
        return ('SYSTEM_PROTECTED','UNKNOWN',-1)
    
def get_group(secd):
    o =  secd.GetSecurityDescriptorGroup()
    if(o):
        return win32security.LookupAccountSid(None,o)
    else:
        return ('SYSTEM_PROTECTED','UNKNOWN',-1)
    

def get_security(path):
    object_res = {"status":"success"}
    sec_des = win32security.GetNamedSecurityInfo(
        path, win32security.SE_FILE_OBJECT,
        win32security.DACL_SECURITY_INFORMATION)
    dacl = sec_des.GetSecurityDescriptorDacl()

    mode = os.stat(path).st_mode
    object_res["mode"] = mode    
    owner = get_owner(sec_des)
    object_res['owner'] = {}
    object_res['owner']['user'] = owner[0]
    object_res['owner']['computer'] = owner[1]
    object_res['owner']['code'] = owner[2]
    
    group = get_group(sec_des)
    object_res['group'] = {}
    object_res['group']['user']     = group[0]
    object_res['group']['computer'] = group[1]
    object_res['group']['code']     = group[2]

    sec_descriptor = win32security.GetFileSecurity(
        path, win32security.DACL_SECURITY_INFORMATION)
    dacl = sec_descriptor.GetSecurityDescriptorDacl()
    
    if not(dacl):
        object_res['status'] = "incomplete"
        return object_res

    aces = []

    for ace_no in range(0, dacl.GetAceCount()):
        ace_obj = {}
        ace = dacl.GetAce(ace_no)
        sid = win32security.LookupAccountSid(None, ace[2])

        ace_obj['sid'] = sid

        ace_type = ace[0][0]
        
        types = []
        for i in WIN_ACE_TYPES:
            if getattr(ntsecuritycon, i) == ace_type:
                types.append(i)

        ace_obj['types'] = {'typesname':types, 'typesint':list([getattr(ntsecuritycon, i) for i in types])}
        inherit = ace[0][1]
        
        if(inherit == win32security.NO_INHERITANCE):
            ace_obj['INHERITANCE']=None
        else:
            types = []
            for i in WIN_INHERITANCE_TYPES:
                if inherit & getattr(win32security, i) == getattr(win32security, i):
                    types.append({"name":i, "code":getattr(win32security, i)})
            ace_obj['INHERITANCE']={'types':types}
        
        win_perm = ace[1]
        flags = inherit
        perm = WIN_FILE_PERMISSIONS
        if not(os.path.isfile(path)):
            perm = WIN_DIR_PERMISSIONS
            if flags & ntsecuritycon.OBJECT_INHERIT_ACE == \
                    ntsecuritycon.OBJECT_INHERIT_ACE and flags & \
                    ntsecuritycon.INHERIT_ONLY_ACE == \
                    ntsecuritycon.INHERIT_ONLY_ACE:
                perm = WIN_DIR_INHERIT_PERMISSIONS
        calc_mask = 0
        ace_obj['permissions']  = []
        for i in perm:
            if getattr(ntsecuritycon, i) & win_perm == getattr(
                    ntsecuritycon, i):
                calc_mask = calc_mask | getattr(ntsecuritycon, i)
                ace_obj['permissions'].append({'type':i, 'code':getattr(ntsecuritycon, i)})
        
        ace_obj['calc_mask'] = calc_mask
        
        aces.append(ace_obj)
        
        
    object_res['ace'] = aces

    return object_res

def p_call(argv):
    current = 0
    path = ""
    while (not(os.path.exists(path))):
        try:
            path = argv[current]
        except IndexError:
            rich.print("[red]ERROR[/red]: File/path not found or invalid.")
            return 1    
        current += 1

    if os.path.isfile(path):
        rich.print(f"[blue]FILE[/blue]:\"{path}\"")
    else:
        rich.print(f"[blue]DIRECTORY[/blue]:\"{path}\"")

    rich.print("")
    sec_des = win32security.GetNamedSecurityInfo(
        path, win32security.SE_FILE_OBJECT,
        win32security.DACL_SECURITY_INFORMATION)

    mode = os.stat(path).st_mode

    owner = get_owner(sec_des)
    rich.print("[green]Owner[/green]:")
    rich.print(f"    · [green]User[/green]: [red]{owner[0]}[/red]")
    rich.print(f"    · [green]Computer[/green]: [red]{owner[1]}[/red]")
    rich.print(f"    · [green]Code[/green]: [red]{owner[2]}[/red]")

    rich.print("")
    
    group = get_group(sec_des)
    rich.print(f"[green]Group[/green]:")
    rich.print(f"    · [green]User[/green]: [red]{group[0]}[/red]")
    rich.print(f"    · [green]Computer[/green]: [red]{group[1]}[/red]")
    rich.print(f"    · [green]Code[/green]: [red]{group[2]}[/red]")

    rich.print("")


    rich.print("Mode:[cyan] " + oct(mode) + " [/cyan](Decimal: " + str(mode) + ")")
    for i in STAT_KEYS:
        if mode & getattr(stat, i) == getattr(stat, i):
            rich.print("  stat:[[red]" + i + '[/red]]')

    sec_descriptor = win32security.GetFileSecurity(
        path, win32security.DACL_SECURITY_INFORMATION)
    dacl = sec_descriptor.GetSecurityDescriptorDacl()
    if dacl is None:
        rich.print("[red]ERROR[/red]:No Discretionary ACL")
        return 1

    for ace_no in range(0, dacl.GetAceCount()):
        ace = dacl.GetAce(ace_no)
        rich.print(f"ACE({ace_no})=\"{repr(ace)}\"")
        rich.print(f"  · SID({ace_no}):")
        sid = win32security.LookupAccountSid(None, ace[2])
        rich.print(f"      · USER([red]{sid[0]}[/red]);")
        rich.print(f"      · GEN([red]{sid[1]}[/red]);")
        rich.print(f"      · INT([red]{sid[2]}[/red]);")
        ace_type = ace[0][0]
        types = []
        for i in WIN_ACE_TYPES:
            if getattr(ntsecuritycon, i) == ace_type:
                types.append(i)
        rich.print(f"   · TYPES([red]{'[/red],[red]'.join(types)}[/red])")
        ace_inherits = ace[0][1]
        rich.print(f"   · INHERITS([orange]flag[/orange]=[cyan]{hex(ace_inherits)}[/cyan]):")
        if ace_inherits == win32security.NO_INHERITANCE:
            rich.print(f"       · [red]NONE[/red]")
        else:
            for i in WIN_INHERITANCE_TYPES:
                if ace_inherits & getattr(win32security, i) == getattr(win32security, i):
                    rich.print("        · [red]"+ i.upper() + '[/red]')
        win_perm = ace[1]
        rich.print(f"   · PERMISSIONS([red]{hex(win_perm)}[/red]):")
        flags = ace_inherits
        perm = WIN_FILE_PERMISSIONS
        if not(os.path.isfile(path)):
            perm = WIN_DIR_PERMISSIONS
            if flags & ntsecuritycon.OBJECT_INHERIT_ACE == \
                    ntsecuritycon.OBJECT_INHERIT_ACE and flags & \
                    ntsecuritycon.INHERIT_ONLY_ACE == \
                    ntsecuritycon.INHERIT_ONLY_ACE:
                perm = WIN_DIR_INHERIT_PERMISSIONS
        calc_mask = 0  # see if we are printing all of the permissions
        for i in perm:
            if getattr(ntsecuritycon, i) & win_perm == getattr(
                    ntsecuritycon, i):
                calc_mask = calc_mask | getattr(ntsecuritycon, i)
                rich.print(f"       · [red]{i}[/red]")
        
        rich.print(f"   · CALC_PERMISSIONS([red]{hex(calc_mask)}[/red]);")

T_Parser = argparse.ArgumentParser(prog = "ls -t", description = "T call.", add_help = False)

T_Parser.add_argument('-d', '--depth', type = int, dest = "depth",default=100)
T_Parser.add_argument('path', type=str, nargs = "+", help="H to use local path")
T_Parser.add_argument("-s", '--save', type=str, dest = "savepath", default=None)

T_Parser.add_argument("--fpickle", action="store_true", dest = "format_pickle", default=False)

T_Parser.add_argument('--hidden', action="store_true", dest = "hidden")

T_Parser.add_argument('--security', action="store_true", dest = "show_also_security", default = False)

def _save_t_call(data, opts):

    exp = JsonExporter()
    
    
    exp.write(
        data, 
        open(opts.savepath, 'w')
    )

    return 0

class _FileInfoNode(Node):
    def __init__(self,name, parent = None, mode = "", st_mode = "", size = None,children = [], status = "SUCCESS",fullpath = "",security = {}):
        self.name = name
        self.parent = parent

        self.mode = mode
        self.st_mode = st_mode
        self.size = size
        self.status = status
        self.fullpath = fullpath
        self.security = security


        if children:
            self.children = children

    def __repr__(self):
        if(self.status != "SUCCESS"):
            return f"{self.__class__.__name__}(status={self.status}, path = {self.fullpath})"
        return f"{self.__class__.__name__}(\"{self.name}\", {'size = {SIZE},'.format(SIZE= format_space(self.size)) if self.size!=None else ''} mode = \"{self.mode}\", status = {self.status}, security_status = {self.security.get('status', 'UNKNOWN')}{', owner={owner}'.format(owner=self.security['owner']['user']) if self.security['status'] == 'success' else ''})"

class Folder(_FileInfoNode):pass
class File(_FileInfoNode):pass

def _p_data_recolection(node, path, opts):
    if(opts.depth == 0):
        return None
    try:
        for obj in os.listdir(path):
            pathname = os.path.join(path, obj)
            mode = os.stat(pathname).st_mode
            pack = _get_mode(mode, os.lstat(pathname).st_file_attributes,['--hidden' if opts.hidden else ""],obj,nocolor=True)    
            if(pack):
                a = pack[0]
            else:
                a = "HIDDEN"
            security = {"status":"NORECORD"}
            if (opts.show_also_security):
                security = get_security(pathname)
            if(os.path.isfile(pathname)):
                File(obj, parent = node,mode = a, st_mode = mode,size = os.path.getsize(pathname),fullpath=pathname,security=security)
            else:
                parent = Folder(obj, parent  = node, mode = a,st_mode = mode, fullpath = pathname,security=security)
                opts.depth = opts.depth - 1
                _p_data_recolection(parent, pathname, opts)
                opts.depth = opts.depth + 1
    except PermissionError as e:
        File("UNKNOWN", parent = node, mode = "UNKNOWN", st_mode = 0,  size = 0, status="PERMISSION_DENIED", fullpath=path)

def t_call(argv):
    opts = T_Parser.parse_args(argv)
    if opts.path[0] == 'H':
        opts.path = [os.getcwd()]
    opts.path = ' '.join(opts.path)
    if not(os.path.exists(opts.path)) or os.path.isfile(opts.path):
        rich.print(f"[red]ERROR[/red]: given path (\"[red]{opts.path}[/red]\") does not exists or is a file")
        return 1
    
    # data recolection
    parent = Folder("root",security={'status':"NORECORD"})
    start_time = time.time()
    
    _p_data_recolection(parent, opts.path, opts)
    end_time = time.time()
    time_took = end_time - start_time
    if (time_took > 5):
        print("Finished Recollecting Data")

    if(opts.savepath):
        _save_t_call(parent, opts)
        return 0
    if(time_took < 5):
        rich.print(RenderTree(parent,style=ContRoundStyle()))
    else:
        print(RenderTree(parent,style = ContRoundStyle()))

    return 0

def main(argv):
    try:
        if(len(argv) == 1):
            return os.system('dir')
        
        if('-h' in argv):
            rich.print(HELP)
            return 0

        if('-l' in argv):
            if ('-p' in argv):
                argv.remove('-p')
                argv.remove('-l')
                argv = argv[1:] if len(argv) else []
                path = os.getcwd()
                if(not(os.path.isdir(path))):
                    path = os.path.dirname(path)
                if(len(argv)):
                    if not(argv[0].startswith('-')):
                        path = argv[0]
                if not(os.path.exists(path)):
                    path = os.path.join(os.getcwd(), path)
                
                for obj in os.listdir(path):
                    if(p_call([obj])):
                        return 1
                
                return 0               
            argv.remove('-l')
            argv = argv[1:] if len(argv) else []
            return l_call(argv)

        if( '-t' in argv):
            argv.remove('-t')
            argv = argv[1:] if len(argv) else []
            return t_call(argv)


        if('-p' in argv):
            argv.remove('-p')
            argv = argv[1:] if len(argv) else []
            return p_call(argv)

    except KeyboardInterrupt:
        return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
