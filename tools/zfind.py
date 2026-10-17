#!/usr/bin/env python3
"""Find zones on volumes that resemble given reference zones.

Usage: tools/zfind.py [-k K] [-m MIN] REFVOL ZONES TARGET...
  REFVOL  volume name or path of the reference (e.g. 2048)
  ZONES   octal zones of the reference, e.g. 55-60 or 55,56,57,60
  TARGET  volumes to scan (names in $BESM6_PATH or paths)
  -k K    window length in words (default 4)
  -m MIN  report target zones with at least MIN % of windows found
          (default 10)
Every K-word window of a target zone with at least 3 different non-zero
words is looked up among the windows of the reference zones. For each target
zone with enough hits: the share of its windows found, the reference zone
most of them come from, the median offset shift (target word - reference
word; 0 = same place in the zone) and whether the zone is identical to a
reference zone.
"""
import os
import struct
import sys
from collections import Counter

ZONE = 8256                     # 8 control words + 1024 data words
ZONE_OFFSET = 4
M48 = (1 << 48) - 1
PATH = os.environ.get('BESM6_PATH', '/usr/local/share/besm6')


def zones(name):
    f = name if os.path.exists(name) and os.sep in name else os.path.join(PATH, name)
    b = open(f, 'rb').read()
    return [[x & M48 for x in struct.unpack('<1032Q', b[z * ZONE:(z + 1) * ZONE])[8:]]
            for z in range(ZONE_OFFSET, len(b) // ZONE)]


def useful(t):
    return len(set(t) - {0}) >= 3


def zlist(s):
    out = []
    for part in s.split(','):
        a, _, b = part.partition('-')
        out += range(int(a, 8), int(b or a, 8) + 1)
    return out


args = sys.argv[1:]
K, MIN = 4, 10
while args and args[0] in ('-k', '-m'):
    o, v = args.pop(0), int(args.pop(0))
    if o == '-k':
        K = v
    else:
        MIN = v
ref, rz, targets = args[0], zlist(args[1]), args[2:]
R = zones(ref)
idx = {}
for z in rz:
    w = R[z]
    for i in range(1024 - K + 1):
        t = tuple(w[i:i + K])
        if useful(t):
            idx.setdefault(t, []).append((z, i))
refset = {z: R[z] for z in rz}
for tv in targets:
    T = zones(tv)
    for tz, w in enumerate(T):
        hits, total, src, shift = 0, 0, Counter(), []
        for i in range(1024 - K + 1):
            t = tuple(w[i:i + K])
            if not useful(t):
                continue
            total += 1
            m = idx.get(t)
            if m:
                hits += 1
                z, j = m[0]
                src[z] += 1
                shift.append(i - j)
        if total and hits * 100 >= MIN * total:
            bz = src.most_common(1)[0][0]
            sh = sorted(shift)[len(shift) // 2]
            same = [z for z, r in refset.items() if r == w]
            print('%s %04o: %3d%% of %4d windows, mostly from %s %04o, shift %+d%s' % (
                tv, tz, hits * 100 // total, total, ref, bz, sh,
                ', IDENTICAL to %s %s' % (ref, ' '.join('%04o' % z for z in same)) if same else ''))
