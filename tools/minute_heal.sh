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
# Refresh the local savings reading. A failure here must not fail the heal.
python3 "$HERE/analytics_savings_refresh.py" >/dev/null 2>&1 || true
python3 "$HERE/p0_settings_check.py" || true
python3 "$HERE/savings_chunk_check.py" || true
python3 "$HERE/guard_alert.py" || true
exit 0
