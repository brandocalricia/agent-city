#!/bin/bash
# Minute self-heal. The runner loop calls this.
# Home center first, then the no-key guard. Exits 1 when either check fails.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/home_error_heal.py"
home_rc=$?
python3 "$HERE/recur.py" --minute
nokey_rc=$?
if [ "$home_rc" -ne 0 ] || [ "$nokey_rc" -ne 0 ]; then
  exit 1
fi
exit 0
