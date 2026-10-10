import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys, os
os.environ["RPC"] = "http://127.0.0.1:8621"
sys.path.insert(0, f'{ROOT}/wallet')
from w import *
r = rpc("debug_getRawHeader", ["latest"])
raw = bytes.fromhex(r['result'][2:])
h = rlp.decode(raw)
print("fields", len(h), [len(x) for x in h])
print("hash", k256(raw).hex())
extra = h[12]
sig = extra[-65:]
h2 = list(h); h2[12] = extra[:-65]
seal = k256(rlp.encode(h2))
pk = keys.Signature(sig).recover_public_key_from_msg_hash(seal)
print("signer", pk.to_canonical_address().hex(), "stateRoot", h[3].hex(), "number", int.from_bytes(h[8], 'big'))
p = rpc("eth_getProof", ['0x' + ALICE.hex(), ['0x0'], 'latest'])
print(str(p)[:600])
print("root", chain_root().hex(), "bal", balance(ALICE))
