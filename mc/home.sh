#!/bin/sh
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
docker rm -f demo-home >/dev/null 2>&1
docker run -d --name demo-home -p 127.0.0.1:8621:8545 -v $ROOT/mc/home:/bundle "${NETHERMIND_IMAGE:-nethermind:frames-da586a98}" --datadir=/data --Init.ChainSpecPath=/bundle/chainspec.json --Mining.Enabled=true --KeyStore.TestNodeKey=8b3a350cf5c34c9194ca85829a2df0ec3153be0318b5e2d3348e872092edffba --Init.DiscoveryEnabled=false --Sync.NetworkingEnabled=false --JsonRpc.Enabled=true --JsonRpc.Host=0.0.0.0 --JsonRpc.Port=8545 '--JsonRpc.EnabledModules=[Eth,Net,Web3,Debug,Trace,Admin,Clique,Proof]' >/dev/null
