#!/usr/bin/env python3
"""Rewrite a part of АИТМ 2148 from BEMSH (parts/NAME.be) into ITM autocode.

Usage: tools/be2itm.py > itm/NAME.itm ...   (see itm/Makefile)
       tools/be2itm.py PART [PART...] [-o FILE]

The text translates (key Р) into a library module whose image, linked by
zagr or tools/itmload.py at its address (entry НАЗ), is the part word for
word.  Several parts can make one module (Н; between them).  The root is
АИТМ (aitm0, the main module) and АИТМ6 (aitm6, НАЗ 06400): a list
module with НАЗ that overlaps no other group, which the loaders put in
the root.  One root module of 1-06777 would be too long for ВЫВМ to keep
its literals (AITM-object.md, section 8).

Input: parts.txt (address, zones), parts/NAME.be (labels, operands),
parts/NAME.be.lst (the BEMSH listing: address and half of every source
line) and parts/NAME.bin (the words).  Every word becomes one statement:
- a command word (commands, кк, дк, конк halves): К; with both halves
  decoded from the binary - index register, ITM mnemonic or Эnnn / Эnn,
  address.  The address is symbolic when the BEMSH operand names a
  label (label(n) for label+n), so ITM marks it relocatable or external;
  otherwise it is the octal number (negative for bit 19 of a short
  command);
- a data word (конд, текст, пам): С; with its 16 octal digits; a word
  the BEMSH comment marks as ITM text (ITM '...') becomes А; with its
  six characters, decoded from the binary, if each of them can be typed
  on a card (not 040, 0140 КИ, 0142 ПОЗ, 0173 ПС: their glued ':' input
  is the terminal's, dispak decks have none); such a word stays in С;
  with the comment as an ITM note ‘...‘.
- a table of packed 12-bit addresses (PACKED; BEMSH has no such
  constant, the part writes its octal digits): Л; with a К field per
  non-zero address, label(n) of the root or of ФАЗ2А, so the addresses
  are relocated and linked like those of commands.
Labels of the part stay on their words.  Labels other parts use are
marked * (entries, exported with key Г from the inner block).  Labels of
other parts become external names (Э; X:Н=X) - except between different
overlay segments (ФАЗ2В and phase 2), where the fixed address is written
as a number.
"""
import os
import re
import sys

PARTS = {}                      # name -> (module, address, words)
for l in open('parts.txt', encoding='utf-8'):
    if l.startswith('#') or not l.strip():
        continue
    n, mod, a, *zs = l.split()
    size = sum(0o400 if '.' in z else 0o2000 for z in zs)
    PARTS[n] = (mod, int(a, 8), size)

# Modules of the linked translator and their overlay segment (0 = root)
MODULE = {'aitm0': 'АИТМ', 'aitm6': 'АИТМ6', 'f1a': 'ФАЗ1А', 'f1b': 'ФАЗ1Б',
          'f2a': 'ФАЗ2А', 'f2b': 'ФАЗ2Б', 'f2c': 'ФАЗ2В'}
# z14 (0414.3) is not part of the translator: the leftover of the loader's
# zone, which zagr replaces
SEG = {'АИТМ': 0, 'АИТМ6': 0, 'ФАЗ1А': 1, 'ФАЗ1Б': 1, 'ФАЗ2А': 2, 'ФАЗ2Б': 2,
       'ФАЗ2В': 3}

SHORT = {0o00: 'ЗП', 0o01: 'ЗМ', 0o03: 'СМ', 0o04: 'АС', 0o05: 'АВ', 0o06: 'ОВ',
         0o07: 'МВ', 0o10: 'СЧ', 0o11: 'ЛУ', 0o12: 'СР', 0o13: 'ЦС', 0o14: 'ИЗ',
         0o15: 'ЛС', 0o16: 'АД', 0o17: 'АУ', 0o20: 'СБ', 0o21: 'РБ', 0o22: 'ВЧ',
         0o23: 'ВН', 0o24: 'СП', 0o25: 'ВП', 0o26: 'СК', 0o27: 'РК', 0o30: 'ВР',
         0o31: 'МР', 0o34: 'КС', 0o35: 'КВ', 0o36: 'СД', 0o37: 'РА', 0o40: 'УИ',
         0o41: 'УМ', 0o42: 'ВИ', 0o43: 'ВМ', 0o44: 'ПИ', 0o45: 'СИ'}
