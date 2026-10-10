#!/bin/bash
printf '\e[1mnode logs\e[0m  docker logs -f demo-home demo-two | grep -E "Error|txs"\n'
(docker logs -n 0 -f demo-home 2>&1 | grep --line-buffered -E "Error response|Sealed block.*txs +[1-9]" | sed -u -e 's/\x1b\[[0-9;]*m//g' -e 's/^[0-9]* [A-Za-z]* //' -e 's/^/home /' | fold -s -w 78) &
docker logs -n 0 -f demo-two 2>&1 | grep --line-buffered -E "Error response|Blocks " | sed -u -e 's/\x1b\[[0-9;]*m//g' -e 's/^[0-9]* [A-Za-z]* //' -e 's/ MGas .*|  */ MGas | /' -e 's/| calls.*//' -e 's/^/two  /' | fold -s -w 78
