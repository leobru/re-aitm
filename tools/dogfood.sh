#!/bin/sh
# Dogfooding: АИТМ 2148, rewritten in ITM autocode (itm/*.itm, made by
# tools/be2itm.py from parts/*.be), translated by АИТМ itself into a module
# library, linked by the BEMSH loader zagr and stored as АИТМЗ.
# Usage: tools/dogfood.sh   (in the repository root; needs itm/*.itm,
#        traces/zagr.2148 and traces/z14mock.2148 - see make dogfood)
# One job per module (tools/itmdeck.py; the text goes to the drum through
# the translator's own entry 04667), each on the volume of the previous;
# the last translates АИТМ (aitm0 + aitm6) with key
# РАГК,АИТМЗ:АИТМ(ФАЗ1А+ФАЗ1Б/ФАЗ2А+ФАЗ2Б/ФАЗ2В)! and zagr stores the
# linked program.  traces/dog/cmp.txt: the stored root and segments
# against the parts (tools/itmcmp.py) and the volume against the one
# tools/itmload.py --store makes from the same library (tools/volcmp.py).
set -e
T=traces/dog
mkdir -p $T
prev=
k=РАНГК
for pm in f1a:ФАЗ1А f1b:ФАЗ1Б f2a:ФАЗ2А f2b:ФАЗ2Б f2c:ФАЗ2В; do
    p=${pm%%:*}; m=${pm##*:}
    tools/itmdeck.py itm/$p.itm "$k,$m!" --tape '67(2222-ЗП)' -o $T/$p.b6
    VOLIN=$prev VOLOUT=$T/$p.vol tools/dispakrun.sh $T/$p.b6 $T/$p.txt
    if grep -q ОШИБКА $T/$p.txt; then echo "$p: ошибки трансляции"; exit 1; fi
    prev=$T/$p.vol; k=РАГК
done
KEY='АИТМЗ:АИТМ(ФАЗ1А+ФАЗ1Б/ФАЗ2А+ФАЗ2Б/ФАЗ2В)!'
tools/itmdeck.py itm/aitm.itm "РАГК,$KEY" --tape '67(2222-ЗП)' -o $T/aitm.b6
VOL2148=traces/zagr.2148 VOLIN=$prev VOLOUT=$T/aitm.vol tools/dispakrun.sh $T/aitm.b6 $T/aitm.txt
grep 'ЗАГР: ЗАПИСАНО' $T/aitm.txt
# reference: the same job with the probe in zone 0414 (no linking), then itmload
VOL2148=traces/z14mock.2148 VOLIN=$prev VOLOUT=$T/pre.vol tools/dispakrun.sh $T/aitm.b6 $T/pre.txt
tools/itmload.py "РАК,${KEY#*:}" $T/pre.vol --store АИТМЗ $T/ref.vol > /dev/null
{ tools/itmcmp.py stored $T/aitm.vol АИТМЗ; tools/volcmp.py $T/aitm.vol $T/ref.vol; } > $T/cmp.txt
cat $T/cmp.txt