LONG = {0o22: 'ИА', 0o23: 'ИК', 0o24: 'ПА', 0o25: 'СА', 0o26: 'У0', 0o27: 'У1',
        0o30: 'ПБ', 0o31: 'ПВ', 0o34: 'И0', 0o35: 'И1', 0o37: 'КЦ'}
DATA = {'конд', 'текст', 'пам'}
# Tables of four 12-bit addresses a word: part -> (first, last + 1).
# ТОШПР, the continuation after error code n (word n/4, field n%4 from
# the left); the addresses from 04000 are in ФАЗ2А, whose errors these are
PACKED = {'aitm0': (0o1566, 0o1606)}
FIELDS = (0o44, 0o30, 0o14, 0)              # /M of the К fields
# ITM codes of the characters an А; constant may hold: letters, digits,
# space (017) and a few signs, from itm-encoding.txt
TEXT = {}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                           'itm-encoding.txt'), encoding='utf-8'):
    f = l.split()
    if f and re.fullmatch(r'[0-7]{3}', f[0]):
        c = ' ' if f[1] == '<space>' else f[1]
        if len(c) == 1 and (c.isalnum() or c in ' ._-()+/'):
            TEXT[int(f[0], 8)] = c


def text(w):
    """The six characters of an ITM text word, or None."""
    cs = [TEXT.get(w >> 40 - 8 * i & 0o377) for i in range(6)]
    return None if None in cs else ''.join(cs)


def words(name):
    b = open('parts/%s.bin' % name, 'rb').read()
    return [int.from_bytes(b[i:i + 6], 'big') for i in range(0, len(b), 6)]


BYMOD = {m: p for p, (m, a, n) in PARTS.items()}


def layout(name):
    """{address: [left src, right src] or ('data', src)}, labels
    {name: address}, source lines and external names {name: (part, its
    name there)} (from
    the внеш lines) of a part, from its listing and source."""
    src = open('parts/%s.be' % name, encoding='utf-8').read().split('\n')
    lay, labels = {}, {}
    ext = {}
    for l in src:
        f = l.split('\t')
        if len(f) > 2 and f[1] == 'внеш':
            # ИМЯ or (СВОЕ,ВНЕШНЕЕ): the own name of an external one
            for x, y, z in re.findall(r'\(([^,()]+),([^,()]+)\)|([^,()]+)', f[2]):
                ext[(x or z).strip()] = (BYMOD[f[0]], (y or z).strip())
    addr, half = None, 0
    for l in open('parts/%s.be.lst' % name, encoding='utf-8'):
        a, code, n = l[25:30], l[31:48], l[55:59]
        if len(l) < 31 or l[24] != ' ' or not re.fullmatch(r'[0-7]{5}| {5}', a) \
                or not code.strip() and not a.strip() \
                or not re.fullmatch(r'[ 0-7]*', code.rstrip('\n')):
            continue                    # comments, pseudo-operations, headers
        n = int(n) if n.strip().isdigit() else None
        f = src[n - 1].split('\t') if n else ['', '', '']
        op = f[1] if len(f) > 1 else ''
        if a.strip():
            addr, half = int(a, 8), 0
        if addr is None:
            continue
        if n and f[0] and op not in ('внеш', 'старт', 'СТАРТ'):
            labels.setdefault(f[0], addr)
        if op == 'пам':
            for i in range(int(f[2])):
                lay[addr + i] = ('data', None if i else n)
            addr += int(f[2]) - 1
            half = 2
            continue
        if re.fullmatch(r' [0-7]{16}', code[:17]) or (not n and not code.strip()):
            lay[addr] = ('data', n)
            half = 2
            continue
        if not code.strip():
            continue
        if half == 2:
            addr += 1
            half = 0
        w = lay.setdefault(addr, [None, None])
        if isinstance(w, tuple):
            continue
        w[half] = n
        half += 1
        if half == 2:
            pass
    for l in src:                   # ИМЯ ЭКВ МЕТКА: a second label
        m = re.fullmatch(r'(\S+)\tэкв\t([А-ЯA-Z][А-ЯA-Z0-9]*)', l)
        if m and m.group(2) in labels:
            labels[m.group(1)] = labels[m.group(2)]
    return lay, labels, src, ext


