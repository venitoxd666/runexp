# import win32con
# import win32api
import os
import sys
import io
# import win32crypt
# import win32file
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

class BTree(object):
    def __init__(self, vl, f):
        self.value = vl
        self.freq = f
        self.left = self.right = None

class Huffman(object):
    def __init__(self, buffer):
        self.buffer = buffer
        self.heap = []

    def __lt__(self, other):
        return self.frequency < other.frequency

    def __eq__(self, other):
        return self.frequency == other.frequency

    def _compute_freqs(self):
        freq = {}
        char = self.buffer.read(1)
        while(char):
            if not(char in freq):
                freq[char] = 0
            freq[char] += 1
            char = self.buffer.read(1)

        return freq

    def build_heap(self, f):
        for key in f:
            cf = f[key]
            byntree_node = BTree(key, cf)
            heapq.heappush(self.heap, byntree_node)

    def compute(self):
        self.buffer.seek(0)
        frqd = self._compute_freqs()
        self.heap = self.build_heap(frqd)

    def decrypt(self):
        pass

class Encrypter(object):
    def __init__(self, opts):
        self.opts = opts
        self._check_args()
        
    def _check_args(self):
        if not(self.opts.file) and not(self.opts.directory):
            self.error("Please specify either a file or a directory", 0x1)
        
        self.directory = self.opts.directory
        self.file = self.opts.file
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
    
    def ntg(self, read_buffer):
        res = io.BytesIO()
        char = read_buffer.read(1)
        password = self.opts.password
        if not(password):
            password = self.need_password("Enter password (Enter to random):")        
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

    def ntg_decrypt(self, read_buffer):
        self.opts.password = self.need_password()
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
    def encrypt(self, method, file, output):
        file = open(file, 'rb')
        if not(hasattr(self, method)):
            self.error(f"Invalid method: {method}",1)
        method = getattr(self, method)
        try:
            output_buffer = method(file)
        except Exception as e:
            print(e)
            self.error(f"Invalid method: {method}",1)
        file.close()
        with open(output, 'wb') as file:
            file.write(output_buffer.getvalue())
        
    def error(self, msg, errno):
       rich.print(f"[red]ERROR({errno})[/red]: {msg}") 
       sys.exit(errno)

    def _output_stream(self):
        for output in self.output:
            yield output
        while(1):
            yield None

    def decrypt(self, method, file, output):
        file = open(file, 'rb')
        method = method + '_decrypt'
        if not(hasattr(self, method)):
            self.error(f"Invalid method: {method}",1,'big')
        method = getattr(self, method)
        output_buffer = method(file)
        file.close()
        with open(output, 'wb') as file:
            file.write(output_buffer.getvalue())

    def decrypt_run(self):
        for file, output in zip(self.file, self._output_stream()):
            output = output or file

            self.decrypt(self.method, file, output)

    def run(self):
        if(self.opts.dercrypt):
            return self.decrypt_run()
        
        for file, output in zip(self.file, self._output_stream()):
            output = output or file

            self.encrypt(self.method, file, output)

if __name__ == "__main__":
    opts = ap.parse_args()
    Encrypter(opts).run()
    