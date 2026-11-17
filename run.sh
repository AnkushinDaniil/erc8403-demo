#!/bin/bash
ROOT="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
cd "$ROOT"
export PATH="$PATH:$ROOT/wallet"
step() { printf '\n$ %s\n' "$*"; "$@"; }
chain/reset.sh
echo "This walkthrough uses a minimal account. The ERC-8403 account is in slots16/ (run slots16/test.py)."
step wallet keys
step wallet add phone --sign laptop
step wallet send 1 bob --sign phone
step wallet revoke laptop --sign phone
step attack stolen-key
step attack foreign-proof
step attack reuse-signature
step attack signed-message
step rm wallet/tree.json
step wallet send 1 bob --sign phone
step wallet recover
step wallet send 1 bob --sign phone
step relay
step wallet send 1 bob --sign phone --on two
step wallet revoke phone --sign vault
step relay
step attack forged-header
step attack stale-proof savings
step attack stale-proof daily
step relay --after-window
step attack stale-proof daily
echo; echo "fresh chains for the last attack"
chain/reset.sh >/dev/null
step attack takeover