def note(t):
    """A comment as ITM notes ‘...‘ of at most 35 characters: the listing
    prints a note in columns 62-96, the address and code overwrite the
    rest, and only the first note after a statement is printed;
    capitals, only characters a card can carry (‘ ends a note); no '!'
    and ';': phase 1 looks for the end of the text and for sections Б;
    without regard to notes."""
    t = ' '.join(t.upper().replace('Ё', 'Е').split())
    for a, b in (('‘', '"'), ("'", '’'), ('«', '"'), ('»', '"'),
                 ('{', '('), ('}', ')'), ('?', ''), ('!', 'ВОСКЛ.'), (';', '.')):
        t = t.replace(a, b)
    out = []
    while t:
        cut = len(t) if len(t) <= 35 else (t.rfind(' ', 0, 36) if ' ' in t[:36] else 35)
        out.append('‘%s‘' % t[:cut].strip())
        t = t[cut:].strip()
    return out


def comments(p, src):
    """Comments of part p: {source line: block comment lines before it},
    {source line: its end-of-line comment}, {label: NAMES comment}."""
    block, inline, names = {}, {}, {}
    run = []
    for i, l in enumerate(src, 1):
        if l.startswith('*'):
            if l.strip('* ') and not re.search('[a-z]', l):    # not disbesm6's
                run.append(l[1:].strip())
            continue
        f = l.split('\t')
        if run and len(f) > 1 and f[1] not in ('внеш', 'вход'):
            block[i] = run
        run = []
        if len(f) > 3 and f[1] not in ('конд', 'текст') and ' '.join(f[3:]).strip():
            inline[i] = ' '.join(f[3:]).strip()
    pat = r"^ '([0-7]{5})': '([^']+)',\s*# (.*)$"
    fn = 'notes/%s.py' % p
    if os.path.exists(fn):
        for a, n, c in re.findall(pat, open(fn, encoding='utf-8').read(), re.M):
            names[n] = c
    return block, inline, names


def operand_syms(text):
    """Names in a BEMSH operand (quoted constants removed)."""
    text = re.sub(r"[мМ]?\d*[впхВПХ]?'[^']*'", ' ', text or '')
    return re.findall(r"[A-ZА-ЯЁ][A-ZА-ЯЁ0-9]*", text)


