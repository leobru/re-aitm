#!/usr/bin/env python3
# Show the code of two АИТМ builds side by side at the addresses that
# tools/xmatch.py -n paired, to check a carried-over name by eye.
# Usage: tools/xshow.py DIR_A DIR_B NAMES.txt [N]
#   NAMES.txt - output of tools/xmatch.py -n DIR_A DIR_B; N - lines of
#   each listing (parts/NAME.adr) to show, default 6.
import re, sys

def adr(d, part):
    res = {}
    lines = open('%s/parts/%s.adr' % (d, part), encoding='utf-8').read().split('\n')
    for i, l in enumerate(lines):
        m = re.match(r'^ *([0-7]{3,5})[ :]', l)
        if m:
            res.setdefault(int(m.group(1), 8), i)
    return lines, res

def parts(d):
    res = []
    for l in open(d + '/parts.txt', encoding='utf-8'):
        if l.startswith('#') or not l.strip():
            continue
        f = l.split()
        n = 0
        for z in f[3:]:
            n += int(z[1:], 8) if z.startswith('-') else 256 if '.' in z else 1024
        res.append((f[0], int(f[2], 8), n))
    return res

def part_at(pl, a):
    for n, b, l in pl:
        if b <= a < b + l:
            return n

da, db, fn = sys.argv[1:4]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 6
pa = parts(da)
cache = {}
def get(d, p):
    if (d, p) not in cache:
        cache[(d, p)] = adr(d, p)
    return cache[(d, p)]
for l in open(fn, encoding='utf-8'):
    m = re.match(r" '(\d+)': '(\S+)',\s*# (\S+) (\S+)(.*)", l)
    if not m:
        continue
    a, name, pb, b, q = m.groups()
    a = int(a, 8); b = int(b.rstrip('п'), 8)
    print('=== %05o %s  <- %s %05o%s' % (a, name, pb, b, q))
    A = get(da, part_at(pa, a)); B = get(db, pb)
    ia = A[1].get(a); ib = B[1].get(b)
    la = A[0][ia:ia + N] if ia is not None else ['?']
    lb = B[0][ib:ib + N] if ib is not None else ['?']
    for x, y in zip(la + [''] * N, lb + [''] * N):
        if x or y:
            print('%-60s| %s' % (x[:60].replace('\t', ' '), y[:70].replace('\t', ' ')))
