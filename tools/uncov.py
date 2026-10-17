#!/usr/bin/env python3
# Code of a part that no job executed: the lines of parts/NAME.be.lst for
# every never-executed range (code words of parts/NAME.adr minus
# parts/NAME.cov), with C lines of context before and after.
# Usage: tools/uncov.py NAME [C] [FROM-TO]   (run in the directory with
#        parts/; C default 2; FROM-TO - octal address range to show)
import re, sys

name = sys.argv[1]
C = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 2
lo, hi = 0, 1 << 15
for a in sys.argv[2:]:
    if '-' in a:
        lo, hi = (int(x, 8) for x in a.split('-'))
cov = {int(l.split(':')[0], 8) for l in open('parts/%s.cov' % name)}
code = set()
for l in open('parts/%s.adr' % name):
    m = re.match(r'\s*([0-7]+)[ :]([0-7]{2} [0-7 ]{2,3} [0-7]{4,5})\s', l)
    if m:
        code.add(int(m.group(1), 8))
un = {a for a in code - cov if lo <= a <= hi}
# listing lines: the address column starts a word, the next line without
# an address is its right half
lst = [l.rstrip('\n') for l in open('parts/%s.be.lst' % name, encoding='utf-8', errors='replace')
       if re.match(r'\s{20,}[0-7 ]{5}\s[0-7]{2} ', l)]
addr, cur = [], None
for l in lst:
    m = re.match(r'\s{20,}([0-7]{5}) ', l)
    if m:
        cur = int(m.group(1), 8)
    addr.append(cur)
show = set()
for i, a in enumerate(addr):
    if a in un:
        show.update(range(max(0, i - 2 * C), min(len(lst), i + 2 * C + 2)))
prev = None
for i in sorted(show):
    if prev is not None and i != prev + 1:
        print('--')
    mark = '!' if addr[i] in un else ' '
    print(mark, lst[i][25:].rstrip())
    prev = i
