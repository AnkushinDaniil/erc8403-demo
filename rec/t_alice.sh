#!/bin/bash
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
G=$ROOT/rec/gate
cd $ROOT
export PATH=$PATH:$ROOT/wallet
PS=$'\e[1;32malice\e[0m:\e[1;34m~\e[0m$ '
typeit() { for ((i=0;i<${#1};i++)); do printf '%s' "${1:$i:1}"; sleep 0.038; done; sleep 0.3; echo; }
gate() { while [ ! -e $G/$1 ]; do sleep 0.04; done; }
run() { gate $1; [ -n "$3" ] && { clear; printf '%s' "$PS"; }; typeit "$2"; touch $G/$1.typed; eval "$2"; printf '%s' "$PS"; touch $G/$1.done; }
clear
printf '%s' "$PS"
run a1 "wallet keys"
run a2 "wallet add phone --sign laptop"
run a3 "wallet send 1 bob --sign phone" c
run a4 "wallet revoke laptop --sign phone"
run a5 "rm wallet/tree.json" c
run a6 "wallet send 1 bob --sign phone"
run a7 "wallet recover"
run a8 "wallet send 1 bob --sign phone"
run b1 "relay" c
run b2 "wallet send 1 bob --sign phone --on two"
run b3 "wallet revoke phone --sign vault" c
run b4 "relay"
run b5 "relay --after-window" c
sleep 600