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
        if hasattr(r, "read") and callable(r.read):
            self._reader = r
        elif callable(r):
            self._reader = RWBuilder(rFunc=r)
        else:
            raise TypeError("unknown type for reader")
    
    @writer.setter
    def writer(self, w):
        if hasattr(w, "write") and callable(w.write):
            self._writer = w
        elif callable(w):
            self._writer = RWBuilder(wFunc=w)
        else:
            raise TypeError("unknown type for writer")

