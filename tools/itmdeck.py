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
or itmload --store on the library volume VOL (АИТМЗ, make dogfood).  The
deck is the same, but ЛЕНТ 40 is the library volume (it is 2222 in
tools/dispakrun.sh) and the drum offset of Э50 0112 is the zone of лист
0 of the record minus 06: the stored translator is laid out as on 2148
(itmload.write_program), so its own Э70 words for zones 06-012 of drum
21 read it from the record.  Run it with dispak --725, which counts the
offset in zones (without it, in units of 040 zones):
DISPAK_OPTS=--725 VOLIN=VOL tools/dispakrun.sh job.b6 out.txt.
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
ЛЕНТ 40(%s)^
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
С 0000 0000 0040 %04o
С 4014 0301 0021 0111
C 0000 1000 0023 0000
В 7000
А0
'''


def offset(spec):
    """Drum offset of the program stored on the library volume."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import itmload
    from vol import zones
    path, z0 = itmload.library(spec[0])
    zs = zones(path)
    cat = itmload.catalogue(zs, z0)
    if itmload.word(spec[1]) not in cat:
        sys.exit('%s нет в каталоге' % spec[1])
    return itmload.read_program(zs, z0, cat[itmload.word(spec[1])])[5] - 0o6


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
    vol, off = ('2222', offset(a.stored)) if a.stored else ('2148', 0o10)
    job = HEAD % (vol, tapes, ' '.join(s[i:i + 4] for i in range(0, 16, 4)), off) \
        + body + '_$\nЕКОНЕЦ\n'
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(job)
    else:
        print(job, end='')


if __name__ == '__main__':
    main()
