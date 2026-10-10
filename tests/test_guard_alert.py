import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.guard_alert import should_post


class TestGuardAlert(unittest.TestCase):
    def test_pass_stays_quiet(self):
        self.assertFalse(should_post("", ""))
        self.assertFalse(should_post("", "p0-settings:flag:BIND"))

    def test_new_failure_posts_once(self):
        self.assertTrue(should_post("p0-settings:bind", ""))
        self.assertFalse(should_post("p0-settings:bind", "p0-settings:bind"))

    def test_changed_failure_posts_again(self):
        self.assertTrue(should_post("savings-chunk:costs-page", "p0-settings:bind"))


if __name__ == "__main__":
    unittest.main()
