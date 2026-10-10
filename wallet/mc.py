import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys, os, json, time
sys.path.insert(0, f'{ROOT}/wallet')
import w, rlp
from w import k256, be, w32, keys, ALICE, BOB, THIEF, DEVICES, addr_of, leaf, tree
from abi import encode, IMPORT, SLOT0
HOME_RPC, TWO_RPC = "http://127.0.0.1:8621", "http://127.0.0.1:8612"
CHAIN_HOME, CHAIN_TWO = 0x13e02, 0x13e03
HELPER = bytes.fromhex("00" * 18 + "f00d")
DAILY = bytes.fromhex("00000000000000000000000000000000cafe8401")
HOME_SIGNER = bytes.fromhex("9965507d1a55bcc2695c58ba16fb37d819b0a4dc")
RELAYER = "2a871d0798f97d79848a013d4936a73bf4cc922c825d33c1cf7073dff6d409c6"
ANYONE = "dbda1821b80551c9d65939329250298aa3472ba22feea921c0cf5d620ea67b97"
WINDOW = 40
PROOFS = f"{ROOT}/mc/proofs"
def on(chain):
    w.RPC, w.CHAIN = (HOME_RPC, CHAIN_HOME) if chain == "home" else (TWO_RPC, CHAIN_TWO)
def hx(s): return bytes.fromhex(s[2:])
def home_bundle(height=None):
    on("home")
    tag = hex(height) if height is not None else w.rpc("eth_blockNumber", [])['result']
    header = hx(w.rpc("debug_getRawHeader", [tag])['result'])
    p = w.rpc("eth_getProof", ['0x' + ALICE.hex(), ['0x0'], tag])['result']
    b = {"height": int(tag, 16), "header": header.hex(), "account": [x[2:] for x in p['accountProof']], "storage": [x[2:] for x in p['storageProof'][0]['proof']], "root": p['storageProof'][0]['value']}
    os.makedirs(PROOFS, exist_ok=True)
    json.dump(b, open(f"{PROOFS}/{b['height']}.json", "w"))
    return b
def load_bundle(height):
    return json.load(open(f"{PROOFS}/{height}.json"))
def plain_tx(priv, to, data, gas=600000):
    on("two")
    k = keys.PrivateKey(bytes.fromhex(priv))
    sender = k.public_key.to_canonical_address()
    tip, cap = w.fees()
    body = [be(CHAIN_TWO), be(w.nonce_of(sender)), be(tip), be(cap), be(gas), bytes(to), b'', data, []]
    s = k.sign_msg_hash(k256(b'\x02' + rlp.encode(body)))
    return w.send_raw(b'\x02' + rlp.encode(body + [be(s.v), be(s.r), be(s.s)]))
def import_data(bundle, header=None):
    return encode(IMPORT, [ALICE, (header or bytes.fromhex(bundle['header']),), [bytes.fromhex(x) for x in bundle['account']]])
def imported(account):
    on("two")
    return int.from_bytes(w.slot(account, 2), 'big')
def remote_frame(aid, addr, proof, bundle, gas=250000):
    sibs = (list(proof) + [b'\0' * 32] * 2)[:2]
    call = encode(SLOT0, [bytes(32), [bytes.fromhex(x) for x in bundle['storage']]])
    return [1, 3, b'', [gas, 0], 0, w32(aid) + w32(addr) + sibs[0] + sibs[1] + w32(bundle['height']) + call]
def remote_send(account, signer, records, bundle, to, wei):
    on("two")
    leaves = {n: leaf(a, h) for n, a, h in records}
    _, proofs = tree(list(leaves.values()))
    rec = [r for r in records if r[0] == signer][0]
    frames = [remote_frame(rec[1], rec[2], proofs[leaves[signer]], bundle), [2, 0, to, [60000, 0], wei, b""]]
    raw, _ = w.sign_tx(account, w.nonce_of(account), frames, bytes.fromhex(DEVICES[signer][0]), w.fees())
    return w.send_raw(raw)
