# ERC-8403 demo

A runnable demo of [ERC-8403: Account Authority Lifecycle](https://github.com/ethereum/ERCs/pull/1979) on two local Nethermind nodes with EIP-8141 frame transactions.

Video, 3 minutes: https://x.com/Ankuinf/status/2108841686902136992 (the same file is attached to the [release](https://github.com/AnkushinDaniil/erc8403-demo/releases/tag/v2)).

## What it shows

The account stores one hash: the root of a tree of its keys. A transaction carries a Merkle proof for the key that signs it.

`run.sh` runs these steps in order. Every `accepted` and `REFUSED` line is the answer of the node or of the contract.

| Step | Result |
| --- | --- |
| add a phone key, pay with it, revoke the laptop key | accepted, the address stays |
| thief signs with the revoked laptop key and an old proof | refused by the node |
| thief sends a proof that is valid for another account | refused by the node |
| thief copies a signature from the chain and changes the recipient | refused by the node |
| the local key tree is deleted, the wallet rebuilds it from account storage | root matches |
| a relayer brings a sealed home block to chain two | both accounts check the seal and the storage proof |
| the phone pays on chain two with a proof from the home chain | accepted |
| the phone key is revoked at home, the new block is relayed | accepted |
| thief forges a home block with his own key | refused by the account |
| thief uses the revoked phone key and an old proof on `savings` (tier 2) | refused by the node |
| the same on `daily` (tier 1) | accepted, 2 ETH are gone |
| the same on `daily` 40 home blocks later | refused by the node |

The accepted theft is on purpose. Tier 1 accepts any root inside its window, so a revoked key works until the window closes. Tier 2 accepts the newest root only.

## Run

You need docker, Python 3 (tested with 3.13), curl and `solc` 0.8.36.

Build the node. The demo is pinned to one Nethermind commit:

```
git clone https://github.com/NethermindEth/nethermind
cd nethermind
git checkout da586a98ae9219c4cb759fbce1a9e13a2ea13973
docker build -t nethermind:frames-da586a98 .
```

Then, in this repository:

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
SOLC=/path/to/solc-0.8.36 ./run.sh
```

The run takes about two minutes. Most of that time is the wait for the tier 1 window to close.

`NETHERMIND_IMAGE` selects another image. `ethpandaops/nethermind:frames-devnet-0` answers `Invalid RLP` to these transactions (checked on 2026-10-10), so the default stays on the pinned commit.

The nodes listen on `127.0.0.1:8621` (home chain) and `127.0.0.1:8612` (chain two). `web/serve.py` serves a small explorer on `127.0.0.1:8700`.

## SLOTS16 with NO_MANAGE

`slots16/Account.yul` implements the `SLOTS16` scheme of the current ERC text: 16 slots, `validate` with the `NO_MANAGE` frame loop, and `setAuthorities` that refuses a set with no authority that may manage it. `slots16/test.py` starts one node, gives the account a manager key, adds a `NO_MANAGE` key in slot 10, and checks:

- the `NO_MANAGE` key pays bob
- the node refuses its call to `setAuthorities`, with an explicit or an empty target, alone or after a transfer
- `setAuthorities` refuses a set with no manager, `2**160` alone, and a word of `2**161`
- the manager revokes the `NO_MANAGE` key
- `authorityRoot()` returns the current root and `SLOTS16`, and `setAuthorities` emits `AuthorityStateChanged` with the new root when the root changes, the discovery interface `IERC8403`

```
SOLC=/path/to/solc-0.8.36 .venv/bin/python slots16/test.py
```

## What is simplified

- `yul/src/Account.yul` is a minimal account, not a full ERC-8403 implementation. Any key in the tree can set a new root.
- The home chain is Clique with one signer. Chain two trusts that signer and nothing else: `mc/sol/HomeVerifier.sol` recovers the signer from the header seal and checks the storage proof against the state root in that header. The relayer is not trusted.
- The tier 1 window is counted by the account contract. It does not use EIP-8272.
- Leaves are secp256k1 keys. There is no post-quantum key in the demo.
- All private keys in the scripts are the public anvil test keys.

## Layout

- `chain/`, `mc/`: chain specs, node start scripts, contracts for chain two.
- `wallet/`: the `wallet`, `attack` and `relay` commands.
- `yul/`: the home account.
- `web/`: explorer pages and the animation page used in the video.
- `rec/`, `voice/`: scripts and data that made the video.

## Video

`rec/all.sh` records the screen and renders the video. It needs Xvfb, xterm, ffmpeg, Chromium and the packages in `requirements-video.txt`. It was run only on the machine that made the video.
