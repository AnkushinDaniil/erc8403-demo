#!/bin/sh
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
docker rm -f demo-two >/dev/null 2>&1
docker run -d --name demo-two -p 127.0.0.1:8612:8545 -v $ROOT/mc/two:/bundle "${NETHERMIND_IMAGE:-nethermind:frames-da586a98}" --datadir=/data --Init.ChainSpecPath=/bundle/chainspec.json --Mining.Enabled=true --Init.DiscoveryEnabled=false --Sync.NetworkingEnabled=false --JsonRpc.Enabled=true --JsonRpc.Host=0.0.0.0 --JsonRpc.Port=8545 '--JsonRpc.EnabledModules=[Eth,Net,Web3,Debug,Trace,Admin]' >/dev/null
for i in $(seq 60); do curl -s -m 2 -X POST -H 'content-type: application/json' --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' http://127.0.0.1:8612 | grep -q result && break; sleep 1; done
