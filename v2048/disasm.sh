#!/bin/sh
# Disassembly of the ITM autocode translator, volume 2048 zones 0055-0060.
#
# aitm.bin   - zones 055..060 dumped with: besmtool dump 2048 --start=055 --length=4
#              loaded at 0 (zone 055 -> 0, 056 -> 02000, 057 -> 04000, 060 -> 06000),
#              entry 010 with A = 0, M2 = 0.
# aitm.trace - addresses executed between the bootstrap and the handover to the
#              compiled program, collected by cov.sh from aitm-2048.b6 and tests/*.b6.
set -e
cd "$(dirname "$0")"
DIS=${DISBESM6:-/usr/local/bin/disbesm6}
exec "$DIS" -b -a0 -e10 --trace=aitm.trace aitm.bin > aitm.lst
