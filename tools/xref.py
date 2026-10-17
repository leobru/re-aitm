#!/usr/bin/env python3
# Cross-references in a part: for each octal address, the commands whose
# operand names it (label, label+n, label(Мr)), as "address-of-word mnemonic".
# Right halves have no address in parts/NAME.adr; they are counted at the
# address of their word.
# Usage: tools/xref.py NAME ADDR ...   (run in the directory with parts/)
import re, sys

name, addrs = sys.argv[1], sys.argv[2:]
cur, refs = None, {}
for l in open('parts/%s.adr' % name, encoding='utf-8'):
    m = re.match(r'\s*([0-7]+)[ :][0-7]{2} ', l)
    if m and l[:5].strip():
        cur = int(m.group(1), 8)
    f = l.rstrip('\n').split('\t')
    if len(f) >= 4 and cur is not None:
        for lab, off in re.findall(r'[GD]([0-7]{5})(?:\+([0-9]+))?', f[3]):
            refs.setdefault(int(lab, 8) + int(off or 0), []).append('%05o %s' % (cur, f[2]))
for x in addrs:
    print(x, '<-', ', '.join(refs.get(int(x, 8), [])))
