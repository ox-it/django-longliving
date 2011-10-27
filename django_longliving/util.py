import base64
import pickle

def pack(value):
    return base64.b64encode(pickle.dumps(value))
def unpack(value):
    return pickle.loads(base64.b64decode(value))
