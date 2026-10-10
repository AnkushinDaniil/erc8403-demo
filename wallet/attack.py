import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from w import *
import rlp
G, R, Y, D, B, X = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[2m", "\033[1m", "\033[0m"
sh = lambda b: "0x" + b.hex()[:6] + "…" + b.hex()[-6:]
DRAIN = [2, 0, THIEF, [60000, 0], 50 * 10**18, b""]
def report(r):
    if r["ok"]:
        print(f"{G}!! accepted{X} · block {r['block']} · funds moved")
    else:
        print(f"{R}✗ REFUSED BY THE NODE{X}"); print(f"  {D}" + r.get('error', r['stage']).replace("frame transaction ", "").replace("transaction invalid, ", "").replace(", ", f"{X}\n  {D}") + X)
    print(f"thief balance: {B}{balance(THIEF) / 1e18:.2f} ETH{X}")
def stolen_key():
    lap = (DEVICES["laptop"][1], addr_of("laptop"))
    ls = [leaf(DEVICES[n][1], addr_of(n)) for n in ("laptop", "vault", "phone")]
    old_root, proofs = tree(ls)
    print(f"signing with the stolen {B}laptop{X} key")
    print(f"proof for the old root {sh(old_root)}")
    raw, _ = sign_tx(ALICE, nonce_of(ALICE), [verify_frame(lap[0], lap[1], proofs[leaf(*lap)]), DRAIN], bytes.fromhex(DEVICES["laptop"][0]), fees())
    report(send_raw(raw))
def foreign_proof():
    m = (DEVICES["mallory"][1], addr_of("mallory"))
    print(f"mallory's key is valid in {B}her own{X} account 0x…{MALLORY_ACCT.hex()[-8:]}")
    print(f"sending her proof to alice's account 0x…{ALICE.hex()[-8:]}")
    raw, _ = sign_tx(ALICE, nonce_of(ALICE), [verify_frame(m[0], m[1], []), DRAIN], bytes.fromhex(DEVICES["mallory"][0]), fees())
    report(send_raw(raw))
def reuse_signature():
    raw = bytes.fromhex(open(os.path.join(HOME, "sent.log")).read())
    b = rlp.decode(raw[1:])
    print(f"copied alice's last signature from the chain")
    print(f"same signature, new recipient: {B}thief{X}")
    b[1] = be(nonce_of(ALICE))
    b[3][1][2] = THIEF
    b[3][1][4] = be(50 * 10**18)
    report(send_raw(b"\x06" + rlp.encode(b)))
def thief_two():
    import mc
    mc.on("two")
    return mc
def first_bundle(mc):
    return mc.load_bundle(min(int(f.split(".")[0]) for f in os.listdir(mc.PROOFS)))
def forged_header():
    mc = thief_two()
    from forge import forged_header as forge
    old = first_bundle(mc)
    mc.on("home"); height = int(mc.w.rpc("eth_blockNumber", [])['result'], 16) + 2; mc.on("two")
    print(f"a home block {B}#{height}{X}, sealed with the thief's own key")
    r = mc.plain_tx(mc.ANYONE, ALICE, mc.import_data(old, forge(old, height, mc.ANYONE)))
    if r["ok"]:
        print(f"{Y}!! accepted{X} · block {r['block']}")
    else:
        print(f"{R}✗ REFUSED BY THE ACCOUNT{X}"); print(f"  {D}import reverted on chain two{X}"); print(f"  {D}newest home root stays @{mc.imported(ALICE)}{X}")
    print(f"thief balance: {B}{balance(THIEF) / 1e18:.2f} ETH{X}")
def stale_proof():
    mc = thief_two()
    name = sys.argv[2]
    target, tier, wei = {"savings": (ALICE, "tier 2 · newest root only", 50 * 10**18), "daily": (mc.DAILY, f"tier 1 · last {mc.WINDOW} blocks", 2 * 10**18)}[name]
    old = first_bundle(mc)
    records = [(n, DEVICES[n][1], addr_of(n)) for n in ("vault", "phone")]
    print(f"stolen {B}phone{X} key + home proof from block {B}#{old['height']}{X}")
    print(f"target: {B}{name}{X} ({tier})")
    r = mc.remote_send(target, "phone", records, old, THIEF, wei)
    if r["ok"]:
        print(f"{Y}!! ACCEPTED{X} · block {r['block']} · {wei // 10**18} ETH moved")
    else:
        print(f"{R}✗ REFUSED BY THE NODE{X}"); print(f"  {D}" + r.get('error', r['stage']).replace("frame transaction ", "").replace(", ", f"{X}\n  {D}") + X)
    print(f"thief balance: {B}{balance(THIEF) / 1e18:.2f} ETH{X}")
{"forged-header": forged_header, "stale-proof": stale_proof, "stolen-key": stolen_key, "foreign-proof": foreign_proof, "reuse-signature": reuse_signature}[sys.argv[1]]()
