import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import json, sys
sys.path.insert(0, f'{ROOT}/wallet')
from w import *
RT = "303314608157600ab0805fb1816020b190815f80b40360415760025fb46041575f5260205260405f205f5b60028110604557505f5403604157600690b35f80aa005b5f80fd5b90828260051b604001b180605d575b5090600101602a565b8082106001146077575f526020525b600160405f20906054565b905f52602052606c565b5f355f55602035806001555f5b818110609657005b8060019160061b81831b9080604001358261010001556060013590610101015501608e56"
assert len(RT) // 2 == 0xbb
d = json.load(open(sys.argv[1]))
for k in list(d['accounts']):
    if 'cafe' in k.lower(): del d['accounts'][k]
def acct(names):
    h = lambda b: '0x' + b.hex()
    recs = [(DEVICES[n][1], addr_of(n)) for n in names]
    st = {h(w32(0)): h(tree([leaf(*r) for r in recs])[0]), h(w32(1)): h(w32(len(recs)))}
    for i, (aid, a) in enumerate(recs):
        st[h(w32(0x100 + 2 * i))] = h(w32(aid)); st[h(w32(0x101 + 2 * i))] = h(w32(a))
    return {"balance": hex(100 * 10**18), "code": "0x" + RT, "storage": st}
d['accounts']['0x' + ALICE.hex()] = acct(["laptop", "vault"])
d['accounts']['0x' + MALLORY_ACCT.hex()] = acct(["mallory"])
d['accounts']['0x' + BOB.hex()] = {"balance": "0x1"}
d['accounts']['0x' + THIEF.hex()] = {"balance": "0x1"}
json.dump(d, open(f'{ROOT}/chain/chainspec.json', 'w'))
print("ok")
