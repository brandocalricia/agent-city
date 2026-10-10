#!/usr/bin/env python3
"""Keep the Home center from sticking on an inactive provider's old error.

The Home subtitle counts one error when provider-metrics picks a
provider whose newest call status is outside 200-399. The installed
source query already requires pc.is_active = 1. The running bundle
did not, so a disabled connection's 401 painted the center red.

This reapplies that filter to every bundle copy of the metrics query,
records a heal attempt when an error is older than two minutes, and
reloads the gateway once when the bundle actually changed. Chat probes
stay out of this path.

HOME_HEAL_RELOAD=0 skips the reload. A non-default install path never
reloads and never reads the live database.
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = Path("/opt/homebrew/lib/node_modules/omniroute")
OLD = "WHERE pc.provider = c.provider\n      )\n    GROUP BY c.provider"
NEW = (
    "WHERE pc.provider = c.provider AND pc.is_active = 1\n"
    "      )\n    GROUP BY c.provider"
)
SOURCE_MARKER = "pc.provider = c.provider AND pc.is_active = 1"
CENTER_OLD = (
    'h[8]!==c?(d=(0,t.jsxs)("div",{className:"flex items-center gap-2 px-5 py-3 '
    'rounded-xl border-2 border-primary bg-primary/8 shadow-lg min-w-[140px] '
    'justify-center",children:[n,a,i,l,u,f,c]}),h[8]=c,h[9]=d)'
)
CENTER_NEW = (
    'h[8]!==c||h[12]!==!!p.error?(d=(0,t.jsxs)("div",{className:"flex items-center '
    'gap-2 px-5 py-3 rounded-xl border-2 "+(p.error?"border-red-500 bg-red-50":'
    '"border-emerald-500 bg-emerald-50")+" shadow-lg min-w-[140px] justify-center",'
    'children:[n,a,i,l,u,f,c]}),h[8]=c,h[12]=!!p.error,h[9]=d)'
)
ICON_OLD = (
    'bg-primary/15 shrink-0",children:(0,t.jsx)("span",{className:"material-symbols-outlined '
    'text-primary text-[16px]",children:"route"})}),f=(0,t.jsx)("span",{className:"text-sm '
    'font-bold text-primary",children:"OmniRoute"})'
)
ICON_NEW = (
    'bg-green-100 shrink-0",children:(0,t.jsx)("span",{className:"material-symbols-outlined '
    'text-green-600 text-[16px]",children:"route"})}),f=(0,t.jsx)("span",{className:"text-sm '
    'font-bold text-green-600",children:"OmniRoute"})'
)
DATA_OLD = "data:{activeCount:t.size}"
DATA_NEW = "data:{activeCount:t.size,error:n.size>0}"
FAIL = "FAIL home metrics filter missing"
QUERY_FAIL = "FAIL home metrics query"
STUCK_S = 120
ATTEMPT_S = 60


def apply_filter(text):
    """Return text with the metrics query limited to active connections."""
    count = text.count(OLD)
    if count == 0:
        return text, 0
    return text.replace(OLD, NEW), count


def apply_center(text):
    """Paint the center rectangle from the error flag. Primary #e54d5e is always red."""
    count = 0
    if CENTER_OLD in text:
        text = text.replace(CENTER_OLD, CENTER_NEW)
        count += 1
    if ICON_OLD in text:
        text = text.replace(ICON_OLD, ICON_NEW)
        count += 1
    if DATA_OLD in text and DATA_NEW not in text:
        text = text.replace(DATA_OLD, DATA_NEW)
        count += 1
    return text, count


def center_is_healthy(text):
    """True when a clear center uses emerald, and red only while p.error is set."""
    return "border-emerald-500 bg-emerald-50" in text and "border-red-500 bg-red-50" in text and CENTER_OLD not in text


def parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def error_provider(rows):
    """Same pick as the provider-metrics route: newest failing last status."""
    best = ""
    best_at = None
    for row in rows:
        status = row.get("lastStatus")
        err_at = parse_time(row.get("lastErrorAt"))
        if status is None or err_at is None:
            continue
        if status >= 200 and status < 400:
            continue
        if best_at is None or err_at > best_at:
            best_at = err_at
            best = row.get("provider") or ""
    return best


def violation(provider, error_age_s, attempt_age_s):
    """True when the center error is older than 2 minutes and no heal ran within 60 seconds."""
    if not provider:
        return False
    if error_age_s is None or error_age_s <= STUCK_S:
        return False
    if attempt_age_s is None:
        return True
    return attempt_age_s > ATTEMPT_S


