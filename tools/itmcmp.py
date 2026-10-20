#!/usr/bin/env python3
"""Compare modules translated from itm/*.itm (tools/be2itm.py) with the parts.

Usage: tools/itmcmp.py module LIB NAME      one module of the library at
                                            its НАЗ, external names from
                                            the labels of all parts
       tools/itmcmp.py stored LIB NAME      a program stored by zagr or
                                            itmload --store: root and
                                            every segment
Run in the repository root.  Compares every part of parts.txt that the
module or program holds with parts/PART.bin (word 0 of a part at 0 is not
compared) and prints the differences; exit status 1 if there are any.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import be2itm                                   # noqa: E402
import itmload                                  # noqa: E402
from vol import zones                           # noqa: E402

M48 = (1 << 48) - 1


def part_words():
    """{part: (address, words)} of parts.txt."""
    return {p: (a, be2itm.words(p)) for p, (m, a, n) in be2itm.PARTS.items()
            if p in be2itm.MODULE}


def compare(mem, parts, label, which):
    """mem: {address: word}; compare the parts in which."""
    bad = 0
    for p, (a, ws) in parts.items():
        if p not in which:
            continue
        got = [mem.get(a + i) for i in range(len(ws))]
        diff = [i for i in range(1 if a == 0 else 0, len(ws)) if got[i] != ws[i]]
        print('%s %-5s %05o-%05o: различий %d' % (label, p, a, a + len(ws) - 1, len(diff)))
        for i in diff[:8]:
            print('    %05o  получено %s  часть %016o' % (
                a + i, '%016o' % got[i] if got[i] is not None else '-' * 16, ws[i]))
        bad += len(diff)
    return bad


def main():
    mode, lib, name = sys.argv[1:4]
    path, z0 = itmload.library(lib)
    zs = zones(path)
    cat = itmload.catalogue(zs, z0)
    if itmload.word(name) not in cat:
        sys.exit('%s нет в каталоге' % name)
    parts = part_words()
    if mode == 'module':
        md = itmload.Module(name, cat[itmload.word(name)], zs, z0)
        itmload.layout([md], False)
        labels = {}                         # the external names of the module
        for p in parts:
            if be2itm.MODULE[p] == name:
                for x, q in be2itm.layout(p)[3].items():
                    labels[itmload.word(x)] = be2itm.layout(q)[1][x]
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):   # repeated names
            itmload.link([md], labels)
        mem = {md.base + i: w for i, w in enumerate(md.image)}
        bad = compare(mem, parts, name, [p for p in parts if be2itm.MODULE[p] == name])
    else:
        root, start, tab, segs, exports, img = itmload.read_program(zs, z0, cat[itmload.word(name)])
        seg = {p: be2itm.SEG[be2itm.MODULE[p]] for p in parts}
        bad = compare(dict(enumerate(root)), parts, 'корень', [p for p in parts if seg[p] == 0])
        for s, e in enumerate(segs, 1):
            mem = {}
            for x in e:
                a, z, k = itmload.unpack_e70(x)
                for i in range(0o400):
                    mem[a + i] = zs[z][k * 0o400 + i]
            bad += compare(mem, parts, 'сегмент %d' % s, [p for p in parts if seg[p] == s])
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
