#!/bin/sh
# Try an autocode text for coverage: make a 2048 deck, trace it and show
# the errors of the listing and the words that no job in traces/ reached.
# Usage: ./covtry.sh PROG.itm [itmjob options]   (run in v2048/)
#   The deck is written next to PROG.itm as PROG.b6; the printout, the
#   coverage and the events go to $TRY (default /tmp/covtry/PROG.*).
#   itmjob.py is the one of the itm-autocode skill ($ITMJOB to override).
set -e
src=$1; shift
name=$(basename "$src" .itm)
TRY=${TRY:-/tmp/covtry}
ITMJOB=${ITMJOB:-$HOME/.claude/skills/itm-autocode/scripts/itmjob.py}
export AITM_UNIT=40 AITM_OFFSET=0 AITM_PHYS=0 AITM_VOL=2048 AITM_FINAL=4520
mkdir -p "$TRY"
python3 "$ITMJOB" "$src" --2048 -o "${src%.itm}.b6" "$@"
rm -rf "$TRY/$name.cov"
../tools/trace.sh "${src%.itm}.b6" "$TRY/$name.txt" |
    ../tools/phases.py - "$TRY/$name.cov" > "$TRY/$name.ev"
grep -o 'ОШИБКА *[0-9]*' "$TRY/$name.txt" | sed 's/  */ /' | sort | uniq -c | tr '\n' ' '
echo
grep -a 'КОНЕЦ ЗАДАЧИ' -A1 "$TRY/$name.txt" | tail -1
python3 ../tools/covgain.py -v "$TRY/$name.cov" | tail -n +3
