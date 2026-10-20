#!/usr/bin/env python3
"""Overview of the generated D/G labels of the parts, for naming them.

Usage: tools/labinfo.py PART [PREFIX]

For each label Dnnnnn/Gnnnnn defined in parts/PART.be (PREFIX limits the
addresses, e.g. 003): its value from parts/PART.be.lst (data words also
with the ITM glyph of the low byte), the parts that use it and how many
times, and the first few instructions that use it.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAB = re.compile(r'\b([DG][0-7]{5})\b')


def glyphs():
    g = {}
    for l in open(os.path.join(ROOT, 'itm-encoding.txt'), encoding='utf-8'):
        if l[:1].isdigit():
            g[int(l[:3], 8)] = l[5:22].strip()
    return g


def main():
    part = sys.argv[1]
    pre = sys.argv[2] if len(sys.argv) > 2 else ''
    g = glyphs()
    val = {}
    for l in open(os.path.join(ROOT, 'parts', part + '.be.lst'),
                  encoding='utf-8', errors='replace'):
        m = re.match(r'\s*(\d{5})\s+(\d{16})\s+\d{4}\s+\d{4}\s+([DG]\d{5})\s', l[24:])
        if m:
            val[m.group(3)] = m.group(2)
    uses = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'parts', '*.be'))):
        p = os.path.basename(f)[:-3]
        for l in open(f, encoding='utf-8'):
            if l.startswith('*') or '\tвнеш\t' in l or '\tвход\t' in l:
                continue
            f2 = l.rstrip('\n').split('\t')
            for n in LAB.findall('\t'.join(f2[1:])):
                uses.setdefault(n, []).append((p, ' '.join(f2[1:3])))
    for l in open(os.path.join(ROOT, 'parts', part + '.be'), encoding='utf-8'):
        n = l.split('\t')[0]
        if not LAB.fullmatch(n) or not n[1:].startswith(pre):
            continue
        u = uses.get(n, [])
        by = {}
        for p, _ in u:
            by[p] = by.get(p, 0) + 1
        v = val.get(n, '')
        gl = ' %r' % g[int(v, 8) & 0o377] if v and int(v, 8) & 0o377 in g else ''
        print('%s %s%s | %s | %s' % (n, v, gl,
              ' '.join('%s:%d' % kv for kv in by.items()),
              '; '.join(sorted({i for _, i in u})[:6])))


if __name__ == '__main__':
    main()
