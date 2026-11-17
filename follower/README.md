# ERC-8403 `SLOTS16_SYNC` follower sketch

`src/Follower.sol` implements `IERC8403` (`authorityRoot`, `AuthorityStateChanged`), `home`, `sync` and the `SLOTS16` `validate` root check of a follower, with a mock adapter.

`validate` recomputes the root from `id`, `predicate` and the four siblings and compares it with the current root. The frame parts of the check (entry 0 signer, empty `msg`, `SENDER` frame to the account, `APPROVE`) are virtual hooks; `MockFrameFollower` sets them from the test. So the tests cover the root check and the order of checks, not EIP-8141 frame execution. Nothing here runs on an EIP-8141 node, and the adapter is a mock, not a storage proof.

Run: `forge test`. Mutation check: `./mutate.sh` (13 mutants; `M5` survives because `abi.decode` already reverts on short return data).
