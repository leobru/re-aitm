#!/usr/bin/env python3
"""Decode a dispak volume image used as the AITM module library (unit 067).

Usage: tools/vol.py 2222 > lib.txt

Zone 0 is the catalogue: pairs (name in ITM, right-justified; descriptor),
terminated by a zero name whose second word is the first free zone.  A
freed entry has name -1.  Descriptor (КОНВЫВ, f2a):
  bit 48 flag | image length << 32 | D05740 << 20 | first zone (01777).
Module (ВЫВМ, f2a), from the first zone on:
  word 0  image length << 33 | literals << 22 | reference records << 10
  word 1  export table words << 36   (key Р option Г)
  image of 010.., relocation scale (3 bits per half-word, ceil(len/8)
  words), literals, reference records, export table (name, 1<<45|addr).
"""
import os
import re
import struct
import sys

ZONE = 8256                     # 8 control words + 1024 data words
ZONE_OFFSET = 4
M48 = (1 << 48) - 1

ITM = {}
for l in open(os.path.join(os.path.dirname(__file__), '..', 'itm-encoding.txt'),
              encoding='utf-8'):
    m = re.match(r'([0-7]{3})  (\S+)', l)
    if m:
        ITM[int(m.group(1), 8)] = m.group(2)


def itm(w):
    return ''.join(ITM.get(c, '{%o}' % c) for c in w.to_bytes(6, 'big')).lstrip('0') or '0'


def zones(f):
    b = open(f, 'rb').read()
    return [[x & M48 for x in struct.unpack('<1032Q', b[z * ZONE:(z + 1) * ZONE])[8:]]
            for z in range(ZONE_OFFSET, len(b) // ZONE)]


def module(zs, z0):
    w = [x for z in zs[z0:] for x in z]
    n, nlit, nref = w[0] >> 33, (w[0] >> 22) & 0o3777, (w[0] >> 10) & 0o7777
    nexp = w[1] >> 36
    print('  header %016o %016o: image %o, literals %o, references %o, exports %o'
          % (w[0], w[1], n, nlit, nref, nexp))
    img, p = w[2:2 + n], 2 + n
    ns = (n + 7) // 8
    scale, p = w[p:p + ns], p + ns
    for i, x in enumerate(img):
        f = [(scale[i // 8] >> (45 - 6 * (i % 8) - 3 * h)) & 7 for h in (0, 1)]
        print('    %05o  %016o  %o%o' % (0o10 + i, x, *f))
    for name, k in (('literal', nlit), ('reference', nref)):
        for x in w[p:p + k]:
            print('    %-9s %016o' % (name, x))
        p += k
    for i in range(p, p + nexp, 2):
        print('    export %-6s %016o' % (itm(w[i]), w[i + 1]))
    return 2 + n + ns + nlit + nref + nexp


def main():
    zs = zones(sys.argv[1])
    cat = zs[0]
    for i in range(0, len(cat), 2):
        name, d = cat[i], cat[i + 1]
        if not name:
            print('end of catalogue, free zone %o' % d)
            break
        z, ln, x = d & 0o1777, (d >> 32) & 0o77777, (d >> 20) & 0o7777
        if name == M48:
            print('%03o  (freed)  %016o  zone %o, length %o' % (i, d, z, ln))
            continue
        print('%03o  %-6s  %016o  flag %o, length %o, D05740 %o, zone %o'
              % (i, itm(name), d, d >> 47, ln, x, z))
        if z < len(zs):
            module(zs, z)


main()
