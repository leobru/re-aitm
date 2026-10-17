#!/bin/sh
# Run a job under the dispak debugger with a full instruction trace ("t2")
# and print the user-mode trace lines to stdout (feed them to phases.py).
# Usage: [VOLIN=in.vol] [VOLOUT=out.vol] tools/trace.sh job.b6 [output.txt] |
#            tools/phases.py - covdir
# Runs in a temporary directory with a private copy of 2099 and a 2222
# that is empty or a copy of $VOLIN; the resulting 2222 is saved to
# $VOLOUT.  $VOL2148, if set, is used as volume 2148 (ЛЕНТ 40), $VOL2048
# as volume 2048.
# dispak is killed after 60 seconds.
job=$(realpath "$1"); prn=${2:+$(realpath -m "$2")}
path=${BESM6_PATH:-/usr/local/share/besm6}
tmp=$(mktemp -d)
if [ -n "$VOLIN" ]; then cp "$VOLIN" "$tmp/2222" && chmod u+w "$tmp/2222"
else touch "$tmp/2222"; fi
cp "$path/2099" "$tmp/2099" && chmod u+w "$tmp/2099"
[ -n "$VOL2148" ] && cp "$VOL2148" "$tmp/2148"
[ -n "$VOL2048" ] && cp "$VOL2048" "$tmp/2048"
(cd "$tmp" && printf 't2\ng\nq\n' |
    sh -c 'echo $$ >pid; exec dispak "$@"' sh --path=.:$path -b "$job" 2>&1 >prn.txt |
    grep -E '^[0-7]{5}:') &
run=$!
(sleep 60; kill -9 $(cat "$tmp/pid")) >/dev/null 2>&1 &
dog=$!
wait $run
kill $dog 2>/dev/null
[ -n "$prn" ] && cp "$tmp/prn.txt" "$prn"
[ -n "$VOLOUT" ] && cp "$tmp/2222" "$VOLOUT"
rm -rf "$tmp"
