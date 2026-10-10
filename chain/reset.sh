#!/bin/sh
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
cd $ROOT
docker rm -f demo8403 >/dev/null 2>&1
.venv/bin/python mc/mkclique.py mc/home/chainspec.json "" >/dev/null
.venv/bin/python mc/mktwo.py >/dev/null
mc/home.sh
mc/two.sh
for i in $(seq 60); do curl -s -m 2 -X POST -H 'content-type: application/json' --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' http://127.0.0.1:8621 | grep -q '"result":"0x[1-9a-f]' && break; sleep 1; done
rm -rf wallet/tree.json wallet/sent.log mc/proofs
wallet/wallet init
