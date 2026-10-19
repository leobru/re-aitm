#!/usr/bin/env python3
"""Texts of the stress test of the loader zagr: many entry names.

Usage: tools/zstress.py OUTDIR [NR NA NB NX]

Writes OUTDIR/ГЛС.itm (the main module: NR entries КРn, uses СА0 and СБ0
of the segments), OUTDIR/СА.itm (segment 1: NA entries САn and ОБЩ, uses
NX root names, some with an offset) and OUTDIR/СБ.itm (segment 2: NB
entries СБn and ОБЩ, the same uses), and OUTDIR/НЕТ.itm (a main module
that uses a name nobody has).  Defaults: 200, 900, 300, 100 - 1400 names
in all (the old table held 333); the image of СА goes to 04000, so the
module is longer than 4 zones.  A module holds at most about 1000 entry
names: ВЫВМ builds the export table at 010000 and the module at 014000.
tools/zstress.sh translates and links them.
"""
import os
import sys


def lines(items, n=3):
    return [''.join(items[i:i + n]) for i in range(0, len(items), n)]


def segment(pre, n, nr, nx, big=False):
    uses = sorted({(k * 37) % nr for k in range(nx)})
    out = ['В;']
    out += ['Э;' + l for l in lines(['КР%d:Н=КР%d,' % (u, u) for u in uses])]
    out += ['В;', 'К;*%s0:СЧКР%d=СЧКР%d(1),' % (pre, uses[0], uses[-1])]
    for i, u in enumerate(uses):
        out.append('СЧКР%d=СЧКР%d(%d),' % (u, uses[(i + 1) % len(uses)], i % 7))
    out.append('С;')
    out += ['*%s%d:%o,' % (pre, i, i) for i in range(1, n)]
    out += ['*ОБЩ:%o,' % n]
    if big:                         # the image to 04000: over 4 zones in all
        out += ['Н;4000,', 'С;7,']
    out += ['Е;', 'Е;']
    return '\n'.join(out) + '\n'


def main():
    d = sys.argv[1]
    nr, na, nb, nx = [int(x) for x in sys.argv[2:6]] or [200, 900, 300, 100]
    os.makedirs(d, exist_ok=True)
    root = ['В;', 'Э;СА0:Н=СА0,СБ0:Н=СБ0,', 'В;',
            'К;*НАЧ:СЧСА0=СЧСБ0,', '=Э074,', 'С;']
    root += ['*КР%d:%o,' % (i, i) for i in range(nr)]
    root += ['Е;', 'Е;']
    files = {'ГЛС': '\n'.join(root) + '\n',
             'СА': segment('СА', na, nr, nx, True),
             'СБ': segment('СБ', nb, nr, nx),
             'НЕТ': 'В;\nЭ;НТ:Н=НЕТУ,\nК;НАЧ:СЧНТ=,\n=Э074,\nЕ;\n'}
    for name, text in files.items():
        open(os.path.join(d, name + '.itm'), 'w', encoding='utf-8').write(text)


if __name__ == '__main__':
    main()
