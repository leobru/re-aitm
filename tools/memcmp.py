#!/usr/bin/env python3
"""Compare the memory the BEMSH loader (zagr/) builds with tools/itmload.py.

Usage: VOL2148=traces/zagr.2148 [VOLIN=in.vol] tools/memcmp.py job.b6 ref.b6

job.b6 is a translation job whose key Р with a list ends in the loader of
zone 0414; ref.b6 is the job tools/itmload.py -o writes for the same key.
The job runs under the dispak debugger with a breakpoint at 051776: the
loader's stub stops there after the last page (page 0) is read and
before it jumps to the program.  Every word that ref.b6 loads (В address,
К cards) is then dumped with the debugger and compared.  Prints the
differences; exit status 1 if there are any or the stub was not reached.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

STUB = 0o51776


def ref_words(path):
    words, a = {}, None
    for l in open(path, encoding='utf-8'):
        if re.match(r'^В [0-7]+$', l):
            a = int(l.split()[1], 8)
        elif l.startswith('К ') and a is not None:
            d = re.sub(r'\D', '', l)
            w = 0
            for half in (d[:9], d[9:]):
                h = 0
                for i, c in enumerate(half):
                    h = h << (1 if i == 0 else 2 if i == 2 else 3) | int(c)
                w = w << 24 | h
            words[a] = w
            a += 1
    return words


def main():
    job, ref = sys.argv[1], sys.argv[2]
    want = ref_words(ref)
    blocks = sorted({a & ~7 for a in want})
    path = os.environ.get('BESM6_PATH', '/usr/local/share/besm6')
    tmp = tempfile.mkdtemp()
    try:
        shutil.copy(os.path.join(path, '2099'), tmp)
        if os.environ.get('VOLIN'):
            shutil.copy(os.environ['VOLIN'], os.path.join(tmp, '2222'))
        else:
            open(os.path.join(tmp, '2222'), 'wb').close()
        shutil.copy(os.environ['VOL2148'], os.path.join(tmp, '2148'))
        for f in os.listdir(tmp):
            os.chmod(os.path.join(tmp, f), 0o644)
        cmds = 'b%o\ng\n' % STUB + ''.join('%o-\n' % b for b in blocks) + 'q\n'
        r = subprocess.run(['timeout', '-s', 'KILL', '60', 'dispak',
                            '--path=.:' + path, '-b', os.path.abspath(job)],
                           input=cmds, capture_output=True, text=True, cwd=tmp)
    finally:
        shutil.rmtree(tmp)
    # the debugger's dump goes to stdout, its stop message to stderr
    if not re.search(r'(?m)^ %05o ' % STUB, r.stdout + r.stderr):
        print('останова в %05o нет: загрузчик не дошёл до пуска' % STUB)
        print('\n'.join(l for l in r.stdout.split('\n') if 'ЗАГР' in l))
        sys.exit(1)
    lines = [l for l in r.stdout.split('\n')
             if re.fullmatch(r'(- )?[0-7]{4} [0-7]{4} [0-7]{4} [0-7]{4}', l.strip())]
    lines = lines[len(lines) - 8 * len(blocks):]
    got = {}
    for k, b in enumerate(blocks):
        for i in range(8):
            g = lines[k * 8 + i].strip().lstrip('- ').split()
            got[b + i] = int(''.join(g), 8)
    bad = 0
    for a in sorted(want):
        if got[a] != want[a]:
            print('%05o  загрузчик %016o  itmload %016o' % (a, got[a], want[a]))
            bad += 1
    print('слов %d, различий %d' % (len(want), bad))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
