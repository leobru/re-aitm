#!/bin/sh
# Check that the initial contents of the buffers 07030-07777 do not matter:
# build the translator from parts/aitm.be with every word there replaced by
# ПАМ (zeros), put it into a copy of volume 2048 and run all jobs of the
# Makefile on it; the printouts, coverage and events must be the same as
# with the original volume (traces/ - run "make traces" first).
# Usage: ./buftest.sh [FROM]   (in v2048/; FROM - octal, default 07030;
#        work directory $W, default /tmp/buftest)
set -e
here=$(cd "$(dirname "$0")" && pwd)
FROM=${1:-07030}
W=${W:-/tmp/buftest}
path=${BESM6_PATH:-/usr/local/share/besm6}
rm -rf "$W"; mkdir -p "$W/v2048/parts"
ln -s "$here/../tools" "$W/tools"
ln -s "$here/../macros.be" "$W/macros.be"
ln -s "$here/../jobs" "$W/jobs"
cd "$here"
cp -a Makefile parts.txt macros.be macros.lib 2222 jobs zones "$W/v2048/"
cp parts/aitm.bin "$W/v2048/parts/"
# The source with ПАМ: the address of each source line is taken from the
# listing (column "N ИСХ" - the line number); a line at FROM or above that
# makes words gets "ПАМ n" with its label kept.
python3 - "$FROM" parts/aitm.be parts/aitm.be.lst "$W/v2048/parts/aitm.be" <<'EOF'
import re, sys
start = int(sys.argv[1], 8)
src = open(sys.argv[2], encoding='utf-8').read().split('\n')
addr = {}
for l in open(sys.argv[3], encoding='utf-8', errors='replace'):
    m = re.match(r'^.{25}([0-7]{5}) .*?\s(\d{4})\s+(\d{4})\s', l)
    if m:
        addr.setdefault(int(m.group(3)), int(m.group(1), 8))
# only lines that make words or reserve them (not comments, not ФИНИШ,
# which the listing shows at the address of the last word)
lines = sorted(n for n in addr if len(src[n - 1].split('\t')) > 2
               and src[n - 1].split('\t')[1] not in ('', 'ФИНИШ'))
size = {}
for i, n in enumerate(lines):
    nxt = addr[lines[i + 1]] if i + 1 < len(lines) else 0o10000
    size[n] = nxt - addr[n]
out, words, last, done = [], 0, 0, False
for n, l in enumerate(src, 1):
    f = l.split('\t')
    if n in addr:
        last = addr[n]
    elif last >= start and len(f) > 2 and f[1] == 'конк' and done:
        continue                # the right half of a word already replaced
    elif last >= start and len(f) > 2 and f[1] in ('конд', 'конк', 'текст', 'пам'):
        sys.exit('строки %d нет в листинге' % n)
    done = n in addr and addr[n] >= start and len(f) > 2 and f[1] in ('конд', 'конк', 'текст', 'пам')
    if done:
        l = '%s\tпам\t%d' % (f[0], size[n])
        words += size[n]
    out.append(l)
open(sys.argv[4], 'w', encoding='utf-8').write('\n'.join(out))
print('ПАМ вместо %d слов с %05o' % (words, start))
EOF
cd "$W/v2048"
../tools/reasm.pl parts/aitm.be || true
# Volume 2048 with the rebuilt words 07000-07777 (zone 0060, sector 3)
python3 - "$path/2048" parts/aitm.new "$W/2048" <<'EOF'
import struct, sys
vol = bytearray(open(sys.argv[1], 'rb').read())
new = open(sys.argv[2], 'rb').read()
M48 = (1 << 48) - 1
base = (0o60 + 4) * 8256 + 8 * 8          # zone 0060, after 8 control words
for a in range(0o6000, 0o10000):
    w = int.from_bytes(new[a * 6:a * 6 + 6], 'big')
    off = base + (a - 0o6000) * 8
    old = struct.unpack_from('<Q', vol, off)[0]
    struct.pack_into('<Q', vol, off, (old & ~M48) | w)
open(sys.argv[3], 'wb').write(vol)
EOF
cmp -l "$path/2048" "$W/2048" | wc -l | sed 's/^/байтов тома изменено: /'
rm -rf traces
VOL2048=$W/2048 make -j8 traces > make.log 2>&1 || { tail make.log; exit 1; }
diff=0
for f in "$here"/traces/*.txt; do
    j=$(basename "$f" .txt)
    [ -f "traces/$j.txt" ] || continue
    cmp -s "$f" "traces/$j.txt" || { echo "распечатка $j отличается"; diff=1; }
    cmp -s "$here/traces/$j.ev" "traces/$j.ev" || { echo "события $j отличаются"; diff=1; }
    diff -r "$here/traces/$j.cov" "traces/$j.cov" > /dev/null || { echo "покрытие $j отличается"; diff=1; }
done
echo "заданий: $(ls traces/*.txt | wc -l)"
[ $diff = 0 ] && echo "все совпадает"
