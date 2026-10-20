#!/usr/bin/env python3
"""Uses of a label in all parts/*.be with the surrounding lines.

Usage: tools/uses.py [-n N] [-p PART] LABEL [LABEL ...]

Prints each command that has LABEL in its operand with N (default 3)
source lines before and after it (with the word address from
parts/PART.be.lst), skipping comments; -p limits the parts.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def addrs(p):
    """source line -> address of its word"""
    res, cur = {}, ''
    for l in open(os.path.join(ROOT, 'parts', p + '.be.lst'), encoding='utf-8', errors='replace'):
        a, n = l[25:30], l[55:59]
        if len(l) > 59 and l[24] == ' ' and re.fullmatch(r'[0-7]{5}', a):
            cur = a
        if n.strip().isdigit() and cur:
            res.setdefault(int(n), cur)
    return res


def main():
    args = sys.argv[1:]
    n, only = 3, None
    while args and args[0].startswith('-'):
        if args[0] == '-n':
            n = int(args[1])
        elif args[0] == '-p':
            only = args[1]
        args = args[2:]
    for lab in args:
        pat = re.compile(r'(?<![А-ЯA-Z0-9])%s(?![А-ЯA-Z0-9])' % re.escape(lab))
        for f in sorted(glob.glob(os.path.join(ROOT, 'parts', '*.be'))):
            p = os.path.basename(f)[:-3]
            if only and p != only:
                continue
            ad = addrs(p)
            src = [(i, l) for i, l in enumerate(open(f, encoding='utf-8').read().split('\n'), 1)
                   if not l.startswith('*')]
            for k, (i, l) in enumerate(src):
                fs = l.split('\t')
                if len(fs) < 3 or fs[1] in ('внеш', 'вход') or not pat.search(fs[2]):
                    continue
                print('== %s %s:%d' % (lab, p, i))
                for j, l2 in src[max(0, k - n):k + n + 1]:
                    print('%s %5s %s' % ('>' if j == i else ' ', ad.get(j, ''), l2.expandtabs(8)[:66]))


if __name__ == '__main__':
    main()
