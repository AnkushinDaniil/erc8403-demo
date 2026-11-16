import json, os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PORT = int(os.environ.get("PORT", "8631"))
os.environ["RPC"] = f"http://127.0.0.1:{PORT}"
sys.path.insert(0, f"{ROOT}/wallet")
from w import *

NAME = "demo-slots16"
NO_MANAGE = 1 << 160
ACCT = bytes.fromhex("00000000000000000000000000000000cafe1616")
SEL_VALIDATE = bytes.fromhex("806afe1e")
SEL_SET = bytes.fromhex("1feb3d6a")
TOPIC = "0x83cb463cdb16a1f07dec96ec96c4f7a43dbac052f1975785c20893767dfb825a"
MANAGER, SPENDER = "laptop", "phone"


def runtime():
    src = open(f"{HERE}/Account.yul").read()
    start = src.index('object "runtime"')
    depth, i = 0, src.index("{", start)
    for j in range(i, len(src)):
        depth += {"{": 1, "}": -1}.get(src[j], 0)
        if depth == 0:
            break
    os.makedirs(f"{HERE}/out", exist_ok=True)
    path = f"{HERE}/out/runtime.yul"
    open(path, "w").write(src[start:j + 1])
    out = subprocess.run([os.environ.get("SOLC", "solc"), "--strict-assembly", "--optimize", "--evm-version", "cancun", "--bin", path], capture_output=True, text=True, check=True).stdout
    return re.findall(r"^[0-9a-f]{20,}$", out, re.M)[-1]


def sleaf(i, pred):
    return k256(b"\x00" + w32(i) + w32(pred)) if pred else b"\0" * 32


def levels(preds):
    lv = [[sleaf(i, p) for i, p in enumerate(preds)]]
    while len(lv[-1]) > 1:
        c = lv[-1]
        lv.append([k256(b"\x01" + c[j] + c[j + 1]) for j in range(0, len(c), 2)])
    return lv


def sroot(preds):
    return levels(preds)[-1][0] if any(preds) else b"\0" * 32


def check_data(preds, i):
    lv = levels(preds)
    return SEL_VALIDATE + w32(i) + w32(preds[i]) + b"".join(lv[h][(i >> h) ^ 1] for h in range(4))


def set_data(preds):
    return SEL_SET + b"".join(w32(p) for p in preds)


def signer_int(name):
    return int.from_bytes(addr_of(name), "big")


def start():
    d = json.load(open(f"{ROOT}/chain/chainspec.json"))
    for k in list(d["accounts"]):
        if "cafe" in k.lower():
            del d["accounts"][k]
    first = [signer_int(MANAGER)] + [0] * 15
    d["accounts"]["0x" + ACCT.hex()] = {"balance": hex(100 * 10**18), "code": "0x" + runtime(), "storage": {"0x" + w32(0).hex(): "0x" + sroot(first).hex()}}
    d["accounts"]["0x" + BOB.hex()] = {"balance": "0x1"}
    d["name"] = "slots16"
    d["engine"] = {"clique": {"params": {"period": 1, "epoch": 30000}}}
    signer_priv = "8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba"
    signer = keys.PrivateKey(bytes.fromhex(signer_priv)).public_key.to_canonical_address()
    g = d["genesis"]
    g["difficulty"] = "0x1"
    g["extraData"] = "0x" + "00" * 32 + signer.hex() + "00" * 65
    g["seal"] = {"ethereum": {"nonce": "0x0000000000000000", "mixHash": "0x" + "00" * 32}}
    json.dump(d, open(f"{HERE}/out/chainspec.json", "w"))
    subprocess.run(["docker", "rm", "-f", NAME], capture_output=True)
    subprocess.run(["docker", "run", "-d", "--name", NAME, "-p", f"127.0.0.1:{PORT}:8545", "-v", f"{HERE}/out:/bundle",
                    os.environ.get("NETHERMIND_IMAGE", "nethermind:frames-da586a98"), "--datadir=/data",
                    "--Init.ChainSpecPath=/bundle/chainspec.json", "--Mining.Enabled=true", f"--KeyStore.TestNodeKey={signer_priv}",
                    "--Init.DiscoveryEnabled=false", "--Sync.NetworkingEnabled=false", "--JsonRpc.Enabled=true",
                    "--JsonRpc.Host=0.0.0.0", "--JsonRpc.Port=8545"], check=True, capture_output=True)
    for _ in range(90):
        try:
            if int(rpc("eth_blockNumber", [])["result"], 16) > 0:
                return first
        except Exception:
            pass
        time.sleep(1)
    raise SystemExit("node did not start")


