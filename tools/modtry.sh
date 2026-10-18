#!/bin/sh
# Translate an autocode fragment with key Р (2148) on an empty volume 067
# and print the error lines and the decoded module (tools/vol.py).
# Usage: tools/modtry.sh 'Э;ВН:Н=ВНЕШ,К;НАЧ:СЧВН=,' [key]
#        (run in the repository root; the fragment goes between В; and Е;,
#        key defaults to РАНГКW,МОД!)
here=$(cd "$(dirname "$0")/.." && pwd)
tmp=$(mktemp -d)
{ sed -n '1,/^А0$/p' "$here/jobs/ext1.b6"
  printf '%s\nВ;\n%s\nЕ;\n!_$\nЕКОНЕЦ\n' "${2:-РАНГКW,МОД!}" "$1"; } > "$tmp/job.b6"
VOLOUT=$tmp/vol "$here/tools/trace.sh" "$tmp/job.b6" "$tmp/prn.txt" > /dev/null
grep -E 'ОШИБКА' "$tmp/prn.txt"
[ -s "$tmp/vol" ] && "$here/tools/vol.py" "$tmp/vol" 2>/dev/null
rm -rf "$tmp"
