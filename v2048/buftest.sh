#!/bin/sh
# Check that the initial contents of the buffer 07000-07777 (zone 0060,
# sectors 2-3, outside the part) do not matter: a copy of volume 2048 gets
# the reassembled part (parts/aitm.new, 0-06777; run "make check" first)
# and zeros in 07000-07777, and all jobs of the Makefile are run on it; the
# printouts, coverage and events must be the same as with the original
# volume (traces/ - run "make traces" first).
# Usage: ./buftest.sh   (in v2048/; work directory $W, default /tmp/buftest)
set -e
here=$(cd "$(dirname "$0")" && pwd)
W=${W:-/tmp/buftest}
path=${BESM6_PATH:-/usr/local/share/besm6}
rm -rf "$W"; mkdir -p "$W/v2048/parts"
ln -s "$here/../tools" "$W/tools"
ln -s "$here/../macros.be" "$W/macros.be"
ln -s "$here/../jobs" "$W/jobs"
cd "$here"
cp -a Makefile parts.txt jobs zones "$W/v2048/"
# Volume 2048: zone 0060 (06000-07777) from parts/aitm.new, then zeros
python3 - "$path/2048" parts/aitm.new "$W/2048" <<'EOF'
import struct, sys
vol = bytearray(open(sys.argv[1], 'rb').read())
new = open(sys.argv[2], 'rb').read()
M48 = (1 << 48) - 1
base = (0o60 + 4) * 8256 + 8 * 8          # zone 0060, after 8 control words
for a in range(0o6000, 0o10000):
    w = int.from_bytes(new[a * 6:a * 6 + 6], 'big') if a * 6 < len(new) else 0
    off = base + (a - 0o6000) * 8
    old = struct.unpack_from('<Q', vol, off)[0]
    struct.pack_into('<Q', vol, off, (old & ~M48) | w)
open(sys.argv[3], 'wb').write(vol)
EOF
cmp -l "$path/2048" "$W/2048" | wc -l | sed 's/^/байтов тома изменено: /'
cd "$W/v2048"
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
