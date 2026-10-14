#!/usr/bin/env python3
"""Search dispak disk images for AITM libraries and related code.

Usage: tools/libscan.py [-v] 2048 2148 2248 ...   (names or paths)

For every zone reports:
  MODCAT  a module-library catalogue (volume 067, LIBRARY.md): pairs of an
          ITM name right-justified and a descriptor (length << 32, zone in
          the low 10 bits) with increasing zones, ended by a zero name and
          the free zone;
  TEXTCAT a text-library catalogue (МЛ30): 0716 = 010000 + n, ITM names at
          016..016+n;
  ITMTEXT zones mostly of ITM text with autocode punctuation (; , :);
  U67     Э70 information words for unit 067 (as 05747/05750/05751 in f2a);
  AITM    zones like a 2148 zone of the translator (0406-0414): the zone
          and shift with the most equal words (at least 100 of them).
"""
import os
import re
import struct
import sys
from collections import Counter

ZONE = 8256
ZONE_OFFSET = 4
M48 = (1 << 48) - 1
PATH = os.environ.get('BESM6_PATH', '/usr/local/share/besm6')
HERE = os.path.dirname(os.path.abspath(__file__))

ITM = {}
for l in open(os.path.join(HERE, '..', 'itm-encoding.txt'), encoding='utf-8'):
    m = re.match(r'([0-7]{3})  (\S+)', l)
    if m:
        ITM[int(m.group(1), 8)] = m.group(2).replace('<space>', ' ').replace('<space2>', ' ')
LETTER = {c for c in ITM if c >= 0o200}
SEMI, COMMA, COLON = 0o45, 0o46, 0o56


def zones(f):
    b = open(f, 'rb').read()
    for z in range(ZONE_OFFSET, len(b) // ZONE):
        yield z - ZONE_OFFSET, [x & M48 for x in
                                struct.unpack('<1032Q', b[z * ZONE:(z + 1) * ZONE])[8:]]


def text(w):
    return ''.join(ITM.get(c, '?') for c in w.to_bytes(6, 'big'))


def is_name(w):
    """ITM name right-justified: leading zero bytes, then letters/digits."""
    bs = w.to_bytes(6, 'big').lstrip(b'\0')
    return (0 < len(bs) <= 6 and bs[0] in LETTER
            and all(c in LETTER or c <= 0o11 for c in bs))


def modcat(d):
    out, last = [], 0
    for i in range(0, 1024, 2):
        name, desc = d[i], d[i + 1]
        if name == 0:
            return out if out and last < desc < 4000 else None
        if name != M48 and not is_name(name):
            return None
        z, ln = desc & 0o1777, (desc >> 32) & 0o77777
        if z <= last or not ln or desc & 0o1776000 & 0o77777777:
            return None
        out.append((text(name).lstrip('0') if name != M48 else '(-1)', ln, z))
        last = z
    return None


def textcat(d):
    n = d[0o716] - 0o10000
    if not 0 <= n < 0o700:
        return None
    names = d[0o16:0o16 + n + 1]
    descs = d[0o720:0o720 + n + 1]
    if not all(w == 0 or is_name(w) for w in names):
        return None
    if not all(0 < x & 0o7777 < 4000 for x in descs):
        return None
    return [(text(w).lstrip('0') or '-', '%o' % (x & 0o7777))
            for w, x in zip(names, descs)]


def itmtext(d):
    bs = b''.join(w.to_bytes(6, 'big') for w in d)
    valid = sum(c in ITM for c in bs)
    letters = sum(c in LETTER for c in bs)
    punct = sum(c in (SEMI, COMMA, COLON) for c in bs)
    if valid > 0.95 * len(bs) and letters > 0.2 * len(bs) and punct > 20:
        return ''.join(ITM.get(c, '?') for c in bs[:120])
    return None


def u67(d):
    return [i for i, w in enumerate(d)
            if w & 0o77777777 == 0o670000 and (w >> 24) & 0o7777 and w >> 44 == 0]


def main():
    args = sys.argv[1:]
    verbose = args and args[0] == '-v'
    if verbose:
        args = args[1:]
    ref = {}
    for z, d in zones(os.path.join(PATH, '2148')):
        if 0o406 <= z <= 0o414:
            for i, w in enumerate(d):
                if w >> 24 and w & 0o77777777 and w != M48:
                    ref.setdefault(w, []).append((z, i))
    for v in args:
        f = v if os.path.exists(v) else os.path.join(PATH, v)
        print('==', v)
        for z, d in zones(f):
            r = []
            c = Counter((rz, ri - i) for i, w in enumerate(d)
                        for rz, ri in ref.get(w, [])[:10])
            if c and c.most_common(1)[0][1] >= 100:
                (rz, sh), k = c.most_common(1)[0]
                r.append('AITM 2148:%04o%+05o, %d words' % (rz, sh, k))
            c = modcat(d)
            if c:
                r.append('MODCAT ' + ' '.join('%s:%o/%o' % e for e in c))
            c = textcat(d)
            if c:
                r.append('TEXTCAT ' + ' '.join('%s:%s' % e for e in c))
            t = itmtext(d)
            if t:
                r.append('ITMTEXT ' + t if verbose else 'ITMTEXT')
            u = u67(d)
            if u:
                r.append('U67 ' + ' '.join('%04o:%016o' % (i, d[i]) for i in u))
            for x in r:
                print('%04o  %s' % (z, x))


main()
