import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from w import *
CACHE = os.path.join(HOME, "tree.json")
SENT = os.path.join(HOME, "sent.log")
G, R, Y, D, B, X = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[2m", "\033[1m", "\033[0m"
sh = lambda b: "0x" + b.hex()[:6] + "…" + b.hex()[-6:]
NAMES = {addr_of(n): n for n in DEVICES}
PEOPLE = {"bob": BOB, "thief": THIEF}
def load():
    if not os.path.exists(CACHE):
        print(f"{R}✗ no local key tree{X}  (tree.json is missing)"); sys.exit(1)
    return [(n, a, bytes.fromhex(h)) for n, a, h in json.load(open(CACHE))]
def save(recs):
    json.dump([(n, a, h.hex()) for n, a, h in recs], open(CACHE, "w"))
def proof_for(recs, name):
    leaves = {n: leaf(a, h) for n, a, h in recs}
    root, proofs = tree(list(leaves.values()))
    return root, proofs[leaves[name]]
def signer_arg(args):
    return args[args.index("--sign") + 1]
def submit(recs, signer, frame2, okmsg):
    rec = [r for r in recs if r[0] == signer]
    if not rec:
        print(f"{R}✗ {signer} is not in the local key tree{X}"); sys.exit(1)
    _, proof = proof_for(recs, signer)
    fr = [verify_frame(rec[0][1], rec[0][2], proof), frame2]
    raw, _ = sign_tx(ALICE, nonce_of(ALICE), fr, bytes.fromhex(DEVICES[signer][0]), fees())
    open(SENT, "w").write(raw.hex())
    r = send_raw(raw)
    if r["ok"]:
        print(f"{G}✓ accepted{X} · block {r['block']} · {okmsg}")
    else:
        print(f"{R}✗ REFUSED BY THE NODE{X}"); print(f"  {D}" + r.get('error', r['stage']).replace("frame transaction ", "").replace("transaction invalid, ", "").replace(", ", f"{X}\n  {D}") + X)
    return r
def cmd_keys(args):
    root = chain_root(); recs = chain_records()
    print(f"account   0x…{ALICE.hex()[-8:]}     balance {balance(ALICE) / 1e18:.2f} ETH")
    print(f"root      {B}{sh(root)}{X}   {D}one hash on chain{X}")
    for i, (aid, a) in enumerate(recs):
        print(f"{'keys' if i == 0 else '    '}      {NAMES.get(a, '?'):<7} {sh(a)}")
def cmd_add(args):
    name, signer = args[0], signer_arg(args)
    recs = load() + [(name, DEVICES[name][1], addr_of(name))]
    setroot(recs, signer, load(), f"key {B}{name}{X} added")
def cmd_revoke(args):
    name, signer = args[0], signer_arg(args)
    old = load(); recs = [r for r in old if r[0] != name]
    setroot(recs, signer, old, f"key {B}{name}{X} revoked")
def setroot(recs, signer, old, msg):
    root, _ = tree([leaf(a, h) for _, a, h in recs])
    cd = root + w32(len(recs)) + b"".join(w32(a) + w32(h) for _, a, h in recs)
    print(f"new root  {B}{sh(root)}{X}")
    r = submit(old, signer, [2, 0, ALICE, [200000, 300000], 0, cd], msg)
    if r["ok"]: save(recs)
def cmd_send(args):
    amt, to, signer = float(args[0]), args[1], signer_arg(args)
    if "--on" in args:
        import mc
        r = mc.remote_send(ALICE, signer, load(), mc.load_bundle(mc.imported(ALICE)), PEOPLE[to], int(amt * 10**18))
        if r["ok"]:
            print(f"{G}✓ accepted{X} · chain two · savings · {amt:g} ETH → {to}")
        else:
            print(f"{R}✗ REFUSED BY THE NODE{X}"); print(f"  {D}{r.get('error', r['stage'])}{X}")
        return
    submit(load(), signer, [2, 0, PEOPLE[to], [60000, 0], int(amt * 10**18), b""], f"{amt:g} ETH → {to}")
def cmd_recover(args):
    recs = chain_records()
    print(f"read {len(recs)} key record(s) from account storage")
    root, _ = tree([leaf(a, h) for a, h in recs])
    on = chain_root()
    print(f"rebuilt   {B}{sh(root)}{X}")
    print(f"on chain  {B}{sh(on)}{X}")
    if root != on:
        print(f"{R}✗ mismatch{X}"); sys.exit(1)
    save([(NAMES.get(h, "?"), a, h) for a, h in recs])
    print(f"{G}✓ match{X} · key tree restored, no backup used")
def cmd_init(args):
    recs = chain_records()
    save([(NAMES.get(h, "?"), a, h) for a, h in recs]); print("ok")
if __name__ == "__main__":
    {"keys": cmd_keys, "add": cmd_add, "revoke": cmd_revoke, "send": cmd_send, "recover": cmd_recover, "init": cmd_init}[sys.argv[1]](sys.argv[2:])
