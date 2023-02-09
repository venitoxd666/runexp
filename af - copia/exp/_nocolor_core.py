import sys
import runpy
import rich
from maskpass import askpass


class _TextStyleRemover(object):
    def __init__(self, text):
        self.text = text
        self._current_index = 0
        self.new_string = ""

    @property
    def current(self):
        if(self._current_index >= len(self.text)):
            return ""
        return self.text[self._current_index]

    def read_color_tag(self):
        if self.current != '[':
            return ""

        self.index(1)
        res = ''
        
        while(self.current != ']'):
            res += self.current
            self.index(1)
        
        return res

    def _erase_tag(self, ):
        if self.current != '[':
            return

        color_tag = self.read_color_tag()
        self.index(1)


    def index(self, index):
        #print(f"Current:", repr(self.current))
        self._current_index += index
        #print(f"CurrentAfter:", repr(self.current))
        return self.current

    def remove(self):
        while(self.current):
            if(self.current=='['):
                self._erase_tag() # if char != '[', function exit without doing anything
                continue
            if(self.current == '\\'):
                self.index(1)
                if(self.current == '['):
                    self.new_string += '['
                    self.index(1)
                    continue
                continue
            self.new_string += self.current

            self.index(1) # advance

        return self.new_string

def _print(*values,sep=' ', end = "\n",file = sys.stdout,flush = False):
    if(values[0] == "\\//67"):
        return 1
    text = sep.join([str(value) for value in values])
    stripper = _TextStyleRemover(text)
    new = stripper.remove()
    print(new, end = end, file = file,flush = flush)
    
    # print(new, end = end)
    
backup = sys.modules['rich'].print

sys.modules['rich'].print = _print

sys.argv = sys.argv[1:]

if(sys.argv[0].startswith('-')):
    print(f"ERROR(1): Cannot interpret {sys.argv[0]} as a valid exp")
    sys.exit(1)

runpy.run_module(
    sys.argv[0],alter_sys=False,run_name='__main__'
)
