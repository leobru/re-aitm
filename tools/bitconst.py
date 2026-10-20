#!/usr/bin/env python3
"""Single-bit data words of the parts and how the code uses them, for
naming bit masks Еn (БЭСМ-6: Е48 - the highest bit, Е1 - the lowest).

Usage: tools/bitconst.py [-m]

For each labelled data word of parts/*.be whose value (from
parts/PART.be.lst) is one bit: part, address, label, bit Еn, the
operations that address it in all parts with counts.  Words written by
ЗП (working cells) are left out.  -m: only those whose every use is И,
ИЛИ or НТЖ (masks); they print as 'ааааа ЕN' lines for tools/addnames.py
grouped by '# PART'.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASK = {'и', 'или', 'нтж'}


def main():
    only = '-m' in sys.argv
    words = []                      # (part, address, label, bit)
    for f in sorted(glob.glob(os.path.join(ROOT, 'parts', '*.be.lst'))):
        p = os.path.basename(f)[:-7]
        for l in open(f, encoding='utf-8', errors='replace'):
            m = re.match(r'\s*([0-7]{5})\s+([0-7]{16})\s+\d{4}\s+\d{4}\s+(\S+)\s', l[24:])
            if m:
                v = int(m.group(2), 8)
                if v and v & (v - 1) == 0:
                    words.append((p, m.group(1), m.group(3), v.bit_length()))
    uses = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'parts', '*.be'))):
        for l in open(f, encoding='utf-8'):
            f2 = l.rstrip('\n').split('\t')
            if l.startswith('*') or len(f2) < 3 or f2[1] in ('внеш', 'вход'):
                continue
            for n in re.findall(r'(?<![А-ЯA-Z0-9])([А-ЯA-Z][А-ЯA-Z0-9]*)(?![А-ЯA-Z0-9(])|'
                                r'(?<![А-ЯA-Z0-9])([А-ЯA-Z][А-ЯA-Z0-9]*)(?=\()', f2[2]):
                n = n[0] or n[1]
                uses.setdefault(n, {}).setdefault(f2[1], 0)
                uses[n][f2[1]] += 1
    last = None
    for p, a, n, b in words:
        u = uses.get(n, {})
        if not u or 'зп' in u:
            continue
        if only:
            if set(u) <= MASK:
                if p != last:
                    print('# %s' % p)
                    last = p
                print('%s Е%d %s' % (a, b, n))
            continue
        print('%-5s %s %-6s Е%-2d %s' % (p, a, n, b,
              ' '.join('%s:%d' % kv for kv in sorted(u.items()))))


if __name__ == '__main__':
    main()
