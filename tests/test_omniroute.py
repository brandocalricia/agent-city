"""OmniRoute snapshot: loader puts it in CITY_DATA, the JSON has no secrets, scheduler prints a plan."""
import json, os, re, shutil, sys, unittest
from helpers import ROOT
from test_build_data import Sandbox
import build_data as bd
sys.path.insert(0, os.path.join(ROOT, "tools"))
import swarm_scheduler as ss

BAD = ("api_key", "email", "localhost", "token", "/Users/")


def city_data(path):
    txt = open(path, encoding="utf-8").read()
    return json.loads(txt.split("window.CITY_DATA = ", 1)[1].rstrip().rstrip(";"))


class Omniroute(unittest.TestCase):
    def test_loader_includes_omniroute_and_json_has_no_secrets(self):
        path = os.path.join(ROOT, "data", "omniroute.json")
        raw = open(path, encoding="utf-8").read()
        for bad in BAD:
            self.assertNotIn(bad, raw, bad)
        o = json.loads(raw)
        self.assertNotIn("budget.json", raw)
        self.assertEqual(bd.load_omniroute(), o)
        self.assertIn("providers", o)
        self.assertIn("compression", o)
        self.assertIn("last", o)
        self.assertEqual(o["quota"]["mode"], "full")
        self.assertEqual(o["last"]["in"], 208)
        self.assertEqual(o["last"]["out"], 80)
        self.assertEqual(o["lanes"]["local"], 1)
        self.assertEqual(o["lanes"]["remote_free"], 3)
        with Sandbox([]) as d:
            os.makedirs(os.path.join(d, "data"))
            shutil.copy(path, os.path.join(d, "data", "omniroute.json"))
            self.assertEqual(bd.main(), 0)
            data = city_data(os.path.join(d, "data.js"))
        self.assertEqual(data["omniroute"]["last"]["in"], 208)
        self.assertEqual(data["omniroute"]["version"], "3.8.51")
        dumped = json.dumps(data["omniroute"])
        for bad in BAD:
            self.assertNotIn(bad, dumped, bad)

    def test_missing_file_yields_empty_object(self):
        with Sandbox([]) as d:
            self.assertEqual(bd.load_omniroute(), {})
            self.assertEqual(bd.main(), 0)
            self.assertEqual(city_data(os.path.join(d, "data.js"))["omniroute"], {})

    def test_data_js_has_no_secrets(self):
        txt = open(os.path.join(ROOT, "data.js"), encoding="utf-8").read()
        for bad in ("api_key", "localhost", "/Users/"):
            self.assertNotIn(bad, txt, bad)
        self.assertIsNone(re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", txt))
        self.assertNotIn("budget.json", txt)

    def test_scheduler_prints_free_first_and_starts_nothing(self):
        src = open(os.path.join(ROOT, "tools", "swarm_scheduler.py"), encoding="utf-8").read()
        for bad in ("subprocess", "Popen", "os.system", "openai", "requests"):
            self.assertNotIn(bad, src, bad)
        p = ss.plan(bd.load_omniroute())
        self.assertEqual(p["started"], 0)
        self.assertEqual(p["grok_fallback_pct"], 0)
        self.assertEqual(p["mode"], "full")
        self.assertEqual(p["workers"], 3)
        self.assertEqual(p["assigned"][0]["kind"], "free")
        empty = ss.plan({"lanes": {}})
        self.assertEqual(empty["grok_fallback_pct"], 100)
        self.assertEqual(empty["mode"], "minimal")
        self.assertEqual(empty["workers"], 0)
        shifted = ss.plan({"lanes": {"remote_free": 1}})
        self.assertEqual(shifted["mode"], "shifted")
        self.assertEqual(shifted["workers"], 1)


if __name__ == "__main__":
    unittest.main()
