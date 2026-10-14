#!/bin/sh
# Disassembly of the ITM autocode translator, volume 2148 (= 2248), zones 0406-0414.
# The physical drum of the deck is ЛЕНТ 40(2148) with offset 0400, so "drum zone N" = disk zone 0400+N.
#
# phase1.bin - memory 0-06777 right after the loader at 06770:
#              0406 -> 0, 0407 -> 02000, 0410 -> 04000, 0411 sectors 0-1 -> 06000-06777.
# phase2.bin - same after the overlay swap done at 04013/01607:
#              0412 -> 04000-05777, 0407 sector 1 -> 06000-06377.
# phaseN.trace - addresses executed while that overlay was resident (ovtrack.py over the test decks).
# phaseN.sym - symbol tables; type M marks words holding ITM-encoded text.
set -e
cd "$(dirname "$0")"
DIS=${DISBESM6:-/usr/local/bin/disbesm6}
"$DIS" -b -a0 -e10 --trace=phase1.trace -nphase1.sym phase1.bin > phase1.lst
"$DIS" -b -a0 -e10 --trace=phase2.trace -nphase2.sym phase2.bin > phase2.lst
