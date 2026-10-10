import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import json, sys
sys.path.insert(0, f'{ROOT}/wallet'); sys.path.insert(0, f'{ROOT}/mc')
from w import ALICE, MALLORY_ACCT, BOB, THIEF
from eth_keys import keys
from mkremote import build
from mc import HELPER, DAILY, HOME_SIGNER, RELAYER, ANYONE, WINDOW, CHAIN_TWO
d = json.load(open(f'{ROOT}/chain/chainspec.json'))
d['name'] = 'two'
d['params']['networkID'] = hex(CHAIN_TWO)
for k in list(d['accounts']):
    if k.lower()[2:] in (ALICE.hex(), MALLORY_ACCT.hex(), BOB.hex(), THIEF.hex()): del d['accounts'][k]
a = d['accounts']
a['0x' + HELPER.hex()] = {"balance": "0x1", "code": "0x" + open(f'{ROOT}/mc/sol/HomeVerifier.hex').read().strip()}
a['0x' + ALICE.hex()] = {"balance": hex(100 * 10**18), "code": "0x" + build(ALICE, HOME_SIGNER, HELPER, 2, WINDOW)}
a['0x' + DAILY.hex()] = {"balance": hex(5 * 10**18), "code": "0x" + build(ALICE, HOME_SIGNER, HELPER, 1, WINDOW)}
for k in (BOB, THIEF): a['0x' + k.hex()] = {"balance": "0x1"}
for k in (RELAYER, ANYONE): a['0x' + keys.PrivateKey(bytes.fromhex(k)).public_key.to_canonical_address().hex()] = {"balance": hex(10 * 10**18)}
json.dump(d, open(f'{ROOT}/mc/two/chainspec.json', 'w'))
print("ok")
