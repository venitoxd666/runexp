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
import heapq

ap = argparse.ArgumentParser(
    prog = "encrypt"
)

ap.add_argument('-f', '--file', dest = 'file',default = None,help="file/s to encrypt", nargs = '+')
ap.add_argument('-o', '--output', dest = 'output', default = None, help="destination of the encryption. Default: File|Directory to be encrypted.", nargs = '+')
ap.add_argument('-d', '--directory', dest = "directory", help = "directory/s to encrypt", nargs = '+')
ap.add_argument('-m', '--method', dest = 'method', help = "method to encrypt.")
ap.add_argument('-u', "--undo", dest = "dercrypt", action = "store_true", help = "especify wether is encrpyt or decrypt")
ap.add_argument('-p', '--password', dest = "password", help = "password to decrypt or encrypt. \"GEN()\" to generate and print it.")

ap.add_argument('--password_mask', dest='mask', help="Change the password input mask", default = "*")


HELP = """
Version: 1.0.0

Changelog:
    1.0.0: -initial behaviour implemented

encrpyt [purple]encrypts[/purple] a file many ways.
(to encrypt a directory use "-d" (check))


Valid values for "-m" | "--method" are:
    -m [red]ntm[/red]
        Not encryption, simple, not really encrypting anything, just changing the format and the most basic encryption method
    -m [red]ntg[/red]
        Symmetric encryption, integer password between 0 and 255.
        
ntm: size complexity: S(n) -> O(n)
ntg: size complexity: S(n) -> O(2*7 + 2*n)

"""

def print_help():
    argparse.ArgumentParser.print_help(ap)
    rich.print(HELP)

ap.print_help = print_help

def _INT_NOT(i, numbits=8):
    return (1 << numbits) - 1 - i

class Diagram(object):
    def __init__(self, value,):
        self.value = value
        self.children = []
        self.parent = None

class Huffman(object):
    def __init__(self, buffer):
        self.buffer = buffer
    
    def compute(self):
        pass
    
    def decrypt(self):
        pass


def req_ps(method):
    method.requires_password = True
    return method

class Encrypter(object):
    def __init__(self, opts):
        self.opts = opts
        self._check_args()
        
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
            res.write(int.to_bytes(_INT_NOT(char[0]), 1, 'big'))
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
    
    def huffman(self, read_buffer):
        huffman = Huffman(read_buffer)
        return huffman.compute()

    # decryption methods
    def ntm_decrypt(self, read_buffer):
        return self.ntm(read_buffer)

    def need_password(self, prompt = "Enter password:"):
        if not(self.opts.password):
            self.opts.password = askpass(prompt,mask=self.opts.mask)           
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

    def huffman_decrypt(self, read_buffer):
        return Huffman(read_buffer).decrypt()

    # keep working functionality
    def encrypt(self, method, file, output,stop):
        file = open(file, 'rb')
        try:
            if(stop()):
                return
            output_buffer = method(file)
        except Exception as e:
            self.error(f"Invalid method: {method}",1)
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
                    text = f'[{char}] - {file} >> {output} '
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
