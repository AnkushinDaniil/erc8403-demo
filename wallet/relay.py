import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mc import *
G, R, D, B, X = "\033[1;32m", "\033[1;31m", "\033[2m", "\033[1m", "\033[0m"
if "--after-window" in sys.argv:
    first = min(int(f.split(".")[0]) for f in os.listdir(PROOFS))
    close = first + WINDOW
    on("home")
    while True:
        now = int(w.rpc("eth_blockNumber", [])['result'], 16)
        print(f"\rroot @{first} leaves the window at {B}#{close}{X} · now #{now} ", end="", flush=True)
        if now >= close: break
        time.sleep(0.2)
    print()
b = home_bundle()
print(f"home block {B}#{b['height']}{X} · sealed by 0x{HOME_SIGNER.hex()[:6]}…{HOME_SIGNER.hex()[-6:]}")
for name, acct in (("savings", ALICE), ("daily", DAILY)):
    r = plain_tx(RELAYER, acct, import_data(b))
    if r["ok"] and imported(acct) == b["height"]:
        print(f"{G}✓{X} {name:<8} checked seal + proof · home root {B}@{b['height']}{X}")
    else:
        print(f"{R}✗ {name} refused the block{X}"); sys.exit(1)
