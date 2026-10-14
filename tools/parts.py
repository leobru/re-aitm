#!/usr/bin/env python3
# Build the parts listed in parts.txt: parts/NAME.bin (zones or sectors
# ZZZZ.S concatenated), parts/NAME.cov (union of traces/*.cov/ZZZZ.S.cov for
# its sectors), parts/NAME.sym (marks from notes/NAME.py), parts/NAME.dis
# (raw disbesm6 -s output, module name from parts.txt) and parts/NAME.adr
# (disbesm6 with addresses and codes).
# Usage: tools/parts.py [name ...]     (default: all)
import glob, os, re, subprocess, sys

def notes(name):
    fn = 'notes/%s.py' % name
    g = {}
    if os.path.exists(fn):
        exec(open(fn).read(), g)
    return g


def sectors(spec):
    """'0406' -> 0406.0-3, '0411.1' -> 0411.1: [(zone, sector)]."""
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
            f.write(sector_data(z, s))
    cov = set()
    for z, s in secs:
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
        f.write(out.replace('НЕИМЯ\tСТАРТ', mod + '\tСТАРТ', 1))
    print('%-7s %s %s: %d адресов исполнялось' % (name, addr, ' '.join(specs), len(cov)))
