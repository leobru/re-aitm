#!/usr/bin/env python3
# Build the parts listed in parts.txt: parts/NAME.bin (zones or sectors
# ZZZZ.S concatenated), parts/NAME.cov (union of traces/*.cov/ZZZZ.S.cov for
# its sectors), parts/NAME.sym (marks from notes/NAME.py), parts/NAME.dis
# (raw disbesm6 -s output, module name from parts.txt) and parts/NAME.adr
# (disbesm6 with addresses and codes). A spec -NNNN (octal) is a gap of
# NNNN words that are not taken from a zone: zeros in the image (ПАМ in the
# source), e.g. the pager windows inside a part.
# Usage: tools/parts.py [name ...]     (default: all)
import glob, os, re, subprocess, sys

def notes(name):
    fn = 'notes/%s.py' % name
    g = {}
    if os.path.exists(fn):
        exec(open(fn).read(), g)
    return g


def sectors(spec):
    """'0406' -> 0406.0-3, '0411.1' -> 0411.1: [(zone, sector)];
    '-2000' -> a gap of 02000 words: [(None, number of words)]."""
    if spec.startswith('-'):
        return [(None, int(spec[1:], 8))]
    z, _, s = spec.partition('.')
    return [(z, int(s))] if s else [(z, i) for i in range(4)]


def sector_data(z, s):
    return open('zones/%s.bin' % z, 'rb').read()[s * 1536:(s + 1) * 1536]


DIS = os.environ.get('DISBESM6', os.path.expanduser('~/git/leobru/dispak-tools/disbesm6'))
os.makedirs('parts', exist_ok=True)
for l in open('parts.txt'):
    if l.startswith('#') or not l.strip():
        continue
    name, mod, addr, *specs = l.split()
    if len(sys.argv) > 1 and name not in sys.argv[1:]:
        continue
    secs = [x for spec in specs for x in sectors(spec)]
    with open('parts/%s.bin' % name, 'wb') as f:
        for z, s in secs:
            f.write(bytes(6 * s) if z is None else sector_data(z, s))
    cov = set()
    for z, s in secs:
        if z is None:
            continue
        for c in glob.glob('traces/*.cov/%s.%d.cov' % (z, s)):
            cov.update(x.split(':')[0] for x in open(c))
    with open('parts/%s.cov' % name, 'w') as f:
        f.writelines('%s: L\n' % a for a in sorted(cov))
    n = notes(name)
    # without coverage the entries are ENTRIES of the notes (if given)
    entry = [min(cov)] if cov else [] if 'ENTRIES' in n else [addr]
    # SYMS = ['ааааа[-ббббб] Т', ...]: disbesm6 types (M - текст ИТМ,
    # C - код, B - начало блока кода, A - код без входа потоком, D - данные);
    # STOPS = ['ааааа', ...]: данные сразу после кода
    sym = ['%s -\n' % x for x in n.get('SYMS', [])]
    sym += ['%s A -\n' % a for a in n.get('STOPS', [])]
    # the start of a gap gets a label (Dааааа: data, named by NAMES)
    gpos = int(addr, 8)
    for z, k in secs:
        if z is None:
            sym.append('%05o D D%05o\n' % (gpos, gpos))
        gpos += 256 if z is not None else k
    opts = ['-e' + e for e in n.get('ENTRIES', [])]
    if sym:
        open('parts/%s.sym' % name, 'w').writelines(sym)
        opts.append('-nparts/%s.sym' % name)
    elif os.path.exists('parts/%s.sym' % name):
        os.remove('parts/%s.sym' % name)
    args = ['-a' + addr] + ['-e' + e for e in entry] + opts + [
        '--trace=parts/%s.cov' % name, 'parts/%s.bin' % name]
    # parts/NAME.adr: the same with addresses and codes, for reading
    with open('parts/%s.adr' % name, 'w') as f:
        subprocess.run([DIS] + args, stdout=f, check=True)
    out = subprocess.run([DIS, '-s'] + args,
                         stdout=subprocess.PIPE, check=True).stdout.decode()
    with open('parts/%s.dis' % name, 'w') as f:
        # the first word carries the module name, not a D/G label
        # (disbesm6 starts an image loaded at 0 from word 1)
        start = int(addr, 8) or 1
        if int(addr, 8) == 0:
            # an indexed operand below 0100 is a number, not an address of
            # the image (СЛИА 1(М3) comes out as СЛИА G00001(М3))
            # (not in jumps, where it is an address); with УИА too: a counter
            out = re.sub(r'(?m)^(\S*\t(?!пио|пино|цикл|пв|пб|по|пе)\S+\t)[GD]000([0-7]{2})([+-]\d+)?(\(М)',
                         lambda m: m.group(1) + str(int(m.group(2), 8) + int(m.group(3) or 0))
                         + m.group(4) if int(m.group(2), 8) + int(m.group(3) or 0) < 0o100
                         else m.group(0), out)
        out = re.sub(r'(?<![А-Я0-9])[GD]%05o(?![0-7])' % start, mod, out)
        # an address inside a gap is the gap label plus offset (Dааааа of the
        # gap start, named in NAMES if wanted): one ПАМ with one label
        gaps = []
        pos = int(addr, 8)
        for z, n in secs:
            if z is None:
                gaps.append((pos, pos + n))
            pos += 256 if z is not None else n
        def gapof(x):
            return next((lo for lo, hi in gaps if lo <= x < hi), None)
        def rel(m):
            x = int(m.group(1), 8) + int(m.group(2) or 0)
            lo = gapof(x)
            if lo is None:
                return m.group(0)
            return 'D%05o' % lo + ('+%d' % (x - lo) if x > lo else '')
        if gaps:
            out = re.sub(r'(?<![А-Я0-9])[GD]([0-7]{5})([+-]\d+)?(?![0-7])', rel, out)
            # labels inside a gap (now Dгггг+n): dropped
            out = re.sub(r'(?m)^D[0-7]{5}\+\d+\t', '\t', out)
            # the ПАМ that disbesm6 split at such a label: one ПАМ again
            pat = re.compile(r'(?m)^(\S*)\tпам\t(\d+)\n\tпам\t(\d+)$')
            while pat.search(out):
                out = pat.sub(lambda m: '%s\tпам\t%d' % (m.group(1), int(m.group(2)) + int(m.group(3))), out)
            for lo, hi in gaps:
                if not re.search(r'(?m)^D%05o\t' % lo, out):
                    print('%s: no label at the gap %05o' % (name, lo), file=sys.stderr)
        f.write(out.replace('НЕИМЯ\tСТАРТ', mod + '\tСТАРТ', 1))
    print('%-7s %s %s: %d адресов исполнялось' % (name, addr, ' '.join(specs), len(cov)))
