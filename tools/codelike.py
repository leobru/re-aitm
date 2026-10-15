#!/usr/bin/env python3
# Data words (КОНД/КОНК in parts/NAME.adr) that look like code: both halves
# are common operations with a plausible operand (an address of the image
# outside the gaps, or a small number with an index register). Prints runs
# of such words with the code line just before the run and the references
# to the first word (labels used elsewhere).
# Usage: tools/codelike.py NAME [MIN]     MIN - shortest run, default 2
import re, sys

name = sys.argv[1]
MIN = int(sys.argv[2]) if len(sys.argv) > 2 else 2
# short operations (7-bit code) and long ones (5-bit, 020-037)
SHORT = {0o000: 'зп', 0o010: 'сч', 0o011: 'и', 0o012: 'нтж', 0o013: 'слц',
         0o015: 'или', 0o036: 'сда', 0o040: 'уи', 0o042: 'счи', 0o004: 'сл',
         0o005: 'вч', 0o020: 'сбр', 0o021: 'рзб', 0o031: 'счмр', 0o064: 'Э64',
         0o070: 'Э70', 0o071: 'Э71', 0o074: 'Э74', 0o075: 'Э75'}
LONG = {0o23: 'мод', 0o24: 'уиа', 0o25: 'слиа', 0o26: 'по', 0o27: 'пе',
        0o30: 'пб', 0o31: 'пв', 0o34: 'пио', 0o35: 'пино', 0o37: 'цикл'}

# the image size and the gaps from parts.txt
size, gaps = 0, []
for l in open('parts.txt', encoding='utf-8'):
    f = l.split()
    if f and not l.startswith('#') and f[0] == name:
        pos = base = int(f[2], 8)
        for z in f[3:]:
            n = int(z[1:], 8) if z.startswith('-') else 256 if '.' in z else 1024
            if z.startswith('-'):
                gaps.append((pos, pos + n))
            pos += n
        size = pos


def plausible(h):
    reg = h >> 20
    if h & (1 << 19):
        op, a = (h >> 15) & 0o37, h & 0o77777
        if op not in LONG:
            return None
        if op in (0o24, 0o25, 0o37) or reg:
            ok = True       # a counter, an index or an indexed address
        else:
            ok = 0o100 <= a < size and not any(lo <= a < hi for lo, hi in gaps)
        return LONG[op] if ok else None
    op, a = (h >> 12) & 0o177, h & 0o7777
    if op & 0o100:
        a |= 0o70000
        op &= 0o77
    if op not in SHORT:
        return None
    if op in (0o036, 0o040, 0o042, 0o031):
        return SHORT[op]
    if reg:
        return SHORT[op]
    if a == 0 and op not in (0o000, 0o010):
        return None
    if 0 < a < 0o100 and op != 0o064:
        return None
    if any(lo <= a < hi for lo, hi in gaps) or a >= size:
        return None
    return SHORT[op]


words = []                      # (address, kind, value or None, line)
prev_code = {}
last = None
for l in open('parts/%s.adr' % name, encoding='utf-8'):
    m = re.match(r'^ *([0-7]{1,5})([ :])(\S+(?: \S+ \S+)?)\s*?\t(\S*)\t(\S+)', l)
    if not m:
        continue
    a = int(m.group(1), 8)
    op = m.group(5)
    if op in ('конд', 'конк') and re.fullmatch(r'[0-7]{16}', m.group(3)):
        words.append((a, int(m.group(3), 8), m.group(4), last))
    elif op not in ('пам', 'конд', 'конк'):
        last = l.rstrip()

refs = {}
src = open('parts/%s.be' % name, encoding='utf-8').read()
runs = []
cur = []
for a, w, lab, before in words:
    l, r = plausible(w >> 24), plausible(w & 0xffffff)
    ok = l and r and w >> 24 and w & 0xffffff
    if ok and cur and cur[-1][0] == a - 1:
        cur.append((a, l, r, lab, before))
    else:
        if len(cur) >= MIN:
            runs.append(cur)
        cur = [(a, l, r, lab, before)] if ok else []
if len(cur) >= MIN:
    runs.append(cur)
for run in runs:
    a0 = run[0][0]
    print('%05o-%05o  %d слов%s' % (a0, run[-1][0], len(run),
          '  метка ' + run[0][3] if run[0][3] else ''))
    print('    перед: %s' % (run[0][4] or '').strip()[:70])
    for a, l, r, lab, _ in run:
        print('    %05o %s / %s' % (a, l, r))
