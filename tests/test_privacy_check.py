"""tools/privacy_check.py: skips local-only files, flags emails/amounts in publishable paths."""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import privacy_check as pc

def _email(user, domain):
    return user + "@" + domain

class PrivacyCheck(unittest.TestCase):
    def test_skips_local_only_names(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "requests.json"), "w") as f:
                f.write('{"email":"' + _email("secret", "family.com") + '"}')
            with open(os.path.join(d, "budget.json"), "w") as f:
                f.write("owed " + "$" + "1,234.00")
            with open(os.path.join(d, "ok.md"), "w") as f:
                f.write("no secrets here")
            old = pc.HERE
            try:
                pc.HERE = d
                self.assertEqual(pc.main(), 0)
            finally:
                pc.HERE = old

    def test_flags_email_in_public_file(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "README.md"), "w") as f:
                f.write("contact " + _email("me", "personal-domain.xyz") + " please")
            old = pc.HERE
            try:
                pc.HERE = d
                self.assertEqual(pc.main(), 1)
            finally:
                pc.HERE = old

    def test_allows_github_noreply(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "wf.yml"), "w") as f:
                f.write('email: "41898282+github-actions[bot]@users.noreply.github.com"')
            old = pc.HERE
            try:
                pc.HERE = d
                self.assertEqual(pc.main(), 0)
            finally:
                pc.HERE = old
