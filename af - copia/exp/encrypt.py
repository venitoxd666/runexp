# import win32con
# import win32api
import os
import sys
import io, time
# import win32crypt
# import win32file
import threading
import argparse
import rich
import random
from maskpass import askpass
from collections import OrderedDict

ap = argparse.ArgumentParser(
    prog = "encrypt"
)

ap.add_argument('-f', '--file', dest = 'file',default = None,help="file/s to encrypt", nargs = '+')
ap.add_argument('-o', '--output', dest = 'output', default = None, help="destination of the encryption. Default: File|Directory to be encrypted.", nargs = '+')
ap.add_argument('-d', '--directory', dest = "directory", help = "directory/s to encrypt", nargs = '+')
ap.add_argument('-m', '--method', dest = 'method', help = "method to encrypt.")
ap.add_argument('-u', "--undo", dest = "dercrypt", action = "store_true", help = "especify wether is encrpyt or decrypt")
ap.add_argument('-p', '--password', dest = "password", help = "password to decrypt or encrypt. \"GEN()\" to generate and print it.")

ap.add_argument('-t', '--repeat', dest='times', help="Number of times to repeat the encryption", type=int, default = 1)


ap.add_argument('--password_mask', dest='mask', help="Change the password input mask", default = "*")

HELP = """
Version: 1.1.0

Changelog:
    1.0.0: -initial behaviour implemented
        1.1.0: Added encryption methods: ntm, ntg, huffman
               Better representation and user interface

encrpyt [purple]encrypts[/purple] a file many ways.
(to encrypt a directory use "-d" (check))


Valid values for "-m" | "--method" are:
    -m [red]ntm[/red]
        Not encryption, simple, not really encrypting anything, just changing the format and the most basic encryption method
    -m [red]ntg[/red]
        Symmetric encryption, integer password between 0 and 255.
    -m [red]huffman[/red]
        multi-state machine encryption, the message depends on the password, as bigger
        the message, as harder to crack the password. And so as bigger the password.
    
ntm: size complexity:     S(n) -> O(n)
ntg: size complexity:     S(n) -> O(2*7 + 2*n)
huffman: size complexity: S(n) -> ~
"""

def print_help():
    argparse.ArgumentParser.print_help(ap)
    rich.print(HELP)

ap.print_help = print_help

encrypter = None

def get_encrypter():
    return encrypter

