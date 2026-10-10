import os; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys; sys.path.insert(0,f'{ROOT}/wallet')
from w import *
P=lambda n: bytes.fromhex(DEVICES[n][0])
def show(tag,r):
    print(tag, {k:(v if k!='receipt' else '...') for k,v in r.items()})
    if 'receipt' in r: print('   frames:', json.dumps(r['receipt'].get('frameReceipts'))[:400], 'gasUsed', r['receipt'].get('gasUsed'))
print('root', chain_root().hex(), chain_records())
lap=(DEVICES['laptop'][1], addr_of('laptop')); ph=(DEVICES['phone'][1], addr_of('phone'))
L1=leaf(*lap); L2=leaf(*ph)
# 0 transfer with laptop
fr=[verify_frame(lap[0],lap[1],[]),[2,0,BOB,[60000,0],10**18,b'']]
raw,_=sign_tx(ALICE,nonce_of(ALICE),fr,P('laptop'),fees()); show('send-laptop',send_raw(raw)); print('bob',balance(BOB))
# 1 add phone
root2,proofs=tree([L1,L2])
cd=root2+w32(2)+w32(lap[0])+w32(lap[1])+w32(ph[0])+w32(ph[1])
fr=[verify_frame(lap[0],lap[1],[]),[2,0,ALICE,[200000,200000],0,cd]]
raw,_=sign_tx(ALICE,nonce_of(ALICE),fr,P('laptop'),fees()); show('add-phone',send_raw(raw))
print('root', chain_root().hex(), root2.hex(), chain_records())