def send(preds, name, frame2):
    i = next(j for j, p in enumerate(preds) if p & ((1 << 160) - 1) == signer_int(name))
    frames = [[1, 3, b"", [200000, 0], 0, check_data(preds, i)], frame2]
    raw, _ = sign_tx(ACCT, nonce_of(ACCT), frames, bytes.fromhex(DEVICES[name][0]), fees())
    return send_raw(raw)


def sender_frame(target, data=b"", value=0):
    return [2, 0, target, [200000, 0], value, data]


results = []


def check(label, cond, detail=""):
    results.append(cond)
    print(("PASS " if cond else "FAIL ") + label + (f"  ({detail})" if detail else ""))


def main():
    first = start()
    try:
        check("first state root in slot 0", chain_root(ACCT) == sroot(first))
        cur = [signer_int(MANAGER)] + [0] * 9 + [signer_int(SPENDER) | NO_MANAGE] + [0] * 5
        r = send(first, MANAGER, sender_frame(ACCT, set_data(cur)))
        logs = r.get("receipt", {}).get("logs", [])
        check("manager adds a NO_MANAGE spender in slot 10", r["ok"] and chain_root(ACCT) == sroot(cur), r.get("error", r["stage"]))
        check("AuthoritySet log holds the new set", any(l["topics"] == [TOPIC] and bytes.fromhex(l["data"][2:]) == b"".join(w32(p) for p in cur) for l in logs))
        bob0 = balance(BOB)
        r = send(cur, SPENDER, sender_frame(BOB, value=10**18))
        check("NO_MANAGE key pays bob", r["ok"] and balance(BOB) == bob0 + 10**18, r.get("error", r["stage"]))
        lockout = [0] * 10 + [signer_int(SPENDER) | NO_MANAGE] + [0] * 5
        r = send(cur, SPENDER, sender_frame(ACCT, set_data(lockout)))
        check("NO_MANAGE key cannot call setAuthorities", not r["ok"] and r["stage"] == "mempool", r.get("error", r["stage"]))
        r = send(cur, SPENDER, sender_frame(b"", set_data(lockout)))
        check("NO_MANAGE key cannot reach the account with an empty target", not r["ok"] and r["stage"] == "mempool", r.get("error", r["stage"]))
        frames = [[1, 3, b"", [200000, 0], 0, check_data(cur, 10)], sender_frame(BOB, value=1), sender_frame(ACCT, set_data(lockout))]
        raw, _ = sign_tx(ACCT, nonce_of(ACCT), frames, bytes.fromhex(DEVICES[SPENDER][0]), fees())
        r = send_raw(raw)
        check("NO_MANAGE key cannot hide the call behind a transfer", not r["ok"] and r["stage"] == "mempool", r.get("error", r["stage"]))
        check("root unchanged after the refused calls", chain_root(ACCT) == sroot(cur))
        r = send(cur, MANAGER, sender_frame(ACCT, set_data(lockout)))
        check("setAuthorities refuses a set with no manager", chain_root(ACCT) == sroot(cur), r.get("error", r["stage"]))
        r = send(cur, MANAGER, sender_frame(ACCT, set_data([NO_MANAGE] + [0] * 15)))
        check("setAuthorities refuses NO_MANAGE alone, 2**160", chain_root(ACCT) == sroot(cur), r.get("error", r["stage"]))
        r = send(cur, MANAGER, sender_frame(ACCT, set_data([1 << 161] + [0] * 9 + [cur[10]] + [0] * 5)))
        check("setAuthorities refuses a word of 2**161", chain_root(ACCT) == sroot(cur), r.get("error", r["stage"]))
        nxt = [signer_int(MANAGER)] + [0] * 15
        r = send(cur, MANAGER, sender_frame(ACCT, set_data(nxt)))
        check("manager revokes the NO_MANAGE key", r["ok"] and chain_root(ACCT) == sroot(nxt), r.get("error", r["stage"]))
    finally:
        if not os.environ.get("KEEP"):
            subprocess.run(["docker", "rm", "-f", NAME], capture_output=True)
    print(f"{sum(results)}/{len(results)} passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
