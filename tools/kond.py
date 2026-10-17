#!/usr/bin/env python3
# Sort the data words (КОНД) of a part into classes, to tell code hidden
# among them from real data. Runs of consecutive КОНД words are taken
# together; for each run:
#   ссылка  - some command addresses a word of the run (label, label+n,
#             label(Мr)): a constant or a table;
#   буфер   - at or above BUF (an area that is overwritten before use);
#   код?    - no references, and either every word decodes to plausible
#             commands (both halves, see tools/codelike.py) with a jump
#             before the run, or a jump in the run leads into the run
#             (plausible() rejects small operands such as cells 2-4):
#             dead code or code reached by a computed jump;
#   данные? - no references and not code-like.
# Usage: tools/kond.py NAME [BUF] [-v]   (run in the directory with parts/;
#        BUF octal; -v lists the runs, otherwise only the totals)
import re, sys

args = [a for a in sys.argv[1:] if a != '-v']
verbose = '-v' in sys.argv
name = args[0]
BUF = int(args[1], 8) if len(args) > 1 else 1 << 15
sys.argv = [sys.argv[0], name]
exec(open(__file__.replace('kond.py', 'codelike.py')).read().split('\nwords = []')[0])

words, refs = {}, set()
prev = {}                       # address -> mnemonic of the word before
cur, lastop = None, None
for l in open('parts/%s.adr' % name, encoding='utf-8'):
    f = l.rstrip('\n').split('\t')
    m = re.match(r'^ *([0-7]{1,5})[ :]', l)
    if m and l[:5].strip():
        cur = int(m.group(1), 8)
        if len(f) > 3 and f[2] == 'конд' and re.fullmatch(r' *[0-7]+ [0-7]{16}', f[0]):
            words[cur] = int(f[0].split()[1], 8)
        prev.setdefault(cur, lastop)
    if len(f) > 3:
        if f[2] not in ('конд', 'конк', 'пам'):
            lastop = f[2]
        for lab, off in re.findall(r'[GD]([0-7]{5})(?:\+([0-9]+))?', f[3]):
            refs.add(int(lab, 8) + int(off or 0))


def inner_jump(r):
    # a long-format jump (по, пе, пб, пв, цикл ...) to a word of the run
    for a in r:
        for h in (words[a] >> 24, words[a] & 0xffffff):
            if h & (1 << 19) and (h >> 15) & 0o37 in (0o26, 0o27, 0o30, 0o31, 0o34, 0o35, 0o37) \
                    and r[0] <= h & 0o77777 <= r[-1]:
                return True
    return False


runs = []
for a in sorted(words):
    if runs and a == runs[-1][-1] + 1:
        runs[-1].append(a)
    else:
        runs.append([a])
total = {}
for r in runs:
    if r[0] >= BUF:
        kind = 'буфер'
    elif any(a in refs for a in r):
        kind = 'ссылка'
    elif all(plausible(words[a] >> 24) and plausible(words[a] & 0xffffff) for a in r) \
            and prev.get(r[0]) in ('пб', 'пв', 'пвл') or inner_jump(r):
        kind = 'код?'
    else:
        kind = 'данные?'
    total[kind] = total.get(kind, 0) + len(r)
    if verbose and kind != 'буфер':
        print('%05o-%05o %3d %-8s %s' % (r[0], r[-1], len(r), kind,
              ' '.join('%016o' % words[a] for a in r[:2]) + (' …' if len(r) > 2 else '')))
print('КОНД: %d слов; %s' % (len(words), ', '.join('%s %d' % kv for kv in sorted(total.items()))))
