#!/usr/bin/env python3
"""Make a copy of volume 2148 with a probe in zone 0414 (the linking loader).

Usage: tools/mkz14.py [out.2148]        (default traces/z14mock.2148)

ЗАВЕР (aitm6 06517) reads drum 21 zone 014 = 2148:0414 into 0-01777 and
jumps to 011 instead of Э74.  The probe at 011 reads what the loader would
get - М13, М1, eight words from 010000 and four from 013776 - so that the
values appear in a t2 trace, and ends the job with Э74.  The rest of the
zone is left as on 2148.
"""
import os
import struct
import sys

ZONE = 8256                     # 8 control words + 1024 data words
ZONE_OFFSET = 4
M48 = (1 << 48) - 1
SRC = os.path.join(os.environ.get('BESM6_PATH', '/usr/local/share/besm6'), '2148')

PROBE = [                       # (left, right), 24-bit instructions
    (0o00420015, 0o00420001),   # счи М13; счи М1
    (0o12410000, 0o10100000),   # уиа 010000(М2); сч 0(М2)
    (0o10100001, 0o10100002),   # сч 1(М2); сч 2(М2)
    (0o10100003, 0o10100004),
    (0o10100005, 0o10100006),
    (0o10100007, 0o12413776),   # сч 7(М2); уиа 013776(М2)
    (0o10100000, 0o10100001),
    (0o10100002, 0o10100003),
    (0o00740000, 0),            # Э74
]
START = 0o11


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'traces/z14mock.2148'
    b = bytearray(open(SRC, 'rb').read())
    base = (0o414 + ZONE_OFFSET) * ZONE + 8 * 8
    for i, (l, r) in enumerate(PROBE):
        a = base + (START + i) * 8
        old = struct.unpack('<Q', b[a:a + 8])[0]
        b[a:a + 8] = struct.pack('<Q', (old & ~M48) | (l << 24 | r))
        print('%05o  %08o %08o' % (START + i, l, r))
    with open(out, 'wb') as f:
        f.write(b)


main()
