#!/usr/bin/env python3
# Split a dispak instruction trace (debugger "t2") of an АИТМ run by overlay.
# Tracks which sector of the physical drum 21 (ФИЗО МБ21: ЛЕНТ 40(2148),
# drum zone N = 2148 zone 0400+N) is loaded into each 256-word sector of
# memory by Э70 (whole zones and single sectors), and attributes every
# executed user-mode address to the drum sector there.
#
# Usage: tools/phases.py trace.log|- [covdir]
#   prints the load events (where, memory <- drum sector) in order;
#   with covdir, writes covdir/ZZZZ.S.cov ("ааааа: L R" lines, disbesm6
#   --trace format; ZZZZ - zone of 2148, S - sector) for every sector that
#   had code executed in it.
import re, sys, os
from collections import defaultdict

DRUM, OFFSET = 0o21, 0o400
sect = {}                       # memory sector (addr >> 8) -> (zone, s) or None
cov = defaultdict(lambda: defaultdict(set))
events = []
prev = None
src = sys.stdin if sys.argv[1] == '-' else open(sys.argv[1], errors='replace')
for l in src:
    m = re.match(r'^([0-7]{5})([:;]) (\S+)', l)
    if not m:
        continue
    addr = int(m.group(1), 8)
    if m.group(2) != ':':
        prev = None
        continue
    zs = sect.get(addr >> 8)
    half = 'R' if prev == addr else 'L'
    prev = addr
    if zs is not None:
        cov[zs][addr].add(half)
    if m.group(3) != '*70':
        continue
    w = re.search(r'\(=([0-7]{16})\)', l)
    if not w:
        continue
    w = int(w.group(1), 8)
    l, r = w >> 24, w & 0xffffff
    lreg, lop, laddr = l >> 20, (l >> 12) & 0o177, l & 0o7777
    rop, raddr = (r >> 12) & 0o177, r & 0o7777
    rd, phys = lop & 0o10, lop & 4
    page = (laddr & 0o3700) << 4
    unit = rop
    zone = raddr & 0o37 if unit < 0o30 or unit >= 0o70 else raddr & 0o7777
    ours = unit == DRUM and phys
    name = ('%04o' % (zone + OFFSET)) if ours else ('%s%02o:%o' % ('P' if phys else 'u', unit, zone))
    if lreg & 8:
        s = (raddr >> 6) & 3
        dst = page + (laddr & 3) * 256
        what = ['%s.%d' % (name, s)]
        if rd:
            sect[dst >> 8] = (zone + OFFSET, s) if ours else None
    else:
        dst = page
        what = [name]
        if rd:
            for s in range(4):
                sect[(dst >> 8) + s] = (zone + OFFSET, s) if ours else None
    events.append('%05o: %06o %s %s' % (addr, dst, '<-' if rd else '->', what[0]))
print('\n'.join(events))
if len(sys.argv) > 2:
    os.makedirs(sys.argv[2], exist_ok=True)
    for (z, s), a in sorted(cov.items()):
        with open(os.path.join(sys.argv[2], '%04o.%d.cov' % (z, s)), 'w') as f:
            for x in sorted(a):
                f.write('%05o: %s\n' % (x, ''.join(sorted(a[x]))))
        print('2148:%04o.%d: %d адресов' % (z, s, len(a)), file=sys.stderr)
