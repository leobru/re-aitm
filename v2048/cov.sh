#!/bin/sh
# usage: cov.sh deck.b6 > seeds ; coverage of translator from bootstrap (40000) to handover (00005 э70)
timeout -s KILL 60 dispak -tt -q "$1" 2>&1 >/dev/null | awk '
/^[0-7][0-7][0-7][0-7][0-7][:;] /{ a=substr($0,1,5); if(a=="40000") on=1; if(!on) next;
  if ($2=="*70" && a=="00005") exit
  if (a<"10000" && a>"00007" && !(a in s)) { s[a]=1; print a":" } }'
