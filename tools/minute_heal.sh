#!/bin/bash
# Minute self-heal. The runner loop calls this.
# Reapplies the no-key guard and reruns the lost-key test.
# Exits 1 when an OmniRoute update wiped the guard and the patch did not restore it.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$HERE/recur.py" --minute
