import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys, os
os.environ["RPC"] = "http://127.0.0.1:8621"
sys.path.insert(0, f'{ROOT}/wallet'); sys.path.insert(0, f'{ROOT}/mc')
from w import *
from abi import *
code = open(f'{ROOT}/mc/sol/HomeVerifier.hex').read().strip()
V = '0x' + '00' * 18 + 'f00d'
n = rpc("eth_blockNumber", [])['result']
hdr = bytes.fromhex(rpc("debug_getRawHeader", [n])['result'][2:])
p = rpc("eth_getProof", ['0x' + ALICE.hex(), ['0x0'], n])['result']
acc = [bytes.fromhex(x[2:]) for x in p['accountProof']]
sto = [bytes.fromhex(x[2:]) for x in p['storageProof'][0]['proof']]
print("nodes", [len(x) for x in acc], [len(x) for x in sto], "storageHash", p['storageHash'])
def call(data):
    return rpc("eth_call", [{"to": V, "data": '0x' + data.hex(), "gas": hex(3000000)}, n, {V: {"code": '0x' + code}}])
r = call(encode(IMPORT, [ALICE, (hdr,), acc])); print(r)
r2 = call(encode(SLOT0, [bytes.fromhex(p['storageHash'][2:]), sto])); print(r2, chain_root().hex())
g = rpc("eth_estimateGas", [{"to": V, "data": '0x' + encode(SLOT0, [bytes.fromhex(p['storageHash'][2:]), sto]).hex()}, n, {V: {"code": '0x' + code}}]); print("gas slotZero", g)
g = rpc("eth_estimateGas", [{"to": V, "data": '0x' + encode(IMPORT, [ALICE, (hdr,), acc]).hex()}, n, {V: {"code": '0x' + code}}]); print("gas import", g)
bad = bytearray(hdr); bad[100] ^= 1
print("tampered", str(call(encode(IMPORT, [ALICE, (bytes(bad),), acc])))[:200])
