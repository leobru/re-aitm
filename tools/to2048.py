#!/usr/bin/env python3
# Convert a job for the АИТМ build on 2148 (jobs/*.b6: ФИЗО МБ21, ЛЕНТ
# 40(2148), loader at 04237, text from 020000) into a job for the older
# build on 2048 (v2048/aitm-2048.b6: ЛЕНТ 40(2048), loader at 040000 that
# reads zones 055-060 into 0-07777 and puts pages 010000-017777 on drum 23,
# text from 010000). Other passport lines (ЛЕНТ 30/31/67 ...) are kept.
# Usage: tools/to2048.py jobs/NAME.b6 > v2048/jobs/NAME.b6
import sys

LOADER = '''Е
В 40000
К 01 24 40000 00 010 0003
К 00 040 0002 01 070 0040
К 01 070 0041
К 01 070 0042
К 01 070 0043
К 01 070 0030
К 01 070 0031
К 01 070 0032
К 01 070 0033
К 01 24 00000 00 042 0002
К 02 24 00000 00 30 00010
В 40030
С 0010 0000 0040 0055
С 0010 0100 0040 0056
С 0010 0200 0040 0057
С 0010 0300 0040 0060
В 40040
С 0000 0400 0023 0000
С 0000 0500 0023 0001
С 0000 0600 0023 0002
С 0000 0700 0023 0003
В 10000
'''

lines = open(sys.argv[1], encoding='utf-8').read().split('\n')
end = lines.index('В 20000')
hdr = lines[:lines.index('Е')]
out = []
for l in hdr:
    if l.startswith('ВХОД'):
        l = 'ВХОД 40000^'
    elif l.startswith('ФИЗО'):
        continue
    elif l.startswith('ЛЕНТ 40('):
        l = 'ЛЕНТ 40(2048)^'
    out.append(l)
sys.stdout.write('\n'.join(out) + '\n' + LOADER + '\n'.join(lines[end + 1:]))
