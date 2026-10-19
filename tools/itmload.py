#!/usr/bin/env python3
"""Linking loader for modules of the ITM autocode translator (2148).

Usage: tools/itmload.py 'РАК,ГЛАВ(ПЕРВ+ВТОР)!' LIB[/ZONE] [-o job.b6] [--seg N]
                        [--common] [--store ИМЯ OUT.vol] [--vol N]

Does what the lost loader in drum 21 zone 014 should do after
ЗАВЕР: takes the main module and the modules of the list from the
module library, places them, relocates and links them, and starts the
program, or stores the linked program in the library.  Format of the
modules and conventions of the loader - AITM-object.md, section 7.

  key     key Р of the translator: letters, ',', main name, '(' list of
          names separated by '+', ')'.  'ИМЯ!' without a list loads one
          module, or a program stored by --store.  Overlays: '/' after a
          name ends a segment, so 'ГЛАВ(ПЕРВ+ВТОР/ТРЕТ)' is the root ГЛАВ
          and the segments ПЕРВ+ВТОР and ТРЕТ, both from the end of
          ГЛАВ; 'А.' or 'Л.' before a name puts it on an абзац (0400) or
          лист (02000) boundary.
  LIB     volume number (file in $BESM6_PATH) or path of a volume image;
          /ZONE - zone of the catalogue, module zones count from it.
  -o      write a dispak job that loads the linked image and starts it:
          the main module and segment N (--seg, default 1).
  --common  one Р area for all modules (default: each module its own).
  --store ИМЯ OUT.vol
          store the linked program in a copy of LIB as ИМЯ: the root,
          then each segment from an абзац boundary.  After the main
          module the root gets a table of Э70 words for unit 067, one
          per sector of a segment, each segment's run ended by 0; the
          program reads segment n by the words at the external name СЕГn.
  --vol N  volume number for ЛЕНТ 67 in the job of a stored program
          (default 2222).

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
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vol import ITM, ZONE, ZONE_OFFSET, itm, kind, parse, zones  # noqa: E402

M15 = 0o77777
M48 = (1 << 48) - 1
SECTOR = 0o400                  # абзац
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


ALIGN = {'А': SECTOR, 'Л': 0o2000}     # абзац, лист


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
    return path, int(z or '0', 8)


def catalogue(zs, z0):
    cat, names = zs[z0], {}
    for i in range(0, len(cat), 2):
        name, d = cat[i], cat[i + 1]
        if not name:
            break
        if name != M48:
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


def layout(mods, common, table=0, rpad=1):
    """Place the root from 010, then `table` words, every segment from
    there, the Р areas after the longest segment (from a multiple of
    rpad).  Returns the end and {segment: (start, end)}."""
    root = place(mods[0], 0o10) + table
    a, spans = root, {}
    for seg in sorted({md.seg for md in mods[1:]}):
        e = root
        for md in mods:
            if md.seg == seg:
                e = place(md, e)
        first = min(md.base for md in mods if md.seg == seg)
        spans[seg] = (first, e)
        a = max(a, e)
    a = -(-a // rpad) * rpad
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
    return a, spans


def link(mods, extra=None):
    """Relocate and link the placed modules; extra - names of the
    loader itself in the root, {name word: address}."""
    names = {}
    for n, v in (extra or {}).items():
        names[n] = {0: (v, 'загрузчик')}
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
    return names


# Stored program ------------------------------------------------------

def e70(addr, zone, sector):
    """Э70 word: read one sector of unit 067 to the абзац at addr.  Left:
    sector exchange (010 in the index field), read (010), sector given
    by number (04000), лист and абзац of the address; right: unit 067,
    zone << 2 | sector (dispak ddio: zones 0-037 only)."""
    if zone > 0o37:
        raise LoadError('зона %o: секторный обмен 067 достаёт только зоны 0-037' % zone)
    left = 0o10 << 20 | 0o10 << 12 | 0o4000 | (addr >> 10) << 6 | (addr >> 8) & 3
    right = 0o67 << 12 | zone << 2 | sector
    return left << 24 | right


def unpack_e70(w):
    """(address, zone, sector) of an Э70 word made by e70()."""
    left, right = w >> 24, w & 0o77777777
    return (left >> 6 & 0o37) << 10 | (left & 3) << 8, (right & 0o177) >> 2, right & 3


def write_program(path, out, z0, name, mods, spans, table, start, names):
    """Store the linked program in a copy of the volume path as out:
      word 0  root length << 33 | segments << 22
      word 1  export words << 36 | table address << 15 | start
      root image (from 010, with the table of Э70 words), export table
      (name, address) of the root names, then the segments, each from a
      sector boundary, as the table reads them.  Catalogue descriptor:
      bit 48 = 0 (a stored program), words << 32, first zone."""
    b = bytearray(open(path, 'rb').read())

    def zone(z):
        off = (z + ZONE_OFFSET) * ZONE
        if len(b) < off + ZONE:
            b.extend(bytes(off + ZONE - len(b)))
        return off

    def put(z, i, w):
        # bit 49 of a data word is the instruction tag (dispak disk.c)
        struct.pack_into('<Q', b, zone(z) + 64 + 8 * i, 1 << 48 | w & M48)

    def get(z, i):
        return struct.unpack_from('<Q', b, zone(z) + 64 + 8 * i)[0] & M48

    # Catalogue: free an old entry of the name; the end mark gives the zone
    i = 0
    while get(z0, i):
        if get(z0, i) == word(name):
            put(z0, i, M48)
        i += 2
    if i + 4 > 1024:
        raise LoadError('каталог полон')
    first = get(z0, i + 1) or 1

    core = {}
    for md in mods:
        for j, w in enumerate(md.image):
            core[(md.seg, md.base + j)] = w
    tab = mods[0].base + len(mods[0].image)
    rootend = tab + len(table)
    exports = [(n, d[0][0]) for n, d in names.items() if 0 in d]
    rec = [0, 0] + [core.get((0, a), 0) for a in range(0o10, rootend)]
    for n, v in exports:
        rec += [n, v]
    sec = -(-len(rec) // SECTOR)
    t, data = [], {}
    for s in sorted(spans):
        a0, a1 = spans[s]
        for a in range(a0, a1, SECTOR):
            t.append(e70(a, z0 + first + sec // 4, sec % 4))
            data[sec] = [core.get((s, x), 0) for x in range(a, a + SECTOR)]
            sec += 1
        t.append(0)
    assert len(t) == len(table)
    rec[2 + tab - 0o10:2 + rootend - 0o10] = t
    rec[0] = (rootend - 0o10) << 33 | len(spans) << 22
    rec[1] = 2 * len(exports) << 36 | tab << 15 | start
    for j, w in enumerate(rec):
        put(z0 + first + j // 1024, j % 1024, w)
    for k, ws in data.items():
        for j, w in enumerate(ws):
            put(z0 + first + k // 4, (k % 4) * SECTOR + j, w)
    nz = -(-sec // 4)
    put(z0, i, word(name))
    put(z0, i + 1, sec * SECTOR << 32 | first)
    put(z0, i + 2, 0)
    put(z0, i + 3, first + nz)
    open(out, 'wb').write(b)
    return first, nz


def read_program(zs, z0, desc):
    """Root image, start, table address, Э70 words of each segment and
    exports of a stored program."""
    w = [x for z in zs[z0 + (desc & 0o1777):] for x in z]
    n, nseg = w[0] >> 33, (w[0] >> 22) & 0o3777
    nexp, tab, start = w[1] >> 36, (w[1] >> 15) & M15, w[1] & M15
    root = w[2:2 + n]
    exports = [(w[i], w[i + 1]) for i in range(2 + n, 2 + n + nexp, 2)]
    segs, j = [], tab - 0o10
    for _ in range(nseg):
        e = []
        while root[j]:
            e.append(root[j])
            j += 1
        segs.append(e)
        j += 1
    return root, start, tab, segs, exports


# Output --------------------------------------------------------------

def kcard(h):
    """Half-word as the 9 digits of a К card (1+3+2+6x3 bits): dispak
    loads К cards as commands; words of С cards are numbers, and
    executing them stops the job with «КОНТРОЛЬ КОМАНДЫ»."""
    return '%o%o %o%02o %04o' % (h >> 23, (h >> 20) & 7, (h >> 18) & 3,
                                 (h >> 12) & 0o77, h & 0o7777)


def job(blocks, start, out, vol=None):
    """blocks: [(address, words)]."""
    with open(out, 'w', encoding='utf-8') as f:
        f.write('ШИФР 419900000012^\nАЦП 10^\nТРАК 32^\nЛИСТ 0-37^\n'
                'ВХОД %o^\nРОСП 0^\n%sВРЕМ 240^\nСПЕЦ^\nЕ\n'
                % (start, 'ЛЕНТ 67(%s)^\n' % vol if vol else ''))
        for base, ws in blocks:
            f.write('В %o\n' % base)
            for w in ws:
                f.write('К %s %s\n' % (kcard(w >> 24), kcard(w & 0o77777777)))
        f.write('ЕКОНЕЦ\n')


def run_stored(a, zs, z0, desc):
    """Job of a stored program: the root and segment --seg, read from the
    volume by its Э70 words; the volume is mounted as ЛЕНТ 67(--vol)."""
    root, start, tab, segs, exports = read_program(zs, z0, desc)
    print('программа: корень 00010-%05o, пуск %05o, таблица сегментов %05o'
          % (0o10 + len(root) - 1, start, tab))
    blocks = [(0o10, root)]
    for s, e in enumerate(segs, 1):
        print('сегмент %d:' % s, ' '.join('%05o<-%o.%o' % unpack_e70(x) for x in e))
        if s == a.seg:
            for x in e:
                addr, z, k = unpack_e70(x)
                blocks.append((addr, zs[z][k * SECTOR:(k + 1) * SECTOR]))
    print('имена:')
    for n, v in exports:
        print('  %-6s %05o' % (itm(n), v))
    if a.out:
        job(blocks, start, a.out, a.vol)


def main():
    ap = argparse.ArgumentParser(description='Загрузчик модулей АИТМ')
    ap.add_argument('key')
    ap.add_argument('lib')
    ap.add_argument('-o', dest='out')
    ap.add_argument('--seg', type=int, default=1)
    ap.add_argument('--common', action='store_true')
    ap.add_argument('--store', nargs=2, metavar=('ИМЯ', 'OUT.vol'))
    ap.add_argument('--vol', default='2222')
    a = ap.parse_args()
    try:
        main_name, segs = parse_key(a.key)
        path, z0 = library(a.lib)
        zs = zones(path)
        cat = catalogue(zs, z0)
        if word(main_name) in cat and not cat[word(main_name)] >> 47:
            if segs or a.store:
                raise LoadError('%s - записанная программа, её не связывают' % main_name)
            return run_stored(a, zs, z0, cat[word(main_name)])
        mods = []
        for s, items in enumerate([[(main_name, 1)]] + segs):
            for j, (n, align) in enumerate(items):
                if word(n) not in cat:
                    raise LoadError('модуля %s нет в каталоге' % n)
                if not cat[word(n)] >> 47:
                    raise LoadError('%s - записанная программа, не модуль' % n)
                md = Module(n, cat[word(n)], zs, z0)
                md.seg, md.align = s, align
                if a.store and s and not j:     # a segment is read by sectors
                    md.align = max(align, SECTOR)
                mods.append(md)
        if segs and not 1 <= a.seg <= len(segs):
            raise LoadError('сегмента %d нет (всего %d)' % (a.seg, len(segs)))
        extra, table = {}, []
        if a.store:
            # The table of Э70 words: its size depends on the placement
            size = -1
            while size != len(table):
                size = len(table)
                end, spans = layout(mods, a.common, size, SECTOR)
                table = [0] * sum(-(-(e - b) // SECTOR) + 1 for b, e in spans.values())
            t = mods[0].base + len(mods[0].image)
            for s in sorted(spans):
                extra[word('СЕГ%d' % s)] = t
                t += -(-(spans[s][1] - spans[s][0]) // SECTOR) + 1
        else:
            end, spans = layout(mods, a.common)
        names = link(mods, extra)
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
        if a.store:
            first, nz = write_program(path, a.store[1], z0, a.store[0], mods, spans,
                                      table, start, names)
            print('записано: %s, зоны %o-%o' % (a.store[0], z0 + first, z0 + first + nz - 1))
    except LoadError as e:
        sys.exit('ОШИБКА ЗАГРУЗЧИКА: %s' % e)
    if a.out:
        job([(md.base, md.image) for md in mods if md.seg in (0, a.seg)], start, a.out)


if __name__ == '__main__':
    main()
