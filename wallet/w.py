import rlp, json, urllib.request, time, os
from Crypto.Hash import keccak
from eth_keys import keys

RPC = os.environ.get("RPC", "http://127.0.0.1:8621")
CHAIN = 0x13e02
HOME = os.path.dirname(os.path.abspath(__file__))
ALICE = bytes.fromhex("00000000000000000000000000000000cafe8403")
MALLORY_ACCT = bytes.fromhex("00000000000000000000000000000000cafe8402")
BOB = bytes.fromhex("0000000000000000000000000000000000000b0b")
THIEF = bytes.fromhex("0000000000000000000000000000000000000bad")
DEVICES = {
    "laptop": ("59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d", 0x0a01),
    "phone": ("5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a", 0x0a02),
    "vault": ("47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a", 0x0a03),
    "mallory": ("7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6", 0x0b01),
}

def k256(b):
    h = keccak.new(digest_bits=256); h.update(b); return h.digest()
def be(x):
    if isinstance(x, (bytes, bytearray)): return bytes(x)
    return b'' if x == 0 else x.to_bytes((x.bit_length() + 7) // 8, 'big')
def w32(x):
    return x.to_bytes(32, 'big') if isinstance(x, int) else bytes(x).rjust(32, b'\0')
def rpc(m, p):
    req = {"jsonrpc": "2.0", "method": m, "params": p, "id": 1}
    r = urllib.request.urlopen(urllib.request.Request(RPC, json.dumps(req).encode(), {'content-type': 'application/json'}))
    return json.load(r)
def addr_of(name):
    return keys.PrivateKey(bytes.fromhex(DEVICES[name][0])).public_key.to_canonical_address()
def leaf(aid, addr):
    return k256(w32(aid) + w32(addr))
def pair(a, b):
    return k256(a + b) if a < b else k256(b + a)
def tree(leaves):
    level = sorted(leaves)
    proofs = {l: [] for l in level}
    groups = [[l] for l in level]
    while len(level) > 1:
        nl, ng = [], []
        for i in range(0, len(level), 2):
            if i + 1 < len(level):
                for l in groups[i]: proofs[l].append(level[i + 1])
                for l in groups[i + 1]: proofs[l].append(level[i])
                nl.append(pair(level[i], level[i + 1])); ng.append(groups[i] + groups[i + 1])
            else:
                nl.append(level[i]); ng.append(groups[i])
        level, groups = nl, ng
    return (level[0] if level else b'\0' * 32), proofs
def slot(acct, i):
    return bytes.fromhex(rpc("eth_getStorageAt", ['0x' + acct.hex(), hex(i), 'latest'])['result'][2:].rjust(64, '0'))
def chain_root(acct=ALICE):
    return slot(acct, 0)
def chain_records(acct=ALICE):
    n = int.from_bytes(slot(acct, 1), 'big')
    return [(int.from_bytes(slot(acct, 0x100 + 2 * i), 'big'), slot(acct, 0x101 + 2 * i)[12:]) for i in range(n)]
def balance(a):
    return int(rpc("eth_getBalance", ['0x' + a.hex(), 'latest'])['result'], 16)
def enc_frame(f):
    mode, flags, target, limits, value, data = f
    return [be(mode), be(flags), bytes(target), [be(limits[0]), be(limits[1])], be(value), bytes(data)]
def fees():
    bf = int(rpc("eth_getBlockByNumber", ['latest', False])['result']['baseFeePerGas'], 16)
    return 1_000_000_000, bf * 2 + 2_000_000_000
def nonce_of(acct):
    return int(rpc("eth_getTransactionCount", ['0x' + acct.hex(), 'pending'])['result'], 16)
def body(sender, nonce, frames, sig, fee, signer=b''):
    return [be(CHAIN), be(nonce), bytes(sender), [enc_frame(f) for f in frames], [[be(1), bytes(signer), b'', sig]], [be(fee[0]), be(fee[1]), b''], []]
def sign_tx(sender, nonce, frames, priv, fee):
    signer = keys.PrivateKey(priv).public_key.to_canonical_address()
    digest = k256(b'\x06' + rlp.encode(body(sender, nonce, frames, b'', fee, signer)))
    s = keys.PrivateKey(priv).sign_msg_hash(digest)
    sig = bytes([s.v]) + s.r.to_bytes(32, 'big') + s.s.to_bytes(32, 'big')
    return b'\x06' + rlp.encode(body(sender, nonce, frames, sig, fee, signer)), sig
def verify_frame(aid, addr, proof, gas=80000):
    sibs = (list(proof) + [b'\0' * 32] * 2)[:2]
    return [1, 3, b'', [gas, 0], 0, w32(aid) + w32(addr) + sibs[0] + sibs[1]]
def send_raw(raw, wait=8.0):
    res = rpc("eth_sendRawTransaction", ['0x' + raw.hex()])
    if 'error' in res:
        return {"ok": False, "stage": "mempool", "error": res['error']['message']}
    h = res['result']
    t = time.time()
    while time.time() - t < wait:
        rc = rpc("eth_getTransactionReceipt", [h]).get('result')
        if rc:
            return {"ok": int(rc['status'], 16) == 1, "stage": "block", "hash": h, "block": int(rc['blockNumber'], 16), "receipt": rc}
        time.sleep(0.2)
    return {"ok": False, "stage": "dropped", "hash": h}
