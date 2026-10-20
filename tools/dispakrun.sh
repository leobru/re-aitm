#!/bin/sh
# Run a job under dispak without a trace (as tools/trace.sh, but fast).
# Usage: [VOLIN=in.vol] [VOLOUT=out.vol] [VOL2148=x.2148] [DISPAK_OPTS=--725]
#        tools/dispakrun.sh job.b6 printout.txt
# Volume 2222 is empty or a copy of $VOLIN and is saved to $VOLOUT;
# dispak is killed after 600 seconds.
job=$(realpath "$1"); prn=$(realpath -m "$2")
path=${BESM6_PATH:-/usr/local/share/besm6}
tmp=$(mktemp -d)
if [ -n "$VOLIN" ]; then cp "$VOLIN" "$tmp/2222" && chmod u+w "$tmp/2222"
else touch "$tmp/2222"; fi
cp "$path/2099" "$tmp/2099" && chmod u+w "$tmp/2099"
[ -n "$VOL2148" ] && cp "$VOL2148" "$tmp/2148"
(cd "$tmp" && timeout -s KILL 600 dispak $DISPAK_OPTS --path=.:$path "$job" > prn.txt 2>&1)
cp "$tmp/prn.txt" "$prn"
[ -n "$VOLOUT" ] && cp "$tmp/2222" "$VOLOUT"
rm -rf "$tmp"
