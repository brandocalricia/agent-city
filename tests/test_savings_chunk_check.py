import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.savings_chunk_check import decide, has_markers


class TestSavingsChunkCheck(unittest.TestCase):
    def test_marker_present_is_ok(self):
        self.assertEqual(decide("patched", True, True, False, True), "ok")
        self.assertEqual(decide("created", True, True, False, False), "ok")

    def test_reapply_only_onto_the_pre_patch_bytes(self):
        self.assertEqual(decide("patched", True, False, True, True), "reapply")

    def test_upgrade_replacement_is_not_overwritten(self):
        self.assertEqual(decide("patched", True, False, False, True), "fail")

    def test_missing_created_file_is_copied_back(self):
        self.assertEqual(decide("created", False, False, False, True), "reapply")

    def test_missing_good_copy_fails(self):
        self.assertEqual(decide("created", False, False, False, False), "fail")
        self.assertEqual(decide("patched", True, False, True, False), "fail")

    def test_markers(self):
        self.assertTrue(has_markers("Savings $ and as of", ("Savings $", "as of")))
        self.assertFalse(has_markers("Savings $", ("Savings $", "as of")))


if __name__ == "__main__":
    unittest.main()
