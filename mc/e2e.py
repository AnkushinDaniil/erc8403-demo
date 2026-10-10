import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'wallet'))
from mc import *
from forge import forged_header
env = dict(os.environ, RPC=HOME_RPC)
cli = lambda *a: print(subprocess.run([f"{ROOT}/wallet/wallet", *a], env=env, capture_output=True, text=True).stdout.strip())
def short(r): return {k: (v if k != 'receipt' else v.get('gasUsed')) for k, v in r.items() if k != 'hash'}
cli("init")
recs = [(n, DEVICES[n][1], addr_of(n)) for n in ("laptop", "vault")]
b1 = home_bundle()
for acct in (ALICE, DAILY): print("import", acct.hex()[-8:], short(plain_tx(RELAYER, acct, import_data(b1))), imported(acct))
print("T2 pay", short(remote_send(ALICE, "laptop", recs, b1, BOB, 10**18)))
print("T1 pay", short(remote_send(DAILY, "laptop", recs, b1, BOB, 10**17)))
cli("revoke", "laptop", "--sign", "vault")
b2 = home_bundle()
for acct in (ALICE, DAILY): print("import", short(plain_tx(RELAYER, acct, import_data(b2))), imported(acct))
print("forged", short(plain_tx(ANYONE, ALICE, import_data(b1, forged_header(b1, b2['height'] + 5, ANYONE)))), imported(ALICE))
print("stale T2", short(remote_send(ALICE, "laptop", recs, b1, THIEF, 10**18)))
print("stale T1 in window", short(remote_send(DAILY, "laptop", recs, b1, THIEF, 2 * 10**18)))
on("home")
while int(w.rpc("eth_blockNumber", [])['result'], 16) < b1['height'] + WINDOW: time.sleep(1)
b3 = home_bundle()
print("import", short(plain_tx(RELAYER, DAILY, import_data(b3))), imported(DAILY))
print("stale T1 after window", short(remote_send(DAILY, "laptop", recs, b1, THIEF, 2 * 10**18)))
print("vault T2 fresh", short(remote_send(ALICE, "vault", [recs[1]], b2, BOB, 10**18)))
on("two"); print("thief", w.balance(THIEF) / 1e18, "bob", w.balance(BOB) / 1e18)
