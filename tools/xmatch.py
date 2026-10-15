#!/usr/bin/env python3
# Align the code of two АИТМ builds with the addresses masked out, and carry
# the names of the second build over to the first.
#
# Every half-word is reduced to (register, operation, small address): the
# address is kept only when it is a number (< 0100 or a small negative
# offset), so code that was moved to other addresses or refers to moved
# cells still matches. Runs of at least K equal half-words are found and
# extended; each run gives an address delta between the builds.
#
# Usage: tools/xmatch.py [-k K] [-n] DIR_A DIR_B
#   DIR_A, DIR_B - directories with parts.txt and parts/NAME.bin (and
#                  notes/NAME.py of DIR_B for the names);
#   prints the aligned runs (address in A, part:address in B, length in
#   words) and then the NAMES of B that fall inside a run, at their A
#   address; -n prints only the names, as lines of a NAMES dict;
#   -c prints the operand addresses that correspond inside the runs (A, B,
#   how many times, the B name if any): a map of the cells.
# Example: tools/xmatch.py v2048 .
import os, re, sys

K = 8
SLACK = 3
args = sys.argv[1:]
only_names = False
cells = False
while args and args[0].startswith('-'):
    o = args.pop(0)
    if o == '-k':
        K = int(args.pop(0))
    elif o == '-n':
        only_names = True
    elif o == '-c':
        cells = True


def parts(d):
    res = []
    for l in open(os.path.join(d, 'parts.txt'), encoding='utf-8'):
        if l.startswith('#') or not l.strip():
            continue
        name, mod, addr = l.split()[:3]
        b = open(os.path.join(d, 'parts', name + '.bin'), 'rb').read()
        res.append((name, int(addr, 8), [int.from_bytes(b[i:i + 6], 'big')
                                          for i in range(0, len(b), 6)]))
    return res


def token(h):
    reg = h >> 20
    if h & (1 << 19):
        op, addr = (h >> 15) & 0o37, h & 0o77777
    else:
        op, addr = (h >> 12) & 0o177, h & 0o7777
        if op & 0o100:
            addr |= 0o70000
        op &= 0o77
    keep = addr < 0o100 or addr > 0o77700
    return (reg, op, addr if keep else None)


def operand(h):
    if h & (1 << 19):
        return h & 0o77777
    return h & 0o7777 | (0o70000 if h & (1 << 18) else 0)


def halves(p):
    name, base, words = p
    res = []
    for i, w in enumerate(words):
        a = base + i
        if base == 0 and i == 0:
            w = 0                           # zone marker, not memory
        res.append((a, 0, token(w >> 24), operand(w >> 24)))
        res.append((a, 1, token(w & 0xffffff), operand(w & 0xffffff)))
    return res


A = [h for p in parts(args[0]) for h in halves(p)]
B = []
bpart = {}
for p in parts(args[1]):
    for h in halves(p):
        bpart[len(B)] = p[0]
        B.append(h)
# a run must not cross from one part of B into another
def same_part(j, n):
    return bpart[j] == bpart[j + n - 1]

zero = (0, 0, 0)
index = {}
for j in range(len(B) - K + 1):
    key = tuple(h[2] for h in B[j:j + K])
    if sum(t == zero for t in key) > K // 2:
        continue                            # runs of zeros match anything
    if same_part(j, K):
        index.setdefault(key, []).append(j)

runs = []                                   # (i in A, j in B, length)
i = 0
while i <= len(A) - K:
    key = tuple(h[2] for h in A[i:i + K])
    cands = index.get(key, [])
    best = None
    for j in cands:
        n = K
        # extend while equal, inside one part of B and with no gap in A
        while i + n < len(A) and j + n < len(B) and A[i + n][2] == B[j + n][2] \
                and same_part(j, n + 1) and A[i + n][0] - A[i + n - 1][0] in (0, 1):
            n += 1
        if best is None or n > best[2]:
            best = (i, j, n)
    if best and len(cands) <= 4:
        runs.append(best)
        i += best[2]
    else:
        i += 1

names = {}
for p in parts(args[1]):
    fn = os.path.join(args[1], 'notes', p[0] + '.py')
    if os.path.exists(fn):
        g = {}
        exec(open(fn, encoding='utf-8').read(), g)
        for a, n in g.get('NAMES', {}).items():
            names[(p[0], a)] = n

out = []
for i, j, n in runs:
    a0, b0 = A[i], B[j]
    if a0[1] != b0[1]:
        continue                            # different half: not a copy
    if not only_names and not cells:
        print('%05o%s  %s:%05o%s  %d слов' % (a0[0], 'п' if a0[1] else '', bpart[j],
                                             b0[0], 'п' if b0[1] else '', (n + 1) // 2))
    delta = a0[0] - b0[0]
    lo, hi = b0[0], B[j + n - 1][0]
    for (pn, a), nm in names.items():
        x = int(a.rstrip('п'), 8)
        # a name up to SLACK words before the run: the entry often differs
        # in an address only
        if pn == bpart[j] and lo - SLACK <= x <= hi:
            out.append(('%05o' % (x + delta), nm, pn, a,
                        '' if x >= lo else ' (до совпадения)'))
if cells:
    from collections import Counter
    pairs = Counter()
    for i, j, n in runs:
        if A[i][1] != B[j][1]:
            continue
        for k in range(n):
            if A[i + k][2][2] is None:
                pairs[(A[i + k][3], B[j + k][3])] += 1
    allb = {int(a.rstrip('п'), 8): nm for (pn, a), nm in names.items()}
    best = {}
    for (a, b), c in pairs.items():
        best.setdefault(a, []).append((c, b))
    # A address, its most frequent B address (count of all pairs), other Bs
    for a in sorted(best):
        bs = sorted(best[a], reverse=True)
        c, b = bs[0]
        print('%05o  %05o  %3d/%-3d %-8s %s' % (a, b, c, sum(x for x, _ in bs), allb.get(b, ''),
              ' '.join('%05o' % y for _, y in bs[1:4])))
    sys.exit(0)
if not only_names:
    print()
for a, nm, pn, b, q in sorted(set(out)):
    print(" '%s': '%s',%s# %s %s%s" % (a, nm, ' ' * max(1, 12 - len(nm)), pn, b, q))
