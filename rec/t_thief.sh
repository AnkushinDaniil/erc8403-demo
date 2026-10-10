#!/bin/bash
ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
G=$ROOT/rec/gate
cd $ROOT
export PATH=$PATH:$ROOT/wallet
PS=$'\e[1;31mthief\e[0m:\e[1;34m~\e[0m$ '
typeit() { for ((i=0;i<${#1};i++)); do printf '%s' "${1:$i:1}"; sleep 0.038; done; sleep 0.3; echo; }
gate() { while [ ! -e $G/$1 ]; do sleep 0.04; done; }
run() { gate $1; clear; printf '%s' "$PS"; typeit "$2"; touch $G/$1.typed; eval "$2"; printf '%s' "$PS"; touch $G/$1.done; }
clear
printf '%s' "$PS"
run t1 "attack stolen-key"
run t2 "attack foreign-proof"
run t3 "attack reuse-signature"
run u1 "attack forged-header"
run u2 "attack stale-proof savings"
run u3 "attack stale-proof daily"
run u4 "attack stale-proof daily"
sleep 600