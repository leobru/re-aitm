#!/usr/bin/env python3
"""Add names to the NAMES dict of notes/PART.py: an entry goes before the
first one with a higher address, the other lines stay where they are.

Usage: tools/addnames.py [-e] PART < LIST

-e: into EXTNAMES (names of other parts' cells in PART, made if missing).

LIST lines: 'ааааа ИМЯ комментарий'.  An existing entry of the address
is replaced.  Checks that the name is a valid label (a letter, then up
to 5 letters or digits) and that no other address uses it in any notes
file (shared phase entries Фааааа excepted); the same name of the same
address in several parts (EXTNAMES of a resident cell) is allowed.
"""
import glob
import re
import sys


def main():
    key = 'EXTNAMES' if sys.argv[1] == '-e' else 'NAMES'
    part = sys.argv[-1]
    fn = 'notes/%s.py' % part
    text = open(fn, encoding='utf-8').read()
    new = {}
    for l in sys.stdin:
        if not l.strip() or l.startswith('#'):
            continue
        a, n, *c = l.split(None, 2)
        if not re.fullmatch(r'[0-7]{5}', a) or \
                not re.fullmatch(r'[А-ЯA-Z][А-ЯA-Z0-9]{0,5}', n):
            sys.exit('bad line: ' + l)
        new[a] = (n, c[0].strip() if c else '')
    taken = {}
    for f in glob.glob('notes/*.py'):
        for a, n in re.findall(r"^ '([0-7]{5})': '([^']+)'", open(f, encoding='utf-8').read(), re.M):
            taken.setdefault(n, set()).add((f, a))
    for a, (n, c) in new.items():
        other = {x for x in taken.get(n, set()) if x[1] != a}
        if other and not n.startswith('Ф'):
            sys.exit('%s: name taken by %s' % (n, sorted(other)))
    if key == 'EXTNAMES' and not re.search(r'^EXTNAMES = \{', text, re.M):
        text = text.replace('NAMES = {', 'EXTNAMES = {\n}\n\nNAMES = {', 1)
    m = re.search(r'^%s = \{\n(.*?)^\}' % key, text, re.M | re.S)
    lines = m.group(1).split('\n')[:-1]
    for a, (n, c) in sorted(new.items()):
        s = " '%s': '%s'," % (a, n)
        s += ' ' * max(1, 24 - len(s)) + '# ' + c if c else ''
        at = [i for i, l in enumerate(lines) if l.startswith(" '%s'" % a)]
        if at:
            lines[at[0]] = s
            continue
        after = [i for i, l in enumerate(lines)
                 if re.match(r" '([0-7]{5})'", l) and l[2:7] > a]
        lines.insert(after[0] if after else len(lines), s)
    body = '\n'.join(lines) + '\n'
    open(fn, 'w', encoding='utf-8').write(text[:m.start(1)] + body + text[m.end(1):])


if __name__ == '__main__':
    main()
