import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.p0_settings_check import evaluate


def good():
    return {
        "flags": {
            "PRICING_SYNC_ENABLED": True,
            "FLUSH_EMPTY_RETRY_ENABLED": True,
            "STREAM_RECOVERY_ENABLED": True,
            "STREAM_EARLY_EOF_SIBLING_FAILOVER_ENABLED": True,
            "STREAM_RECOVERY_TOOLCALL_ORDER_FIX": True,
            "OMNIROUTE_ROTATE_ON_400": True,
            "PROVIDER_COOLDOWN_ENABLED": True,
            "REQUIRE_API_KEY": True,
        },
        "bind_loopback": True,
        "lockout_enabled": True,
        "denylist": ["grok-cli/*", "xai-oauth/*", "*command-a-reasoning*"],
        "provider_cooldown": True,
        "combo_cooldown": True,
        "stream_recovery": True,
        "continue_midstream": False,
    }


class TestP0SettingsCheck(unittest.TestCase):
    def test_good_snapshot(self):
        self.assertEqual(evaluate(good()), [])

    def test_flag_failure(self):
        snapshot = good()
        snapshot["flags"]["PRICING_SYNC_ENABLED"] = False
        self.assertEqual(evaluate(snapshot), ["flag:PRICING_SYNC_ENABLED"])

    def test_bind_failure(self):
        snapshot = good()
        snapshot["bind_loopback"] = False
        self.assertEqual(evaluate(snapshot), ["bind"])

    def test_lockout_failure(self):
        snapshot = good()
        snapshot["lockout_enabled"] = False
        self.assertEqual(evaluate(snapshot), ["lockout"])

    def test_denylist_failure(self):
        snapshot = good()
        snapshot["denylist"] = ["grok-cli/*", "xai-oauth/*"]
        self.assertEqual(evaluate(snapshot), ["denylist"])

    def test_provider_cooldown_failure(self):
        snapshot = good()
        snapshot["provider_cooldown"] = False
        self.assertEqual(evaluate(snapshot), ["provider-cooldown"])

    def test_combo_cooldown_failure(self):
        snapshot = good()
        snapshot["combo_cooldown"] = False
        self.assertEqual(evaluate(snapshot), ["combo-cooldown"])

    def test_stream_recovery_failure(self):
        snapshot = good()
        snapshot["stream_recovery"] = False
        self.assertEqual(evaluate(snapshot), ["stream-recovery"])

    def test_midstream_failure(self):
        snapshot = good()
        snapshot["continue_midstream"] = True
        self.assertEqual(evaluate(snapshot), ["midstream"])

    def test_missing_midstream_fails_closed(self):
        snapshot = good()
        snapshot["continue_midstream"] = None
        self.assertEqual(evaluate(snapshot), ["midstream"])


if __name__ == "__main__":
    unittest.main()
