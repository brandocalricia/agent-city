#!/usr/bin/env python3
"""Check the standing OmniRoute P0 settings. Prints one line and writes a proof."""

import json
import os
import plistlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FLAGS = (
    "PRICING_SYNC_ENABLED",
    "FLUSH_EMPTY_RETRY_ENABLED",
    "STREAM_RECOVERY_ENABLED",
    "STREAM_EARLY_EOF_SIBLING_FAILOVER_ENABLED",
    "STREAM_RECOVERY_TOOLCALL_ORDER_FIX",
    "OMNIROUTE_ROTATE_ON_400",
    "PROVIDER_COOLDOWN_ENABLED",
    "REQUIRE_API_KEY",
)
SQLITE_FLAGS = FLAGS[:5]
ENV_FLAGS = FLAGS
DENYLIST = ("grok-cli/*", "xai-oauth/*", "*command-a-reasoning*")
DB = Path.home() / ".omniroute" / "storage.sqlite"
PLIST = Path.home() / "Library" / "LaunchAgents" / "com.omniroute.server.plist"
PROOF = Path.home() / ".agent-city" / "proofs" / "p0-settings.json"


def truthy(value):
    return str(value).strip().lower() in {"true", "1", "yes"}


def evaluate(snapshot):
    failures = []
    flags = snapshot.get("flags") or {}
    for name in FLAGS:
        if flags.get(name) is not True:
            failures.append(f"flag:{name}")
    if snapshot.get("bind_loopback") is not True:
        failures.append("bind")
    if snapshot.get("lockout_enabled") is not True:
        failures.append("lockout")
    denylist = snapshot.get("denylist") or []
    if any(pattern not in denylist for pattern in DENYLIST):
        failures.append("denylist")
    if snapshot.get("provider_cooldown") is not True:
        failures.append("provider-cooldown")
    if snapshot.get("combo_cooldown") is not True:
        failures.append("combo-cooldown")
    if snapshot.get("stream_recovery") is not True:
        failures.append("stream-recovery")
    if snapshot.get("continue_midstream") is not False:
        failures.append("midstream")
    return failures


def sqlite_rows(sql):
    if not DB.is_file():
        return []
    proc = subprocess.run(
        ["sqlite3", "-json", str(DB), sql],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return []
    data = json.loads(proc.stdout)
    return data if isinstance(data, list) else []


def blank_snapshot():
    return {
        "flags": {name: False for name in FLAGS},
        "bind_loopback": False,
        "lockout_enabled": False,
        "denylist": [],
        "provider_cooldown": False,
        "combo_cooldown": False,
        "stream_recovery": False,
        "continue_midstream": True,
    }


def collect():
    snapshot = blank_snapshot()
    sql_flags = {}
    for row in sqlite_rows(
        "SELECT key, value FROM key_value WHERE namespace = 'feature_flags'"
    ):
        key = row.get("key")
        if key in SQLITE_FLAGS:
            sql_flags[key] = truthy(row.get("value"))
    env = {}
    if PLIST.is_file():
        with PLIST.open("rb") as handle:
            loaded = plistlib.load(handle)
        raw = loaded.get("EnvironmentVariables") or {}
        if isinstance(raw, dict):
            env = raw
    for name in ENV_FLAGS:
        from_plist = truthy(env.get(name))
        if name in SQLITE_FLAGS:
            snapshot["flags"][name] = bool(sql_flags.get(name) and from_plist)
        else:
            snapshot["flags"][name] = from_plist
    host = str(env.get("OMNIROUTE_SERVER_HOST") or "")
    snapshot["bind_loopback"] = host == "127.0.0.1"
    settings = {}
    for row in sqlite_rows(
        "SELECT key, value FROM key_value WHERE namespace = 'settings' "
        "AND key IN ('modelLockout','modelVisibilityDenylist','resilienceSettings')"
    ):
        key = row.get("key")
        if key == "password" or not isinstance(key, str):
            continue
        try:
            settings[key] = json.loads(row.get("value") or "null")
        except json.JSONDecodeError:
            settings[key] = None
    lockout = settings.get("modelLockout")
    snapshot["lockout_enabled"] = (
        isinstance(lockout, dict) and lockout.get("enabled") is True
    )
    denylist = settings.get("modelVisibilityDenylist")
    snapshot["denylist"] = denylist if isinstance(denylist, list) else []
    resilience = settings.get("resilienceSettings")
    if not isinstance(resilience, dict):
        resilience = {}
    provider = resilience.get("providerCooldown")
    combo = resilience.get("comboCooldownWait")
    stream = resilience.get("streamRecovery")
    snapshot["provider_cooldown"] = (
        isinstance(provider, dict) and provider.get("enabled") is True
    )
    snapshot["combo_cooldown"] = isinstance(combo, dict) and combo.get("enabled") is True
    snapshot["stream_recovery"] = (
        isinstance(stream, dict) and stream.get("enabled") is True
    )
    if isinstance(stream, dict) and "continueMidStream" in stream:
        snapshot["continue_midstream"] = stream.get("continueMidStream") is True
    else:
        snapshot["continue_midstream"] = True
    return snapshot


def write_proof(proof):
    PROOF.parent.mkdir(parents=True, exist_ok=True)
    handle = os.open(str(PROOF), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(handle, (json.dumps(proof, indent=2) + "\n").encode())
    finally:
        os.close(handle)


def main():
    error_class = None
    try:
        failures = evaluate(collect())
    except Exception as exc:
        failures = ["check-error"]
        error_class = type(exc).__name__
    proof = {
        "ok": not failures,
        "failed": failures,
        "checkedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if error_class:
        proof["errorClass"] = error_class
    try:
        write_proof(proof)
    except Exception as exc:
        proof["errorClass"] = type(exc).__name__
        failures = failures or ["check-error"]
    if failures:
        print("p0 fail: " + ",".join(failures))
        return 1
    print("p0 ok")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print("p0 fail: check-error")
        sys.exit(1)
