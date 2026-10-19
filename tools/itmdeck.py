#!/usr/bin/env python3
"""Make a dispak job for АИТМ 2148 from an autocode text of any length.

Usage: tools/itmdeck.py TEXT.itm 'KEYS' [-o job.b6] [--tape 67(2222-ЗП)]

The text goes to memory from 07000 (card В 7000, А0) and cell 3 gets
06776 + N, N the number of words of the text: the deck's loader puts it
into the accumulator before ЗАГР, so the translator enters ПУСК1 with
A not 0 and copies the N words to the drum itself (f1a 04667, ТЕКСТП),
whatever their number.  KEYS is the key line before В; (e.g.
'РАГК,ФАЗ1А!'), the text is the program from В; to the last Е;.
"""
import argparse

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('text')
    ap.add_argument('keys')
    ap.add_argument('-o', dest='out')
    ap.add_argument('--tape', action='append', default=[])
    a = ap.parse_args()
    body = a.keys + '\n' + open(a.text, encoding='utf-8').read().rstrip('\n') + '\n!'
    n = len(body) // 6 + 0o100            # 6 characters a word, with a margin
    if 0o7000 + n > 0o52000:
        raise SystemExit('текст длиннее памяти 07000-051777')
    s = '%016o' % (0o6776 + n)
    tapes = ''.join('ЛЕНТ %s^\n' % t for t in a.tape)
    job = HEAD % (tapes, ' '.join(s[i:i + 4] for i in range(0, 16, 4))) + body + '_$\nЕКОНЕЦ\n'
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(job)
    else:
        print(job, end='')


if __name__ == '__main__':
    main()
