import pickle
import codecs
from src.FLM.utils.config import PICKLE_PROTOCOL, CODEC
class TCP_Package(object):
    def __init__(self, command=None, data=None, NP_shape=None, NP_dtype = None):
        self.cmd = command
        self.data = data
        self.NP_shape = NP_shape
        self.NP_dtype = NP_dtype

    def encode(self,codec=CODEC, protocol=PICKLE_PROTOCOL):
        return codecs.encode(self._pickle(protocol),encoding=codec)

    def _pickle(self,protocol=PICKLE_PROTOCOL):
        return pickle.dumps(self,protocol=protocol)
    def __eq__(self, obj):
        if not isinstance(obj, TCP_Package):
            # don't attempt to compare against unrelated types
            return NotImplemented
        return (self.cmd == obj.cmd) and (self.data == obj.data) and (self.NP_dtype == obj.NP_dtype) and (self.NP_shape == obj.NP_shape)
