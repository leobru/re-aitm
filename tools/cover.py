#!/usr/bin/env python3
# Code coverage of the parts by the test jobs.
# Usage: tools/cover.py [-r] [-j JOB]... [-u] [-l] [-d] [PART...]
#   Brings the traces of the jobs up to date ("make traces"; -r - all of
#   them again), then compares the executed addresses (traces/JOB.cov) with
#   the code words of each part (instruction lines of parts/PART.be.lst,
#   made by "make check") and prints a table: code words, executed, percent.
#   PART... - also list the unexecuted code ranges of these parts with the
#             nearest label above ("МЕТКА+N").
#   -j JOB  - count only these jobs (name as in traces/, e.g. macro2).
#   -u      - with -j: print what these jobs execute that no other job does.
#   -l      - instead of the ranges print the source of PART... (label,
#             operation, operand, comment) with the address of each word;
#             '-' marks the code words that were never executed.
#   -d      - list the executed addresses that the source shows as data
#             (candidates for ENTRIES in notes/PART.py).
import glob, os, re, subprocess, sys

args = sys.argv[1:]
redo = '-r' in args
uniq = '-u' in args
listing = '-l' in args
data = '-d' in args
only = []
want = []
i = 0
while i < len(args):
    if args[i] == '-j':
        only.append(args[i + 1]); i += 1
    elif not args[i].startswith('-'):
        want.append(args[i])
    i += 1

subprocess.run(['make', '-s'] + (['-B'] if redo else []) + ['traces'],
               check=True, stdout=sys.stderr)

parts = []
for l in open('parts.txt'):
    f = l.split()
    if f and not l.startswith('#'):
        parts.append((f[0], f[3:]))

def zonecov(spec, jobs=None, excl=None):
    # spec: a zone (all its sectors) or zone.sector
    s = set()
    for c in glob.glob('traces/*.cov/%s.cov' % (spec if '.' in spec else spec + '.?')):
        n = os.path.basename(os.path.dirname(c))[:-4]
        if jobs and n not in jobs or excl and n in excl:
            continue
        s.update(int(x.split(':')[0], 8) for x in open(c))
    return s

allw = {}                       # part -> all addresses of its listing

def code(name):
    # address -> label+offset for the words that hold instructions
    res = {}
    allw[name] = set()
    lab, base = '', 0
    try:
        f = open('parts/%s.be.lst' % name, errors='replace')
    except OSError:
        return res
    for l in f:
        m = re.match(r'^.{0,36}?([0-7]{5}) ([0-7]{2} [0-7]{2,3} +[0-7]{4,5}|[0-7]{16})(?: +[0-7]{5})? +\d{4}  \d{4} (.{0,6}) ?(\S*) *(\S*)', l)
        if not m:
            continue
        a = int(m.group(1), 8)
        allw[name].add(a)
        if m.group(3).strip():
            lab, base = m.group(3).strip(), a
        # a word that starts with КОНК, ДК or КК 0,… (an Э64 parameter
        # word) is data in command format; КК '64',… is an extracode
        kk0 = m.group(4) == 'КК' and m.group(5).startswith('0,')
        if ' ' in m.group(2) and m.group(4) not in ('КОНК', 'ДК', 'ДКБ') and not kk0:
            res[a] = (lab + ('+%o' % (a - base) if a != base else '')) if lab else ''
    return res

tot = [0, 0]
for name, zones in parts:
    c = code(name)
    ex = set()
    for z in zones:
        ex |= zonecov(z, only) - (zonecov(z, None, only) if uniq and only else set())
    hit = ex & set(c)
    tot[0] += len(c); tot[1] += len(hit)
    print('%-7s %5d слов кода, исполнялось %5d (%3d%%)'
          % (name, len(c), len(hit), 100 * len(hit) // max(len(c), 1)))
    if data:
        bad = sorted(ex - set(c))
        if bad:
            print('    данные исполнялись: ' + ' '.join('%05o' % a for a in bad))
    if name in want and listing:
        miss = set(c) - hit
        for l in open('parts/%s.be.lst' % name, errors='replace'):
            m = re.match(r'^.{0,36}?(?:([0-7]{5}) )?(?:[0-7]{2} [0-7]{2,3} +[0-7]{4,5}|[0-7]{16})(?: +[0-7]{5})? +\d{4}  \d{4} (.*)', l)
            if m:
                a = int(m.group(1), 8) if m.group(1) else None
                print('%s %5s %s' % ('-' if a in miss else ' ', m.group(1) or '', m.group(2).rstrip()))
            elif re.match(r'^ {30,}\d{4}  \d{4} \*', l):
                print('        ' + l[l.index('*', 40):].rstrip())
    elif name in want:
        miss = sorted(set(c) - hit)
        j = 0
        while j < len(miss):
            k = j
            while k + 1 < len(miss) and miss[k + 1] == miss[k] + 1:
                k += 1
            print('    %05o-%05o %4d  %s' % (miss[j], miss[k], k - j + 1, c[miss[j]]))
            j = k + 1
print('%-7s %5d слов кода, исполнялось %5d (%3d%%)'
      % ('всего', tot[0], tot[1], 100 * tot[1] // max(tot[0], 1)))
