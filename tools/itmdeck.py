#!/usr/bin/env python3
"""Make a dispak job for АИТМ 2148 from an autocode text of any length.

Usage: tools/itmdeck.py TEXT.itm 'KEYS' [-o job.b6] [--tape 67(2222-ЗП)]

The text goes to memory from 07000 (card В 7000, А0) and cell 3 gets
06776 + N, N the number of words of the text: the deck's loader puts it
into the accumulator before ЗАГР, so the translator enters ПУСК1 with
A not 0 and copies the N words to the drum itself (f1a 04667, ТЕКСТП),
whatever their number.  KEYS is the key line before В; (e.g.
'РАГК,ФАЗ1А!'), the text is the program from В; to the last Е;.

With --stored VOL NAME the translator is the program NAME stored by zagr
or itmload --store on the library volume VOL (АИТМЗ, make dogfood): the
deck loads its root and segment 1 (phase 1) from the record instead of
the zones of 2148, and a starter at 027770 enters 010 with A = 06776 + N.
Phase 2 is still read from 2148 (ЛЕНТ 40) by the translator's own Э70.
"""
import argparse
import os
import sys

HEAD = '''ШИФР 419900000012^
АЦП 10^
ТРАК 32^
ЛИСТ 0-24^
ВХОД 4237^
ФИЗО МБ21^
РОСП 0^
ЛЕНТ 40(2148)^
%sВРЕМ 600^
СПЕЦ^
Е
В 3
С %s
В 4237
K 00 000 0000
К 00 010 4243 00 050 0112
К 00 070 4244
К 00 010 0003 00 30 06770
С 0000 0000 0040 0010
С 4014 0301 0021 0111
C 0000 1000 0023 0000
В 7000
А0
'''


def stored(spec, acc, tapes):
    """Head of a deck that loads the stored program and starts it."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import itmload
    from vol import zones
    path, z0 = itmload.library(spec[0])
    zs = zones(path)
    cat = itmload.catalogue(zs, z0)
    root, start, tab, segs, exports = itmload.read_program(zs, z0, cat[itmload.word(spec[1])])
    blocks = [(1, root[1:])]
    for x in segs[0] if segs else []:
        addr, z, k = itmload.unpack_e70(x)
        blocks.append((addr, zs[z][k * itmload.SECTOR:(k + 1) * itmload.SECTOR]))
    long_ = lambda ir, op, a: ir << 20 | 1 << 19 | (op & 0o17) << 15 | a
    short = lambda ir, op, a: ir << 20 | op << 12 | a
    # as the deck and ЗАГР (aitm6 06770) do: Э50 0112 - volume 040 (2148)
    # from zone 0400 (an extracode in the right half: after it execution
    # goes on with the next word); A = 06776 + N, М1 = М2 = 0, М16 = 06777
    starter = [long_(1, 0o24, 0o27776) << 24 | short(1, 0o10, 0),  # уиа; сч (М1)
               long_(0, 0o22, 0) << 24 | short(0, 0o50, 0o112),    # мода; Э50
               long_(1, 0o24, 0o27777) << 24 | short(1, 0o10, 0),  # уиа; сч (М1)
               long_(1, 0o24, 0) << 24 | long_(0o16, 0o24, 0o6777),  # уиа М1, М16
               long_(0, 0o30, start) << 24,                         # пб пуск
               0, 0o0000000000400010, acc]                          # 027776, 027777
    out = HEAD.split('В 3\n')[0].replace('ВХОД 4237', 'ВХОД 27770') % tapes
    for base, ws in blocks + [(0o27770, starter)]:
        out += 'В %o\n' % base
        for w in ws:
            out += 'К %s %s\n' % (itmload.kcard(w >> 24), itmload.kcard(w & 0o77777777))
    return out + 'В 7000\nА0\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('text')
    ap.add_argument('keys')
    ap.add_argument('-o', dest='out')
    ap.add_argument('--tape', action='append', default=[])
    ap.add_argument('--stored', nargs=2, metavar=('VOL', 'ИМЯ'))
    a = ap.parse_args()
    body = a.keys + '\n' + open(a.text, encoding='utf-8').read().rstrip('\n') + '\n!'
    n = len(body) // 6 + 0o100            # 6 characters a word, with a margin
    if 0o7000 + n > 0o52000:
        raise SystemExit('текст длиннее памяти 07000-051777')
    s = '%016o' % (0o6776 + n)
    tapes = ''.join('ЛЕНТ %s^\n' % t for t in a.tape)
    job = HEAD % (tapes, ' '.join(s[i:i + 4] for i in range(0, 16, 4))) + body + '_$\nЕКОНЕЦ\n'
    if a.stored:
        job = stored(a.stored, 0o6776 + n, tapes) + body + '_$\nЕКОНЕЦ\n'
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(job)
    else:
        print(job, end='')


if __name__ == '__main__':
    main()
