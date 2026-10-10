import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
sys.path.insert(0, f'{ROOT}/wallet')
from w import k256, w32
def sel(sig): return k256(sig.encode())[:4]
def pad(b): return b + b'\0' * (-len(b) % 32)
def enc_bytes(b): return w32(len(b)) + pad(b)
def enc_bytes_arr(a):
    heads, tails, off = b'', b'', 32 * len(a)
    for x in a:
        e = enc_bytes(x); heads += w32(off); tails += e; off += len(e)
    return w32(len(a)) + heads + tails
def encode(sig, args):
    heads, tails = [], []
    for a in args:
        if isinstance(a, list): tails.append(enc_bytes_arr(a)); heads.append(None)
        elif isinstance(a, tuple): tails.append(enc_bytes(a[0])); heads.append(None)
        else: heads.append(w32(a)); tails.append(b'')
    off = 32 * len(args); out = b''
    for h, t in zip(heads, tails):
        if h is None: out += w32(off); off += len(t)
        else: out += h
    return sel(sig) + out + b''.join(tails)
IMPORT = "importCheck(address,bytes,bytes[])"
SLOT0 = "slotZero(bytes32,bytes[])"
