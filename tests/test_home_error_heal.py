"""Home center stays clear of inactive errors, and a stuck error must be healed."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import home_error_heal  # noqa: E402

SCRIPT = ROOT / "tools" / "home_error_heal.py"
OLD = home_error_heal.OLD


def test_inactive_401_is_not_the_center_error():
    rows = [
        {
            "provider": "ovhcloud",
            "lastStatus": 401,
            "lastErrorAt": "2026-10-09T21:20:08.021Z",
        },
        {
            "provider": "kilo-gateway",
            "lastStatus": 401,
            "lastErrorAt": "2026-10-09T21:20:08.020Z",
        },
    ]
    active = [
        {
            "provider": "cloudflare-ai",
            "lastStatus": 200,
            "lastErrorAt": "2026-10-09T20:27:18.120Z",
        }
    ]
    assert home_error_heal.error_provider(active) == ""
    assert home_error_heal.error_provider(rows + active) == "ovhcloud"


def test_stuck_error_without_attempt_is_a_violation():
    assert home_error_heal.violation("ovhcloud", 121, None) is True


def test_attempt_inside_sixty_seconds_is_not_a_violation():
    assert home_error_heal.violation("ovhcloud", 180, 30) is False


def test_error_under_two_minutes_is_not_a_violation():
    assert home_error_heal.violation("groq", 90, None) is False


def test_clear_center_is_not_a_violation():
    assert home_error_heal.violation("", 999, None) is False


def test_stale_attempt_is_a_violation():
    assert home_error_heal.violation("ovhcloud", 180, 61) is True


def test_apply_filter_is_idempotent():
    import tempfile

    tmp_path = Path(tempfile.mkdtemp())
    chunk = tmp_path / "dist" / "chunk.js"
    chunk.parent.mkdir()
    chunk.write_text("prefix " + OLD + " suffix")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path)],
        capture_output=True,
        text=True,
        env={"HOME_HEAL_RELOAD": "0", "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 0, proc.stderr
    assert "PASS home metrics filter installed 1" in proc.stdout
    text = chunk.read_text()
    assert "pc.is_active = 1" in text
    assert OLD not in text
    again = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert again.returncode == 0, again.stderr
    assert "PASS home metrics filter found" in again.stdout
    assert chunk.read_text() == text


if __name__ == "__main__":
    test_inactive_401_is_not_the_center_error()
    test_stuck_error_without_attempt_is_a_violation()
    test_attempt_inside_sixty_seconds_is_not_a_violation()
    test_error_under_two_minutes_is_not_a_violation()
    test_clear_center_is_not_a_violation()
    test_stale_attempt_is_a_violation()
    test_apply_filter_is_idempotent()
    print("PASS home error heal tests")
