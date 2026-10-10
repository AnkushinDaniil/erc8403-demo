import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import json, sys
sys.path.insert(0, f'{ROOT}/wallet')
from eth_keys import keys
SIGNER_PRIV = "8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba"
signer = keys.PrivateKey(bytes.fromhex(SIGNER_PRIV)).public_key.to_canonical_address()
d = json.load(open('chain/chainspec.json'))
d['name'] = 'home'
d['engine'] = {"clique": {"params": {"period": 1, "epoch": 30000}}}
drop = sys.argv[2].split(',') if len(sys.argv) > 2 and sys.argv[2] else []
for k in list(d['params']):
    if any(x in k for x in drop): del d['params'][k]
g = d['genesis']
g['difficulty'] = '0x1'
g['extraData'] = '0x' + '00' * 32 + signer.hex() + '00' * 65
g['seal'] = {"ethereum": {"nonce": "0x0000000000000000", "mixHash": "0x" + "00" * 32}}
json.dump(d, open(sys.argv[1], 'w'))
print("signer", signer.hex())
