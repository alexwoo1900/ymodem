import types

class RWBuilder(object):
    def __init__(self, rFunc=None, wFunc=None):
        self.read = rFunc
        self.write = wFunc
    
class Protocol(object):

    @property
    def reader(self):
        return self._reader

    @property
    def writer(self):
        return self._writer

    @reader.setter
    def reader(self, r):
        if hasattr(r, "read") and isinstance(r.read, types.FunctionType):
            self._reader = r
        elif isinstance(r, types.FunctionType):
            self._reader = RWBuilder(rFunc=r)
        else:
            raise TypeError("unknown type for reader")
    
    @writer.setter
    def writer(self, w):
        if hasattr(w, "write") and isinstance(w.write, types.FunctionType):
            self._writer = w
        elif isinstance(w, types.FunctionType):
            self._writer = RWBuilder(wFunc=w)
        else:
            raise TypeError("unknown type for writer")

