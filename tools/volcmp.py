#!/usr/bin/env python3
"""Compare the data words of two dispak volume images zone by zone.

Usage: tools/volcmp.py a.vol b.vol

Used for the library written by the BEMSH loader (zagr/) against the one
tools/itmload.py --store writes for the same key.  Prints each zone that
differs with its first differing word; exit status 1 if any differ.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vol import zones  # noqa: E402

a, b = zones(sys.argv[1]), zones(sys.argv[2])
bad = len(a) != len(b)
for z in range(min(len(a), len(b))):
    d = [i for i in range(1024) if a[z][i] != b[z][i]]
    if d:
        print('зона %o: различий %d, первое в слове %04o: %016o %016o'
              % (z, len(d), d[0], a[z][d[0]], b[z][d[0]]))
        bad = True
print('зон %d и %d, %s' % (len(a), len(b), 'различаются' if bad else 'совпадают'))
sys.exit(1 if bad else 0)
