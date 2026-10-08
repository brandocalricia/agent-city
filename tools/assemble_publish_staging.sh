#!/usr/bin/env bash
set -euo pipefail
if [ ! -d .publish-staging ]; then
  echo "No .publish-staging; nothing to assemble."
  exit 0
fi

python3 - <<'PY'
import base64, re
from pathlib import Path
stg = Path(".publish-staging")
for a1 in stg.glob("*.patch.b64.a1"):
    key = a1.name[:-len(".patch.b64.a1")]
    chunks = []
    for label in ("a", "b"):
        for i in range(1, 4):
            p = stg / f"{key}.patch.b64.{label}{i}"
            if not p.exists():
                raise SystemExit(f"missing {p}")
            chunks.append(p.read_text())
    data = base64.b64decode("".join(chunks).strip())
    out = stg / f"{key}.patch"
    out.write_bytes(data)
    print(f"decoded {out} ({len(data)} bytes from a1-3+b1-3)")
for a in stg.glob("*.patch.b64.a"):
    if a.name.endswith(tuple(f".a{i}" for i in range(1,10))):
        continue
    key = a.name[:-len(".patch.b64.a")]
    if (stg / f"{key}.patch").exists():
        continue
    b = stg / f"{key}.patch.b64.b"
    if not b.exists():
        raise SystemExit(f"missing {b}")
    data = base64.b64decode((a.read_text() + b.read_text()).strip())
    out = stg / f"{key}.patch"
    out.write_bytes(data)
    print(f"decoded {out} ({len(data)} bytes from a+b halves)")
for p in list(stg.glob("*.patch.b64")):
    if any(p.name.endswith(s) for s in [".a", ".b"] + [f".a{i}" for i in range(1,10)] + [f".b{i}" for i in range(1,10)]):
        continue
    if ".part" in p.name:
        continue
    if not p.name.endswith(".patch.b64"):
        continue
    key = p.name[:-len(".patch.b64")]
    if (stg / f"{key}.patch").exists():
        continue
    data = base64.b64decode(p.read_text().strip())
    out = stg / f"{key}.patch"
    out.write_bytes(data)
    print(f"decoded {out} ({len(data)} bytes from single b64)")
parts = {}
for p in stg.glob("*.patch.b64.part*"):
    m = re.match(r"(.+)\.patch\.b64\.part(\d+)$", p.name)
    if not m:
        continue
    key, idx = m.group(1), int(m.group(2))
    parts.setdefault(key, []).append((idx, p))
for key, items in parts.items():
    if (stg / f"{key}.patch").exists():
        continue
    items.sort()
    data = base64.b64decode("".join(p.read_text().strip() for _, p in items))
    out = stg / f"{key}.patch"
    out.write_bytes(data)
    print(f"decoded {out} ({len(data)} bytes from {len(items)} parts)")
PY

ROOT="https://raw.githubusercontent.com/brandocalricia/agent-city/main"
if [ -f .publish-staging/tests.patch ]; then
  curl -fsSL "$ROOT/tests/test_comms.py" -o tests/test_comms.py
  patch -p1 < .publish-staging/tests.patch
  echo "patched tests/test_comms.py"
fi
if [ -f .publish-staging/comms.patch ]; then
  curl -fsSL "$ROOT/grok-build/comms/comms.py" -o grok-build/comms/comms.py
  patch -p1 < .publish-staging/comms.patch
  echo "patched grok-build/comms/comms.py"
fi
if [ -f .publish-staging/data.patch ]; then
  curl -fsSL "$ROOT/data.js" -o data.js
  patch -p1 < .publish-staging/data.patch
  echo "patched data.js"
fi
# Whole-file b64 octets win over patches: NAME.full.b64.a1..a4+b1..b4 (NAME uses __ for /)
python3 - <<'PY2'
import base64
from pathlib import Path
stg = Path(".publish-staging")
for a1 in stg.glob("*.full.b64.a1"):
    key = a1.name[:-len(".full.b64.a1")]
    chunks = []
    for label in ("a", "b"):
        for i in range(1, 5):
            p = stg / ("%s.full.b64.%s%d" % (key, label, i))
            if not p.exists():
                raise SystemExit("missing %s" % p)
            chunks.append(p.read_text())
    data = base64.b64decode("".join(chunks).strip())
    rel = key.replace("__", "/")
    Path(rel).parent.mkdir(parents=True, exist_ok=True)
    Path(rel).write_bytes(data)
    print("wrote %s (%d bytes from full.b64 a1-4+b1-4)" % (rel, len(data)))
PY2



# Whole-file numbered b64 parts: NAME.full.b64.p1..pN
python3 - <<'PY3'
import base64, re
from pathlib import Path
stg = Path(".publish-staging")
groups = {}
for p in stg.glob("*.full.b64.p*"):
    m = re.match(r"(.+)\.full\.b64\.p(\d+)$", p.name)
    if not m:
        continue
    groups.setdefault(m.group(1), []).append((int(m.group(2)), p))
for key, items in groups.items():
    items.sort()
    data = base64.b64decode("".join(p.read_text().strip() for _, p in items))
    rel = key.replace("__", "/")
    Path(rel).parent.mkdir(parents=True, exist_ok=True)
    Path(rel).write_bytes(data)
    print("wrote %s (%d bytes from full.b64 p1..%d)" % (rel, len(data), len(items)))
PY3

rm -rf .publish-staging
echo "Staging removed."