def main():
    args = [a for a in sys.argv[1:]]
    out = sys.stdout
    if '-o' in args:
        i = args.index('-o')
        out = open(args[i + 1], 'w', encoding='utf-8')
        del args[i:i + 2]
    parts = args
    module = MODULE[parts[0]]
    lays = {p: layout(p) for p in PARTS if p in MODULE}

    def owner(p, x):
        """(part, address) of name x used in part p, or None."""
        lay, labels, src, ext = lays[p]
        if x in labels:
            return p, labels[x]
        if x in ext:
            return ext[x][0], lays[ext[x][0]][1][ext[x][1]]
        return None

    def xname(p, x):
        """The name in its owner of name x used in part p."""
        return lays[p][3].get(x, (None, x))[1]
    def packed(p, w):
        """[(field, part, label, offset)] of a packed address word."""
        fs = []
        for m in FIELDS:
            v = w >> m & 0o7777
            if v:
                q = 'f2a' if v >= 0o4000 else p
                a, x = max((a, x) for x, a in lays[q][1].items() if a <= v)
                fs.append((m, q, x, v - a))
        return fs
    # names every part uses from other modules, and the entries they need
    used, exported = {}, set()
    for p, (f, l) in PACKED.items():
        ws = words(p)
        for a in range(f, l):
            for m, q, x, off in packed(p, ws[a - PARTS[p][1]]):
                if q != p:
                    used.setdefault(p, set()).add(x)
                    exported.add((q, x))
    for p, (lay, labels, src, ext) in lays.items():
        for a, w in lay.items():
            for n in ([w[1]] if isinstance(w, tuple) else w):
                f = src[n - 1].split('\t') if n else []
                for x in operand_syms(f[2] if len(f) > 2 else ''):
                    o = owner(p, x)
                    if not o or MODULE[o[0]] == MODULE[p]:
                        continue
                    sp, so = SEG[MODULE[p]], SEG[MODULE[o[0]]]
                    if so == 0 or sp == 0 or so == sp:
                        used.setdefault(p, set()).add(x)
                        exported.add((o[0], xname(p, x)))
    # a shared entry of phases (a list in SEGREF of tools/mkbe.py notes):
    # the same label at the same address, every part of the list exports it
    from mkbe import load_notes
    for p in lays:
        for a, u in load_notes(p).get('SEGREF', {}).items():
            if isinstance(u, list):
                for q in u:
                    exported.add((q, next(x for x, v in lays[q][1].items()
                                          if v == int(a, 8))))
    base = PARTS[parts[0]][1] or 1          # aitm0: word 0 is not loaded
    externals = sorted({(x, xname(p, x)) for p in parts for x in used.get(p, ())})
    body = ['В;']                   # before it the translator reads keys
    for p in parts:
        fn = 'notes/%s.py' % p
        if os.path.exists(fn):
            body += note(open(fn, encoding='utf-8').readline().lstrip('# '))
    body += ['Э;НАЗ:П=%o,' % base]
    for i in range(0, len(externals), 3):
        body.append('Э;' + ''.join('%s:Н=%s,' % s for s in externals[i:i + 3]))
    body.append('В;')
    section = None
    for k, p in enumerate(parts):
        lay, labels, src, ext = lays[p]
        ws = words(p)
        start = PARTS[p][1]
        first = 1 if start == 0 else 0
        if k:
            body.append('Н;%o,' % (start + 0o10 - base))
            section = None
        at = {}                     # address -> its labels, own one first
        for n, v in labels.items():
            at.setdefault(v, []).append(n)
        block, inline, names = comments(p, src)

        def tail(st, labs, ns):
            """The statement with the comments of its labels and lines."""
            cs = [names[x] for x in labs if x in names] + \
                [inline[n] for n in ns if n in inline]
            ls = note('; '.join(cs)) if cs else []
            if ls and len(st) + len(ls[0]) <= 72:
                return [st + ls[0]] + ls[1:]
            return [st] + ls
        for i in range(first, len(ws)):
            a = start + i
            w = ws[i]
            lab0 = at.get(a, [])
            lab = ''.join(('*' if (p, x) in exported else '') + x + ':' for x in lab0)
            entry = lay.get(a)
            ns = [n for n in ([entry[1]] if isinstance(entry, tuple) else entry or []) if n]
            if ns and ns[0] in block:
                body += note(' '.join(block[ns[0]]))
            if p in PACKED and PACKED[p][0] <= a < PACKED[p][1]:
                if section != 'Л':
                    body.append('Л;')
                    section = 'Л'
                body.append('%s%s,' % (lab, '='.join(
                    'К%s%s/%o' % (x, '(%o)' % off if off else '', m)
                    for m, q, x, off in packed(p, w))))
                continue
            if entry is None or isinstance(entry, tuple):
                n = entry and entry[1]
                t = n and "ITM '" in src[n - 1] and text(w)
                if t and section != 'А':
                    body.append('А;')
                    section = 'А'
                elif not t and section != 'С':
                    body.append('С;')
                    section = 'С'
                c = n and not t and re.search(r"ITM '(.*)'", src[n - 1])
                if c:
                    body.append('%s%s,‘%s‘' % (lab, '%o' % w, c.group(1)))
                else:
                    body += tail('%s%s,' % (lab, t or '%o' % w), lab0, [])
                continue
            halves = []
            for h, n in zip((w >> 24, w & 0o77777777), entry):
                halves.append(half(h, n and src[n - 1].split('\t'), p, owner, used))
            if section != 'К':
                body.append('К;')
                section = 'К'
            body += tail('%s%s=%s,' % (lab, halves[0], halves[1]), lab0, ns)
    body += ['Е;', 'Е;']
    print('\n'.join(body), file=out)


def half(h, f, part, owner, used):
    if h == 0:
        return ''                           # empty half: '=X,' or 'X=,'
    ir = (h >> 20) & 0o17
    if h & 1 << 19:
        op = 0o20 | (h >> 15) & 0o17
        mn = LONG.get(op, 'Э%02o' % op)
        addr, bits = h & 0o77777, 15
    else:
        op = (h >> 12) & 0o77
        mn = SHORT.get(op, 'Э%03o' % op)
        addr = h & 0o7777 | (0o70000 if h & 1 << 18 else 0)
        bits = 12
    a = None
    for s in operand_syms(f[2] if f and len(f) > 2 else ''):
        o = owner(part, s)
        if not o:
            continue
        q, v = o
        if MODULE[q] != MODULE[part] and s not in used.get(part, ()):
            continue                        # other segment: the number
        off = (addr - v) & 0o77777
        if off >= 0o40000:
            off -= 0o100000
        a = s if not off else '%s(%s)' % (s, '%o' % off if off > 0 else '-%o' % -off)
        break
    if a is None:
        if addr == 0:
            a = ''
        elif addr >= 0o70000:
            a = '-%o' % (0o100000 - addr)
        else:
            a = '%o' % addr
            if mn.startswith('Э'):
                a = '+' + a
    return ('%o' % ir if ir else '') + mn + a


if __name__ == '__main__':
    main()
