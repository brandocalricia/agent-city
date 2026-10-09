"""The Home center chunk that the manifest names must be emerald, and the service worker must not reuse a year-old copy."""

import json
import os
import urllib.request
from pathlib import Path

ORIGIN = os.environ.get("OMNIROUTE_HOME_ORIGIN", "http://127.0.0.1:20128")
DIST = Path(
    os.environ.get(
        "OMNIROUTE_DIST",
        "/opt/homebrew/lib/node_modules/omniroute/dist",
    )
)
OLD_CENTER = "border-2 border-primary bg-primary/8"
EMERALD = "border-emerald-500 bg-emerald-50"
RED = "border-red-500 bg-red-50"


def center_chunk_ok(text):
    """Empty error maps to emerald. The old primary rectangle is a failure."""
    if OLD_CENTER in text or "#e54d5e" in text:
        return False
    return EMERALD in text and RED in text and 'p.error?"border-red-500 bg-red-50"' in text


def sw_ok(text):
    """/_next/ fetches must bypass the HTTP cache."""
    if 'cache: "no-store"' not in text:
        return False
    return "/_next/" in text


def manifest_chunk_paths(dist):
    path = (
        Path(dist)
        / ".build/next/server/app/(dashboard)/home/page/react-loadable-manifest.json"
    )
    data = json.loads(path.read_text())
    found = []
    for entry in data.values():
        for name in entry.get("files") or []:
            if name.endswith(".js"):
                found.append("/_next/" + name)
    return found


def fetch(url):
    with urllib.request.urlopen(url, timeout=8) as response:
        return response.status, response.read().decode("utf-8", "replace")


def live_center():
    """Return the served topology chunk and the service worker."""
    paths = manifest_chunk_paths(DIST)
    chosen = None
    body = ""
    for path in paths:
        status, text = fetch(ORIGIN + path)
        if status != 200:
            continue
        if "border-emerald-500" in text or OLD_CENTER in text or 'children:"OmniRoute"' in text:
            chosen = path
            body = text
            break
    sw_status, sw_body = fetch(ORIGIN + "/sw.js")
    return chosen, body, sw_status, sw_body


def test_old_primary_rectangle_fails():
    assert center_chunk_ok('className:"' + OLD_CENTER + '"') is False


def test_red_hex_in_the_center_chunk_fails():
    assert center_chunk_ok(EMERALD + RED + " #e54d5e") is False


def test_emerald_mapping_passes():
    sample = EMERALD + " " + RED + ' p.error?"border-red-500 bg-red-50"'
    assert center_chunk_ok(sample) is True


def test_service_worker_without_no_store_fails():
    assert sw_ok('if (isNextAsset) { fetch(event.request) }') is False
    assert sw_ok('pathname.startsWith("/_next/"); fetch(event.request, { cache: "no-store" })') is True


def test_live_home_manifest_serves_an_emerald_center():
    path, body, sw_status, sw_body = live_center()
    assert path, "Home loadable manifest did not name a topology chunk"
    assert center_chunk_ok(body), path
    assert sw_status == 200
    assert sw_ok(sw_body)


if __name__ == "__main__":
    test_old_primary_rectangle_fails()
    test_red_hex_in_the_center_chunk_fails()
    test_emerald_mapping_passes()
    test_service_worker_without_no_store_fails()
    test_live_home_manifest_serves_an_emerald_center()
    print("PASS home center asset")
