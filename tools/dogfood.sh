#!/bin/sh
# Dogfooding: АИТМ 2148, rewritten in ITM autocode (itm/*.itm, made by
# tools/be2itm.py from parts/*.be), translated by АИТМ itself into a module
# library, linked by the BEMSH loader zagr and stored as АИТМЗ.
# Usage: tools/dogfood.sh   (in the repository root; needs itm/*.itm,
#        traces/zagr.2148 and traces/z14mock.2148 - see make dogfood)
# One job per module (tools/itmdeck.py; the text goes to the drum through
# the translator's own entry 04667), each on the volume of the previous;
# the last translates АИТМ (aitm0) with key
# РАГК,АИТМЗ:АИТМ(АИТМ6+ФАЗ1А+ФАЗ1Б/ФАЗ2А+ФАЗ2Б/ФАЗ2В)! and zagr stores the
# linked program.  traces/dog/cmp.txt: the stored root and segments
# against the parts (tools/itmcmp.py) and the volume against the one
# tools/itmload.py --store makes from the same library (tools/volcmp.py);
# then the stored АИТМЗ translates and runs itm/privet.itm.
set -e
T=traces/dog
mkdir -p $T
prev=
k=РАНГК
for pm in aitm6:АИТМ6 f1a:ФАЗ1А f1b:ФАЗ1Б f2a:ФАЗ2А f2b:ФАЗ2Б f2c:ФАЗ2В; do
    p=${pm%%:*}; m=${pm##*:}
    tools/itmdeck.py itm/$p.itm "$k,$m!" --tape '67(2222-ЗП)' -o $T/$p.b6
    VOLIN=$prev VOLOUT=$T/$p.vol tools/dispakrun.sh $T/$p.b6 $T/$p.txt
    if grep -q ОШИБКА $T/$p.txt; then echo "$p: ошибки трансляции"; exit 1; fi
    prev=$T/$p.vol; k=РАГК
done
KEY='АИТМЗ:АИТМ(АИТМ6+ФАЗ1А+ФАЗ1Б/ФАЗ2А+ФАЗ2Б/ФАЗ2В)!'
tools/itmdeck.py itm/aitm.itm "РАГК,$KEY" --tape '67(2222-ЗП)' -o $T/aitm.b6
VOL2148=traces/zagr.2148 VOLIN=$prev VOLOUT=$T/aitm.vol tools/dispakrun.sh $T/aitm.b6 $T/aitm.txt
grep 'ЗАГР: ЗАПИСАНО' $T/aitm.txt
# reference: the same job with the probe in zone 0414 (no linking), then itmload
VOL2148=traces/z14mock.2148 VOLIN=$prev VOLOUT=$T/pre.vol tools/dispakrun.sh $T/aitm.b6 $T/pre.txt
tools/itmload.py "РАК,${KEY#*:}" $T/pre.vol --store АИТМЗ $T/ref.vol > /dev/null
{ tools/itmcmp.py stored $T/aitm.vol АИТМЗ; tools/volcmp.py $T/aitm.vol $T/ref.vol; } > $T/cmp.txt
# the stored АИТМЗ at work: the deck of АИТМ with the library volume as
# ЛЕНТ 40 and the drum offset of the record (itmdeck --stored; dispak
# --725 counts it in zones): the translator reads itself from the record
# and prints for itm/privet.itm the same as from the zones of 2148
tools/itmdeck.py itm/privet.itm 'П' -o $T/privet0.b6
tools/dispakrun.sh $T/privet0.b6 $T/privet0.txt
tools/itmdeck.py itm/privet.itm 'П' --stored $T/aitm.vol АИТМЗ -o $T/privet.b6
DISPAK_OPTS=--725 VOLIN=$T/aitm.vol tools/dispakrun.sh $T/privet.b6 $T/privet.txt
grep -q 'ПРИВЕТ ВСЕМУ' $T/privet.txt
cmp -s $T/privet0.txt $T/privet.txt
echo 'АИТМЗ: «ПРИВЕТ ВСЕМУ», печать как у АИТМ 2148' >> $T/cmp.txt
cat $T/cmp.txt
