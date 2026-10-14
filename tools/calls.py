#!/usr/bin/env python3
# Subroutine calls (ПВ, vjm) in full dispak traces of АИТМ runs
# (tools/trace.sh job.b6 > traces/JOB.t2), attributed to the parts of
# parts.txt by the drum sectors loaded with Э70 (as tools/phases.py).
# Usage: tools/calls.py traces/JOB.t2 ...
# Prints for every called address: part, number of calls, the index
# register of the ПВ, the callers (part:address) and the exits - the last
# instruction before control came back to the word after the call (or
# "+n" - the return went n words further).
import re, sys
from collections import defaultdict

DRUM, OFFSET = 0o21, 0o400
part_of = {}                            # (zone, sector) -> (name, base addr)
for l in open('parts.txt'):
    if l.startswith('#') or not l.strip():
        continue
    name, mod, addr, *specs = l.split()
    a = int(addr, 8)
    for spec in specs:
        z, _, s = spec.partition('.')
        for sec in ([int(s)] if s else range(4)):
            part_of[(int(z, 8), sec)] = name

calls = defaultdict(int)
callers = defaultdict(set)
regs = defaultdict(set)
exits = defaultdict(lambda: defaultdict(int))
for fn in sys.argv[1:]:
    sect = {}
    stack = []                          # (return address, target key)
    pend = None
    prev = None
    for l in open(fn, errors='replace'):
        m = re.match(r'^([0-7]{5})([:;]) (\S+)\s*(\S*)', l)
        if not m:
            continue
        if m.group(2) != ':':
            continue
        pc = int(m.group(1), 8)
        op, arg = m.group(3), m.group(4)
        here = sect.get(pc >> 8, '?')
        if pend is not None:
            key = (here, pc)
            calls[key] += 1
            callers[key].add(pend[1])
            regs[key].add(pend[2])
            stack.append((pend[0], key))
            if len(stack) > 64:
                del stack[0]
            pend = None
        # a return: control at a word after a pending call
        for k in range(len(stack) - 1, max(-1, len(stack) - 8), -1):
            ret, key = stack[k]
            if ret <= pc <= ret + 3 and prev and prev[1] == 'uj':
                d = pc - ret
                exits[key]['%05o%s' % (prev[0], '+%d' % d if d else '')] += 1
                del stack[k:]
                break
        if op == 'vjm':
            r = re.search(r'\((\d+)\)', arg)
            pend = (pc + 1, '%s:%05o' % (here, pc), r.group(1) if r else '0')
        if op == '*70':
            w = re.search(r'\(=([0-7]{16})\)', l)
            if w:
                w = int(w.group(1), 8)
                lw, rw = w >> 24, w & 0xffffff
                lreg, lop, laddr = lw >> 20, (lw >> 12) & 0o177, lw & 0o7777
                unit, raddr = (rw >> 12) & 0o177, rw & 0o7777
                if lop & 0o10:
                    page = (laddr & 0o3700) << 4
                    zone = raddr & 0o37
                    ours = unit == DRUM and lop & 4
                    if lreg & 8:
                        s = (raddr >> 6) & 3
                        dst = page + (laddr & 3) * 256
                        sect[dst >> 8] = part_of.get((zone + OFFSET, s), '?') if ours else '?'
                    else:
                        for s in range(4):
                            sect[(page >> 8) + s] = part_of.get((zone + OFFSET, s), '?') if ours else '?'
        prev = (pc, op)

for key in sorted(calls, key=lambda k: (k[0], k[1])):
    ex = ' '.join('%s×%d' % (e, n) for e, n in sorted(exits[key].items()))
    cl = sorted(callers[key])
    print('%-6s %05o %6d М%-3s выходы: %s\n         вызовы (%d): %s' % (
        key[0], key[1], calls[key], ','.join(sorted(regs[key])), ex or '-',
        len(cl), ' '.join(cl[:12]) + (' …' if len(cl) > 12 else '')))
