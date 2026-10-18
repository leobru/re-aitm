#!/usr/bin/env python3
"""Linking loader for modules of the ITM autocode translator (2148).

Usage: tools/itmload.py 'РАК,ГЛАВ(ПЕРВ+ВТОР)!' LIB[/ZONE] [-o job.b6] [--seg N]
                        [--common]

Does what the lost loader in drum 21 zone 014 should do after
ЗАВЕР: takes the main module and the modules of the list from the
module library, places them, relocates and links them, and starts the
program.  Format of the modules - AITM-object.md; conventions of the
loader - its section "Loader".

  key     key Р of the translator: letters, ',', main name, '(' list of
          names separated by '+', ')'.  'ИМЯ!' without a list loads one
          module.  Overlays: '/' after a name ends a segment, so
          'ГЛАВ(ПЕРВ+ВТОР/ТРЕТ)' is the root ГЛАВ and the segments
          ПЕРВ+ВТОР and ТРЕТ, both from the end of ГЛАВ; 'А.' or 'Л.'
          before a name puts it on an абзац (0400) or лист (02000)
          boundary.
  LIB     volume number (file in $BESM6_PATH) or path of a volume image;
          /ZONE - zone of the catalogue, module zones count from it.
  -o      write a dispak job that loads the linked image and starts it:
          the main module and segment N (--seg, default 1).
  --common  one Р area for all modules (default: each module its own).

The map of the memory, the names and the resolved references go to
stdout.  The main module goes to 010 (as translated), the others follow,
the Р areas (zeroed) after the images of all segments; the start is the
entry НАЧ of the main module, or 010.  A name is looked up in the
segment of the reference, then in the root, then in the other segments;
a segment cannot refer to another segment, and a reference from the root
must have the same address in every segment that defines the name.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vol import ITM, itm, kind, parse, zones  # noqa: E402

M15 = 0o77777
CODE = {}
for c, ch in sorted(ITM.items(), reverse=True):
    CODE[ch] = c                # the lowest code of a character wins


class LoadError(Exception):
    pass


def word(name):
    """ITM text, right-justified, as a 48-bit word."""
    if len(name) > 6:
        raise LoadError('имя длиннее 6 литер: %s' % name)
    w = 0
    for ch in name:
        if ch not in CODE:
            raise LoadError('литеры %s нет в коде ИТМ' % ch)
        w = w << 8 | CODE[ch]
    return w


ALIGN = {'А': 0o400, 'Л': 0o2000}     # абзац, лист


def parse_key(key):
    """Main module name and the segments of the list from a key Р:
    each segment is a list of (name, alignment)."""
    key = key.strip().rstrip('!')
    m = re.fullmatch(r'(?:Р?[^,(]*,)?\s*([^,(+/.)]+?)\s*(?:\((.*)\))?\s*', key)
    if not m:
        raise LoadError('не разобрать ключ: %s' % key)
    segs, align = [[]], 1
    body = m.group(2) or ''
    items = re.findall(r'\s*([^+/.)]*?)\s*([+/.)]|$)', body)
    for name, d in items:
        if not name and not d:
            continue
        if d == '.':
            if name not in ALIGN:
                raise LoadError('%s. - не А. и не Л.' % name)
            align = ALIGN[name]
            continue
        if not name:
            raise LoadError('пустое имя в списке: %s' % body)
        segs[-1].append((name, align))
        align = 1
        if d == '/':
            segs.append([])
    if not segs[-1] and len(segs) > 1:
        raise LoadError('сегмент без модулей: %s' % body)
    return m.group(1), [s for s in segs if s]


def library(spec):
    path, z = spec, ''
    m = re.fullmatch(r'(.+)/([0-7]+)', spec)
    if m and not os.path.exists(spec):
        path, z = m.groups()
    if not os.path.exists(path):
        path = os.path.join(os.environ.get('BESM6_PATH', '/usr/local/share/besm6'), path)
    return zones(path), int(z or '0', 8)


def catalogue(zs, z0):
    cat, names = zs[z0], {}
    for i in range(0, len(cat), 2):
        name, d = cat[i], cat[i + 1]
        if not name:
            break
        if name != (1 << 48) - 1:
            names[name] = d
    return names


class Module:
    def __init__(self, name, desc, zs, z0):
        self.name = name
        self.m = parse(zs, z0 + (desc & 0o1777))
        self.image = list(self.m['image'])
        self.rsize = (desc >> 20) & 0o7777
        self.base = self.delta = self.rbase = 0
        self.seg, self.align = 0, 1

    def value(self, k, v):
        """Value of kind k (0-4) of this module, v as translated."""
        return {0: v, 1: v + self.delta, 2: self.rbase + v,
                3: v - self.delta, 4: v - self.rbase}[k] & M15


def place(md, a):
    a = -(-a // md.align) * md.align
    md.base, md.delta = a, a - 0o10
    return a + len(md.image)


def link(mods, common):
    # Placement: the root from 010, every segment from the end of the
    # root, Р areas after the longest segment
    root = place(mods[0], 0o10)
    a = root
    for seg in sorted({md.seg for md in mods[1:]}):
        e = root
        for md in mods:
            if md.seg == seg:
                e = place(md, e)
        a = max(a, e)
    if common:
        size = max(md.rsize for md in mods)
        for md in mods:
            md.rbase = a
        a += size
    else:
        for md in mods:
            md.rbase = a
            a += md.rsize
    if a > 0o100000:
        raise LoadError('программа не помещается: конец %o' % a)

    # Names: export tables; name -> {segment: (address, module)}
    names = {}
    for md in mods:
        if not md.m['exports']:
            print('предупреждение: у %s нет таблицы входов (ключ Г)' % md.name)
        for n, v in md.m['exports']:
            k = v >> 45
            if k == 5:
                continue
            d = names.setdefault(n, {})
            if md.seg in d:
                print('предупреждение: %s повторно в %s' % (itm(n), md.name))
                continue
            d[md.seg] = (md.value(k, v & M15), md.name)

    def lookup(md, n):
        d = names.get(n)
        if not d:
            raise LoadError('%s: внешнее имя %s не найдено' % (md.name, itm(n)))
        for s in (md.seg, 0):
            if s in d:
                return d[s][0]
        if md.seg:
            raise LoadError('%s: имя %s из другого сегмента (%s)'
                            % (md.name, itm(n), d[min(d)][1]))
        if len({v for v, _ in d.values()}) > 1:
            raise LoadError('%s: адрес %s разный в сегментах (%s)' % (md.name, itm(n),
                            ', '.join('%s %05o' % (m, v) for v, m in d.values())))
        return d[min(d)][0]

    def external(md, lit, off=0):
        """Address of literal lit (with flag 04000 = minus) + offset."""
        neg, lit = lit & 0o4000, lit & 0o3777
        n = md.m['literals'][lit]
        v = lookup(md, n) + off
        md.links.append((itm(n), off, neg, v))
        return -v if neg else v

    def resolve(md, k, v):
        if k == 5:
            return external(md, v)
        if k == 6:
            r = md.m['refs'][v]
            return external(md, (r >> 30) & 0o7777, r & M15)
        return md.value(k, v)

    for md in mods:
        md.links = []
        for i, w in enumerate(md.image):
            for h in (0, 1):
                k = kind(md.m, i, h)
                if not k:
                    continue
                sh = 24 * (1 - h)
                half = (w >> sh) & 0o77777777
                if half & 1 << 19:      # long command: 15-bit address
                    half = half & ~M15 | resolve(md, k, half & M15) & M15
                else:                   # short: 12 bits, bit 19 - 070000
                    v = half & 0o7777 | (0o70000 if half & 1 << 18 else 0)
                    v = resolve(md, k, v) & M15
                    if 0o10000 <= v < 0o70000:
                        raise LoadError('%s: адрес %05o не помещается в короткую '
                                        'команду (слово %05o)' % (md.name, v, md.base + i))
                    half = half & ~(1 << 18 | 0o7777) | (v >= 0o70000) << 18 | v & 0o7777
                w = w & ~(0o77777777 << sh) | half << sh
            md.image[i] = w
        # Records of Л; fields
        for r in md.m['refs']:
            k = r >> 45
            if not k:
                continue
            width = ((r >> 41) & 0o17) + 1
            low = ((r >> 35) & 0o77) - width + 1
            i = (r & M15) - 0o10
            v = resolve(md, k, (r >> 15) & M15) & ((1 << width) - 1)
            mask = ((1 << width) - 1) << low
            md.image[i] = md.image[i] & ~mask | v << low
    return names, a


def kcard(h):
    """Half-word as the 9 digits of a К card (1+3+2+6x3 bits): dispak
    loads К cards as commands; words of С cards are numbers, and
    executing them stops the job with «КОНТРОЛЬ КОМАНДЫ»."""
    return '%o%o %o%02o %04o' % (h >> 23, (h >> 20) & 7, (h >> 18) & 3,
                                 (h >> 12) & 0o77, h & 0o7777)


def job(mods, start, out):
    with open(out, 'w', encoding='utf-8') as f:
        f.write('ШИФР 419900000012^\nАЦП 10^\nТРАК 32^\nЛИСТ 0-37^\n'
                'ВХОД %o^\nРОСП 0^\nВРЕМ 240^\nСПЕЦ^\nЕ\n' % start)
        for md in mods:
            f.write('В %o\n' % md.base)
            for w in md.image:
                f.write('К %s %s\n' % (kcard(w >> 24), kcard(w & 0o77777777)))
        f.write('ЕКОНЕЦ\n')


def main():
    ap = argparse.ArgumentParser(description='Загрузчик модулей АИТМ')
    ap.add_argument('key')
    ap.add_argument('lib')
    ap.add_argument('-o', dest='out')
    ap.add_argument('--seg', type=int, default=1)
    ap.add_argument('--common', action='store_true')
    a = ap.parse_args()
    try:
        main_name, segs = parse_key(a.key)
        zs, z0 = library(a.lib)
        cat = catalogue(zs, z0)
        mods = []
        for s, items in enumerate([[(main_name, 1)]] + segs):
            for n, align in items:
                if word(n) not in cat:
                    raise LoadError('модуля %s нет в каталоге' % n)
                md = Module(n, cat[word(n)], zs, z0)
                md.seg, md.align = s, align
                mods.append(md)
        if segs and not 1 <= a.seg <= len(segs):
            raise LoadError('сегмента %d нет (всего %d)' % (a.seg, len(segs)))
        names, end = link(mods, a.common)
    except LoadError as e:
        sys.exit('ОШИБКА ЗАГРУЗЧИКА: %s' % e)
    start = 0o10
    for n, v in mods[0].m['exports']:
        if n == word('НАЧ') and v >> 45 == 1:
            start = mods[0].value(1, v & M15)
    print('модуль  сегмент  образ        область Р')
    for md in mods:
        print('%-6s  %-7s  %05o-%05o  %s' % (
            md.name, md.seg or 'корень', md.base, md.base + len(md.image) - 1,
            '%05o-%05o' % (md.rbase, md.rbase + md.rsize - 1) if md.rsize else '-'))
    print('конец %05o, пуск %05o' % (end, start))
    print('имена:')
    for n, d in names.items():
        for s, (v, mn) in sorted(d.items()):
            print('  %-6s %05o  %s' % (itm(n), v, mn))
    for md in mods:
        for n, off, neg, v in sorted(set(md.links)):
            print('  %s: %s%s%s = %05o' % (md.name, '-' if neg else '', n,
                                          '(%o)' % off if off else '', v))
    if a.out:
        job([md for md in mods if md.seg in (0, a.seg)], start, a.out)


if __name__ == '__main__':
    main()