def to_bytes(i):
    if i is None:
        return b""
    if isinstance(i, bytes):
        return i

    return i.to_bytes((i.bit_length() // 8) + (1 if i.bit_length() % 8 else 0), 'big')

def set_encrypter(enc):
    global encrypter
    encrypter=enc
    return encrypter

def _INT_NOT(i, numbits=8):
    return (1 << numbits) - 1 - i

class Diagram(object):
    def __init__(self, token, parent=None):
        self.token = token
        self.children = {}
        self.parent = parent
    
    def add_state(self, state, token):
        if(token == self.token):
            self.children[state] = self
            return self
        if(state in self.children):
            return self.children[state]
        
        self.children[state] = Diagram(token, parent=self)
        return self.children[state]

    def __repr__(self):
        return f"Diagram<{self.token} states:{list(self.children.keys())}>"

class Huffman(object):
    def __init__(self, encrypter:"Encrypter", buffer):
        self.buffer = buffer
        self.encrypter = encrypter
        self.psswd = self.process_password(self.encrypter.need_password())
        if(len(self.psswd) < 10):
            self.encrypter.error("Password too short, massive data loss if password too short. Recomended to write something big", 1)
        self._encrypt = True
        
    def process_password(self, password:str, recv=10,og_recv=10):
        vector = list(password)
        res = b""
        last = None
        last_count = 0
        
        for obj in vector:
            if isinstance(obj, str):
                obj = ord(obj)
            if(obj == last):
                last_count += 1
                continue
            else:
                if(last_count >= 1):
                    res += to_bytes(last_count)
                res += to_bytes(last)
                last = obj
                last_count = 0
        if(last_count > 1):
            res += to_bytes(last_count)
        res += to_bytes(last)
        last = obj
        _res = res
        _res += _res[:4] # a little of extra space in the password wich makes it harder to crack
                         # the encoding
        addup = sum(_res)
        _res += int.to_bytes(addup, 
                             (addup.bit_length() // 8 + 1),
                             'big'
                            )
        _res += int.to_bytes(addup, 
                             (addup.bit_length() // 8 + 1),
                             'little'
                            )

        _res += b'\xff'
        if(sum(_res) % 2 == 0 and (recv > 0)):
            _res = self.process_password(_res, recv = recv - 1,og_recv=og_recv)
        elif (recv > 0):
            _res = self.process_password(_res + _res[1::2] + b'\x01', recv = recv - 2,og_recv=og_recv)

        return _res
        
    def get_diagram(self):
        # works, DO NOT DARE TO TOUCH THIS SHIT
        # or ELSE IT CAN DESTROY EVERYTHING THAT HAS TO DO WITH HUFFMAN
        char = self.buffer.read(1)
        root = last = Diagram(char)
        count = -1
        mapping = {char:root}
        while(char):
            # char advance
            char = self.buffer.read(1)
            if not(char):
                continue

            # state / password advance
            count += 1
            if(count == len(self.psswd)):
                count = 0   
            identifier = to_bytes(self.psswd[count])
            # mapping
            if(char in mapping):
                # already mapped, just add a state to it
                if last.children.get(identifier, None) is not None:
                    identifier += b"\x01"
                last.children[identifier] = mapping[char]
                last = mapping[char]
            else:
                last = last.add_state(identifier, char)
                mapping[char] = last
        return root

    def flatten(self, root, saved:list):
        if(root in saved):
            return
        res = OrderedDict()
        res[root.token] = root
        
        saved.append(root)
        
        for obj in root.children.values():
            _upd = self.flatten(obj, saved)
            if not(_upd):
                continue 
            res.update(_upd)
        
        return res

    def a_getvalue(self):
        res = io.BytesIO()
        current = self.get_diagram()
        if not(current):
            return res.getvalue()
        
        saved = list()
        flat = self.flatten(current, saved)

        for obj in flat:
            bj,refs = flat[obj],flat[obj].children
            res.write(
                int.to_bytes(
                    len(refs),
                    1,
                    'big'
                )
            )
            for state, obj in refs.items():
                res.write(
                    int.to_bytes(
                        state,
                        1,
                        'big'
                    )
                )
                res.write(
                    int.to_bytes(
                        saved.index(obj),
                        1,
                        'big'
                    )
                )
            res.write(bj.token)

        res.seek(0)
        return res.getvalue()


    def b_getvalue(self):
        def _ensure_read(index):
            char = self.buffer.read(index)
            if not(char):
                self.encrypter.error(
                    "File format corrupt for huffman encryption", 1)
            return char

        def read_chunk():
            number_of_refs = _ensure_read(1)[0]
            refs = {}
            for i in range(number_of_refs):
                case = _ensure_read(1)
                index = _ensure_read(1)[0]
                refs[case] = index
            return {
                "refs":refs,
                "token":_ensure_read(1)
            }
        
        def _lazy_char():
            backup = self.buffer.tell()
            res = self.buffer.read(1)
            self.buffer.seek(backup)
            return res

        chunks = []
        while(_lazy_char()):
            chunks.append(read_chunk())
        
        current_chunk_index = 0
        count = -1
        res = io.BytesIO()

        while(True):
            count += 1
            if(count == len(self.psswd)):
                count = 0
            
            current = chunks[current_chunk_index]

            case = int.to_bytes(self.psswd[count],1,'big')

            refs = current['refs']
            
            res.write(current['token'])
            
            if not len(refs):
                break

            if not(case in refs):
                break
            current_chunk_index = refs[case]
            
        return res.getvalue()

    def c_getvalue(self):
        if(self._encrypt):
            return self.a_getvalue()
        return self.b_getvalue()

    def compute(self):
        self._encrypt=True
        v = self.c_getvalue()
        self.getvalue = lambda *a,**k:v
        return self

    def decrypt(self):
        self._encrypt=False
        v = self.c_getvalue()
        self.getvalue = lambda *a,**k:v
        return self

def req_ps(method):
    method.requires_password = True
    return method

class Encrypter(object):
    def __init__(self, opts):
        self.opts = opts
        self._check_args()
        set_encrypter(self)
        
    def _check_args(self):
        if not(self.opts.file) and not(self.opts.directory):
            self.error("Please specify either a file or a directory", 0x1)
        
        self.directory = self.opts.directory
        self.file = self.opts.file
        if not(self.file):
            self.file = []
            if not(self.directory):
                raise ValueError("Expected or file (\"-f FILE\") or directory (\"-d DIRECTORY\")")
            for dir in self.directory:
                for root, _, files in os.walk(dir):
                    for file in files:
                        self.file.append(os.path.join(root, file))
        self.directory = self.opts.directory
        
        if not(self.opts.method):
            self.error("Please specify a method to encrypt", 0x1)
        
        self.method = self.opts.method 
        self.output = self.opts.output or []
    
    
    # encryption methods    
    def ntm(self, read_buffer):
        res = io.BytesIO()
        char = read_buffer.read(1)
        while(char):
            """
            char*chr;
            while(1){
                if (fileRead(readFileBuffer, chr)) { // eof
                    break;
                }
                fileWrite(outFileBuffer,(char*)(~(*chr)));
            }
            
            """
            res.write(int.to_bytes(_INT_NOT(
                char[0]),
                1,
                'big'
            ))
            char = read_buffer.read(1)
        return res
    
    @req_ps
    def ntg(self, read_buffer):
        res = io.BytesIO()
        char = read_buffer.read(1)
        password = self.opts.password
        if not(password):
            password = random.randint(0, 255)
            rich.print(f"Generated password is : {password}")
        if(self.opts.password):
            if not(self.opts.password.isdigit()):
                self.error("Password for ntg must be a integer positive number", 0x1)
            password = int(self.opts.password)
            if(password < 0 or password > 0xff):
                self.error(f"Password for ntg must be between 0 and 255, got {password}", 0x1)
        
        for _ch in b"UNKNOWN":
            res.write(int.to_bytes(_ch + password, 2, 'big'))
        
        while(char):
            res.write(
                int.to_bytes(char[0] + password, 2, 'big')                
            )    
            char = read_buffer.read(1)

        return res
    
    @req_ps
    def huffman(self, read_buffer):
        huffman = Huffman(self,read_buffer)
        return huffman.compute()

    # decryption methods
    def ntm_decrypt(self, read_buffer):
        return self.ntm(read_buffer)

    def need_password(self, prompt = "Enter password:"):
        if not(self.opts.password):
            try:
                self.opts.password = askpass(prompt,mask=self.opts.mask)
            except KeyboardInterrupt:
                self.error("KeyboardInterrupt", -255)
        return self.opts.password

    @req_ps
    def ntg_decrypt(self, read_buffer):
        if not(self.opts.password.isdigit()):
            self.error("Password for ntg must be a integer positive number", 0x1)
        password = int(self.opts.password)
        if(password < 0 or password > 0xff):
            self.error(f"Password for ntg must be between 0 and 255, got {password}", 0x1)

        header_length = len("UNKNOWN")

        def I(c):
            decoded = int.from_bytes(c, 'big') - password
            if(decoded > 255 or decoded < 0):
                self.error("Incorrect password.",0x1)
            return decoded
        
        header = b'UNKNOWN'
        for i in range(header_length):
            if (header[i] != I(read_buffer.read(2))):
                self.error("Incorrect password.",0x1)
        
        res = io.BytesIO()
        
        char = read_buffer.read(2)
        while(char):
            res.write(int.to_bytes(I(char),1, 'big'))
            
            char  = read_buffer.read(2)

        return res

    @req_ps
    def huffman_decrypt(self, read_buffer):
        return Huffman(self,read_buffer).decrypt()

    # keep working functionality
    def encrypt(self, method, fl, output,stop):
        for i in range(self.opts.times):
            file = open(fl, 'rb')
            try:
                if(stop()):
                    return
                output_buffer = method(file)
            except Exception as e:
                self.error(f"Invalid method: {method} (errmsg:{str(e)})", 1)
            file.close()
            if(stop()):
                return

            with open(output, 'wb') as file:
                if(stop()):
                    return
                file.write(output_buffer.getvalue())
        
    def error(self, msg, errno):
       rich.print(f"[red]ERROR({errno})[/red]: {msg}") 
       sys.exit(errno)

    def _output_stream(self):
        for output in self.output:
            yield output
        while(1):
            yield None

    def run(self):
        if(self.opts.dercrypt):
            self.method = self.method + '_decrypt'

        if not(hasattr(self, self.method)):
            self.error(f"Invalid method: {self.method}",1)

        method = getattr(self, self.method)

        if(getattr(method,'requires_password',False)):
            self.need_password()

        chars = '|/-\\'
        stop_thread = 0
        kill_thread = lambda : stop_thread
        for file, output in zip(self.file, self._output_stream()):
            output = output or file
            thread = threading.Thread(target=self.encrypt, args=(method, file,output, kill_thread))
            thread.daemon = True
            state = 0
            thread.start()
            text = ""
            sys.stdout.write("\n")
            while(thread.is_alive()):
                try:
                    char = chars[state % len(chars)]
                    text = f'[{char}] - {file} >> {output}\n'
                    sys.stdout.write("\033[F" + text)
                    sys.stdout.flush()
                    time.sleep(0.2)
                    state += 1
                except KeyboardInterrupt:
                    sys.stdout.write("\n")
                    return sys.exit(1)
        
        sys.stdout.write("\n")

if __name__ == "__main__":
    opts = ap.parse_args()
    Encrypter(opts).run()
