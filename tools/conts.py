#!/usr/bin/env python3
# Code that disbesm6 does not reach, candidates for ENTRIES in notes/NAME.py:
#  - continuations: "УИА адрес(Мr)" where Мr is a return register (some
#    routine of the parts returns by ПБ (Мr)) - the callee returns to the
#    address through Мr (the resident 00223, 00225, 00411 ... do so);
#  - jumps and calls with a literal address 'ааааа' into another part.
# Prints the target addresses that are still undecoded (КОНД/КОНК/ПАМ) in
# parts/NAME.adr with the places that lead there.
# Usage: tools/conts.py NAME ...      (all parts of parts.txt are read)
import re, sys

JUMPS = ('пб', 'пв', 'пвл', 'по', 'пе', 'пио', 'пино', 'цикл')


def load(name):
    kind = {}                   # address -> 'code' / 'data'
    seq = []                    # (address, op, operand) in order
    cur = None
    for l in open('parts/%s.adr' % name).read().split('\n'):
        f = l.split('\t')
        if len(f) < 4:
            continue
        new = re.match(r'^ *([0-7]+)[ :]', f[0]) if f[0][:5].strip() else None
        if new:
            cur = int(new.group(1), 8)
            kind[cur] = 'data' if f[2] in ('конд', 'конк', 'пам') else 'code'
        if cur is not None:
            seq.append((cur, f[2], f[3]))
    return kind, seq


# z14 (a work zone over the resident) is not a target
parts = [l.split()[0] for l in open('parts.txt')
         if l.strip() and not l.startswith('#') and l.split()[0] != 'z14']
P = {p: load(p) for p in parts}
retregs = set()
for kind, seq in P.values():
    for a, op, arg in seq:
        m = re.fullmatch(r'\d*\((М\d+)\)', arg)
        if op == 'пб' and m:
            retregs.add(m.group(1))
res = {}
for p, (kind, seq) in P.items():
    for i, (a, op, arg) in enumerate(seq):
        if op == 'уиа':
            # (ПБ 01424/01430 - the error routine: Мr holds the error code)
            nxt = [x for x in seq[i + 1:i + 5]]
            if any(re.fullmatch(r"'14(24|30)'|G014(24|30)", x[2]) for x in nxt):
                continue
            m = re.match(r"(?:[GD]([0-7]{5})([+-]\d+)?|'([0-7]+)')\((М\d+)\)$", arg)
            if not m or m.group(4) not in retregs:
                continue
            # a ПВ by another register right after: Мr is a parameter
            if nxt and nxt[0][1] in ('пв', 'пвл') and not nxt[0][2].endswith('(%s)' % m.group(4)):
                continue
            t = int(m.group(1), 8) + int(m.group(2) or 0) if m.group(1) else int(m.group(3), 8)
            if P[p][0].get(t) == 'data':
                res.setdefault((p, t), set()).add('%s:%05o' % (p, a))
        elif op in JUMPS:
            m = re.match(r"'([0-7]{4,5})'(\(М\d+\))?$", arg)
            if not m:
                continue
            t = int(m.group(1), 8)
            for q, (k2, s2) in P.items():
                if q != p and k2.get(t) == 'data':
                    res.setdefault((q, t), set()).add('%s:%05o' % (p, a))
want = set(sys.argv[1:]) or set(parts)
for (q, t) in sorted(res):
    if q in want:
        print('%s %05o  из %s' % (q, t, ' '.join(sorted(res[(q, t)]))))
