#!/bin/sh
# Stress test of the loader zagr (zone 0414): 1400 entry names, a
# library module longer than 4 zones (tools/zstress.py).
# Usage: tools/zstress.sh   (in the repository root; needs traces/zagr.2148
#        and traces/z14mock.2148 - see make zstress)
# СА and СБ are translated into a library, then the main module ГЛС with
# key Р and the list (СА/СБ):
# - run: the memory zagr builds against tools/itmload.py (tools/memcmp.py);
# - store (ЗСТ:): the volume against itmload --store (tools/volcmp.py);
# - НЕТ: a name nobody has gives «ЗАГР: НЕТ ИМЕНИ».
# traces/zst/cmp.txt holds the results; exit status 1 on a difference.
set -e
T=traces/zst
mkdir -p $T
rm -f $T/cmp.txt
tools/zstress.py $T
deck() { tools/itmdeck.py $T/$1.itm "$2" --tape '67(2222-ЗП)' -o $T/$3.b6; }
deck СА 'РАНГК,СА!' sa
VOLOUT=$T/sa.vol tools/dispakrun.sh $T/sa.b6 $T/sa.txt
deck СБ 'РАГК,СБ!' sb
VOLIN=$T/sa.vol VOLOUT=$T/lib.vol tools/dispakrun.sh $T/sb.b6 $T/sb.txt
if grep -q ОШИБКА $T/sa.txt $T/sb.txt; then echo 'ошибки трансляции'; exit 1; fi
# reference library with ГЛС in it: the main translated without the loader
deck ГЛС 'РАГК,ГЛС(СА/СБ)!' run
VOL2148=traces/z14mock.2148 VOLIN=$T/lib.vol VOLOUT=$T/pre.vol tools/dispakrun.sh $T/run.b6 $T/pre.txt
tools/itmload.py 'РАК,ГЛС(СА/СБ)!' $T/pre.vol -o $T/ref.b6 > /dev/null
VOL2148=traces/zagr.2148 VOLIN=$T/lib.vol tools/memcmp.py $T/run.b6 $T/ref.b6 > $T/cmp.txt
deck ГЛС 'РАГК,ЗСТ:ГЛС(СА/СБ)!' st
VOL2148=traces/zagr.2148 VOLIN=$T/lib.vol VOLOUT=$T/st.vol tools/dispakrun.sh $T/st.b6 $T/st.txt
grep 'ЗАГР: ЗАПИСАНО' $T/st.txt
tools/itmload.py 'РАК,ГЛС(СА/СБ)!' $T/pre.vol --store ЗСТ $T/ref.vol > /dev/null
tools/volcmp.py $T/st.vol $T/ref.vol >> $T/cmp.txt
deck НЕТ 'РАГК,НЕТ(СА)!' net
VOL2148=traces/zagr.2148 VOLIN=$T/lib.vol tools/dispakrun.sh $T/net.b6 $T/net.txt
grep 'ЗАГР: НЕТ ИМЕНИ' $T/net.txt >> $T/cmp.txt
cat $T/cmp.txt