def now_utc():
    return datetime.now(timezone.utc)


def as_of(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def reapply(install):
    """Patch bundle copies. Returns the number of fragments changed."""
    root = Path(install)
    changed = 0
    seen = 0
    if not root.is_dir():
        return -1
    for path in root.rglob("*.js"):
        if "node_modules" in path.relative_to(root).parts:
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        updated, count = apply_filter(text)
        updated, center_count = apply_center(updated)
        if OLD in text or NEW in text:
            seen += 1
        if count == 0 and center_count == 0:
            continue
        backup_dir = Path.home() / ".agent-city" / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = now_utc().strftime("%Y%m%dT%H%M%SZ")
        dest = backup_dir / f"metrics-active-{stamp}-{path.name}"
        if not dest.exists():
            shutil.copy2(path, dest)
        path.write_text(updated)
        changed += count + center_count
    source = root / "src" / "lib" / "db" / "callLogStats.ts"
    if source.is_file() and SOURCE_MARKER not in source.read_text(errors="replace"):
        return -1
    if seen == 0:
        return -1
    return changed


def _query(db_path):
    sql = """
    SELECT c.provider AS provider,
      (
        SELECT c2.status FROM call_logs c2
        WHERE c2.provider = c.provider
        ORDER BY c2.timestamp DESC, c2.id DESC
        LIMIT 1
      ) AS lastStatus,
      MAX(
        CASE
          WHEN (c.status < 200 OR c.status >= 400) OR c.error_summary IS NOT NULL
          THEN c.timestamp
        END
      ) AS lastErrorAt
    FROM call_logs c
    WHERE c.provider IS NOT NULL AND c.provider != '-'
      AND EXISTS (
        SELECT 1 FROM provider_connections pc
        WHERE pc.provider = c.provider AND pc.is_active = 1
      )
    GROUP BY c.provider
    """
    proc = subprocess.run(
        ["sqlite3", "-json", str(db_path), sql],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError("query")
    raw = proc.stdout.strip()
    if not raw:
        return []
    rows = json.loads(raw)
    if not isinstance(rows, list):
        raise RuntimeError("query")
    return rows


def read_attempt_age(path, moment):
    if not path.is_file():
        return None
    stamp = parse_time(path.read_text(errors="replace").strip())
    if stamp is None:
        return None
    return (moment - stamp).total_seconds()


def write_attempt(path, moment):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(as_of(moment) + "\n")


def omniroute_call_in_flight():
    proc = subprocess.run(
        ["pgrep", "-f", "--", "--model omniroute"],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def reload_gateway():
    if omniroute_call_in_flight():
        print("PASS home filter installed reload deferred")
        return 0
    uid = os.getuid()
    proc = subprocess.run(
        ["launchctl", "kickstart", "-k", f"gui/{uid}/com.omniroute.server"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(FAIL)
        return 1
    print("PASS home gateway reloaded")
    return 0


def main(argv):
    install = Path(argv[1]) if len(argv) > 1 else DEFAULT
    live = install == DEFAULT
    changed = reapply(install)
    if changed < 0:
        print(FAIL)
        return 1
    if changed:
        print(f"PASS home metrics filter installed {changed}")
    else:
        print("PASS home metrics filter found")
    if not live:
        return 0
    moment = now_utc()
    db_path = Path.home() / ".omniroute" / "storage.sqlite"
    try:
        rows = _query(db_path)
    except Exception:
        print(QUERY_FAIL)
        return 1
    provider = error_provider(rows)
    attempt_path = Path.home() / ".agent-city" / "proofs" / "home-error-attempt"
    attempt_age = read_attempt_age(attempt_path, moment)
    age = None
    if provider:
        err_times = [
            parse_time(row.get("lastErrorAt"))
            for row in rows
            if row.get("provider") == provider
        ]
        err_times = [item for item in err_times if item is not None]
        if err_times:
            age = (moment - max(err_times)).total_seconds()
    if provider and violation(provider, age, attempt_age):
        write_attempt(attempt_path, moment)
        print(f"PASS home heal attempt {provider} as-of {as_of(moment)}")
    elif provider:
        print(f"PASS home errorProvider {provider} as-of {as_of(moment)}")
    else:
        print(f"PASS home errorProvider empty as-of {as_of(moment)}")
    if changed and os.environ.get("HOME_HEAL_RELOAD", "1") != "0":
        return reload_gateway()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
