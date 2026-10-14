#!/usr/bin/env python3
# Coverage of the parts by job: words executed (traces/JOB.cov) out of the
# words of each part, and for every job the words no other job reaches.
# Usage: tools/covgain.py [-v] [covdir ...]   (default: traces/*.cov)
#   -v      list the words only that job reaches, as address ranges.
#   covdir  a coverage directory outside traces/ (a trial job) is compared
#           with all of traces/*.cov.
import glob, os, sys


def sectors(spec):
    z, _, s = spec.partition('.')
    return [(z, int(s))] if s else [(z, i) for i in range(4)]


def parts():
    res = []
    for l in open('parts.txt'):
        if l.startswith('#') or not l.strip():
            continue
        name, mod, addr, *specs = l.split()
        res.append((name, int(addr, 8), [x for s in specs for x in sectors(s)]))
    return res


def cov(d, secs):
    res = set()
    for z, s in secs:
        fn = '%s/%s.%d.cov' % (d, z, s)
        if os.path.exists(fn):
            res.update(int(x.split(':')[0], 8) for x in open(fn))
    return res


def ranges(s):
    s = sorted(s); out = []
    for a in s:
        if out and a == out[-1][1] + 1:
            out[-1][1] = a
        else:
            out.append([a, a])
    return ' '.join('%05o' % a if a == b else '%05o-%05o' % (a, b) for a, b in out)


verbose = '-v' in sys.argv
args = [a.rstrip('/') for a in sys.argv[1:] if a != '-v']
base = sorted(glob.glob('traces/*.cov'))
dirs = args or base
P = parts()
print('%-14s' % 'задание' + ''.join('%8s' % n for n, a, s in P))
print('%-14s' % 'слов' + ''.join('%8d' % (len(s) * 256) for n, a, s in P))
total = {n: set() for n, a, s in P}
for d in dirs:
    others = [x for x in base if x != d]
    row = '%-14s' % os.path.basename(d)[:-4]
    only = []
    for n, a, secs in P:
        c = cov(d, secs)
        o = set().union(*[cov(x, secs) for x in others]) if others else set()
        total[n] |= c
        new = c - o
        row += '%8s' % ('%d+%d' % (len(c), len(new)) if new else len(c) or '-')
        if verbose and new:
            only.append('  %s: %s' % (n, ranges(new)))
    print(row)
    for l in only:
        print(l)
if not args:
    print('%-14s' % 'всего' + ''.join('%8d' % len(total[n]) for n, a, s in P))
