#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
export PATH=$HOME/.foundry/bin:$PATH
orig=$(mktemp); cp src/Follower.sol "$orig"
run() { name=$1; from=$2; to=$3
  python3 -c 'import sys;p,a,b=sys.argv[1:];s=open(p).read();assert a in s,a;open(p,"w").write(s.replace(a,b,1))' src/Follower.sol "$from" "$to"
  echo "== $name"; forge test 2>&1 | grep -E "^\[FAIL|Suite result"; cp "$orig" src/Follower.sol; }
run M1-nochain "require(block.chainid != homeChainId);" ""
run M2-noage "if (timestamp < block.timestamp) require(block.timestamp - timestamp <= maxAge);" ""
run M3-alwaysemit "if (value != currentRoot) {" "if (true) {"
run M4-noorder "require(blockNumber > homeBlockNumber);" ""
run M5-noshort "require(ok && ret.length >= 64);" "require(ok);"
run M6-nostoreblock "homeBlockNumber = blockNumber;" ""
run V1-nozeropred "require(predicate != bytes32(0));" ""
run V2-norootcmp "require(h == currentRoot);" ""
run V3-nomsgempty "require(msgEmpty);" ""
run V4-nosigner "require(signer == address(uint160(uint256(predicate))));" ""
run V5-nonomanage "if (uint256(predicate) & NO_MANAGE != 0) require(!_senderFrameToSelf());" ""
run V6-noapprove "_approve(_frameScope());" ""
run V7-swapchildren "? keccak256(abi.encodePacked(bytes1(0x01), h, siblings[k]))" "? keccak256(abi.encodePacked(bytes1(0x01), siblings[k], h))"
echo "== restored"; forge test 2>&1 | grep "Suite result"
