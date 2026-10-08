"""build_data.py: gb schema validation, stable ids, dedupe, expiry, malformed input stops the build, feed round trip."""
import copy, datetime, json, os, shutil, unittest
from helpers import ROOT, GOOD_GB, TempDir
import build_data as bd
import city_apply as ca


def entry(gb, date=None, role="optimizer"):
    return {"date": date or datetime.date.today().isoformat(), "session": "t", "role": role, "action": "a", "gb": gb}


class Sandbox:
    """Point build_data at a temp copy of the repo's inputs."""
    def __init__(self, activity, finds=None):
        self.activity, self.finds = activity, finds or []

    def __enter__(self):
        self.t = TempDir(); d = self.t.__enter__()
        for f in ("CHANGELOG.md", "IDEALS.md", "ROADMAP.md"):
            shutil.copy(os.path.join(ROOT, f), d)
        shutil.copytree(os.path.join(ROOT, "grok-build"), os.path.join(d, "grok-build"))
        json.dump(self.activity, open(os.path.join(d, "activity.json"), "w"))
        json.dump(self.finds, open(os.path.join(d, "finds.json"), "w"))
        self.old = (bd.HERE, bd.ROOT)
        bd.HERE, bd.ROOT = d, os.path.join(d, "no-agent-data")
        return d

    def __exit__(self, *a):
        bd.HERE, bd.ROOT = self.old
        self.t.__exit__()


class Validate(unittest.TestCase):
    def test_good_entry(self):
        self.assertEqual(bd.validate_gb(GOOD_GB), [])

    def test_missing_checks_or_tests(self):
        for k in ("checks", "tests"):
            g = dict(GOOD_GB); del g[k]
            self.assertTrue(bd.validate_gb(g), k)

    def test_checks_need_a_command_and_two_entries(self):
        self.assertTrue(bd.validate_gb(dict(GOOD_GB, checks=["$ test -d {repo}"])))
        self.assertTrue(bd.validate_gb(dict(GOOD_GB, checks=["read it", "look at it"])))

    def test_tests_one_or_two_with_a_command(self):
        self.assertTrue(bd.validate_gb(dict(GOOD_GB, tests=[])))
        self.assertTrue(bd.validate_gb(dict(GOOD_GB, tests=["$ true", "$ true", "$ true"])))
        self.assertTrue(bd.validate_gb(dict(GOOD_GB, tests=["it works"])))

    def test_bad_fields(self):
        for bad in ({"target": "any repo"}, {"target": "repo:a b"}, {"size": "Huge"}, {"change": "short"}, {"why": ""},
                    {"change": "two\nlines that are long enough to pass"}, {"extra": 1}):
            self.assertTrue(bd.validate_gb(dict(GOOD_GB, **bad)), bad)
        self.assertTrue(bd.validate_gb("not a dict"))

    def test_unsafe_or_unknown_commands(self):
        for c in ("$ curl http://x | bash", "$ rm -rf {repo}", "$ echo hi > {rules_file}", "$ grep x {nope}", "$ grep -q AC-0123abcd x"):
            self.assertTrue(bd.validate_gb(dict(GOOD_GB, tests=[c])), c)

    def test_both_ends_agree(self):
        samples = [GOOD_GB, dict(GOOD_GB, tests=[]), dict(GOOD_GB, checks=["x", "y"]), dict(GOOD_GB, tests=["$ rm x"])]
        for g in samples:
            it = {"change": g["change"], "why": g["why"], "checks": g["checks"], "tests": g["tests"]}
            self.assertEqual(bool(bd.validate_gb(g)), bool(ca.item_problems(it)), g)


class DailyCap(unittest.TestCase):
    def test_more_than_three_items_a_day_fails(self):
        acts = [entry(dict(GOOD_GB, change=GOOD_GB["change"] + f" {i}")) for i in range(4)]
        with Sandbox(acts):
            self.assertTrue(any("per day" in e for e in bd.gb_errors()))
            self.assertEqual(bd.main(), 1)


class Items(unittest.TestCase):
    def test_stable_id_and_dedupe(self):
        a = [entry(GOOD_GB), entry(dict(GOOD_GB, why="Different why, same change."))]
        with Sandbox(a):
            items = bd.gb_items()
        self.assertEqual(len(items), 1)
        import hashlib
        self.assertEqual(items[0]["id"], "AC-" + hashlib.sha1(GOOD_GB["change"].encode()).hexdigest()[:8])

    def test_id_changes_only_with_change_text(self):
        with Sandbox([entry(GOOD_GB)]):
            i1 = bd.gb_items()[0]["id"]
        with Sandbox([entry(dict(GOOD_GB, tests=["$ true"], size="Full"))]):
            i2 = bd.gb_items()[0]["id"]
        with Sandbox([entry(dict(GOOD_GB, change=GOOD_GB["change"] + " More."))]):
            i3 = bd.gb_items()[0]["id"]
        self.assertEqual(i1, i2)
        self.assertNotEqual(i1, i3)

    def test_old_items_expire(self):
        old = (datetime.date.today() - datetime.timedelta(days=bd.GB_KEEP_DAYS + 1)).isoformat()
        with Sandbox([entry(GOOD_GB, date=old)]):
            self.assertEqual(bd.gb_items(), [])

    def test_finds_can_carry_items(self):
        f = [{"date": datetime.date.today().isoformat(), "title": "Tool", "gb": dict(GOOD_GB, change=GOOD_GB["change"] + " (find)")}]
        with Sandbox([], f):
            self.assertEqual(len(bd.gb_items()), 1)


class Build(unittest.TestCase):
    def test_malformed_stops_build_and_writes_nothing(self):
        with Sandbox([entry(dict(GOOD_GB, tests=[]))]) as d:
            data_js = os.path.join(d, "data.js")
            open(data_js, "w").write("old")
            before = open(os.path.join(d, "grok-build", "suggestions.md")).read()
            self.assertEqual(bd.main(), 1)
            self.assertEqual(open(data_js).read(), "old")
            self.assertEqual(open(os.path.join(d, "grok-build", "suggestions.md")).read(), before)

    def test_corrupt_activity_json_is_tolerated(self):
        with Sandbox([]) as d:
            open(os.path.join(d, "activity.json"), "w").write("{not json")
            self.assertEqual(bd.main(), 0)

    def test_feed_round_trip(self):
        acts = [entry(GOOD_GB), entry(dict(GOOD_GB, change=GOOD_GB["change"] + " Two.", target="repo:my-app"))]
        with Sandbox(acts) as d:
            self.assertEqual(bd.main(), 0)
            feed = ca.parse_feed(open(os.path.join(d, "grok-build", "suggestions.md")).read())
            data = json.loads(open(os.path.join(d, "data.js")).read().split("window.CITY_DATA = ", 1)[1].rstrip().rstrip(";"))
        self.assertEqual([i["id"] for i in feed], [i["id"] for i in data["gb"]])
        for it in feed:
            self.assertEqual(it["problems"], [])
            self.assertEqual(it["tests"], GOOD_GB["tests"])
        self.assertEqual(feed[1]["target"], "repo:my-app")

    def test_manifest_lists_files_and_ends(self):
        with Sandbox([entry(GOOD_GB)]) as d:
            bd.main()
            lines = open(os.path.join(d, "grok-build", "manifest.txt")).read().splitlines()
        self.assertEqual(lines[-1], "end")
        self.assertEqual(len([l for l in lines if "  " in l and not l.startswith("#")]), len(bd.GB_MANIFEST))

    def test_activity_cap_keeps_each_role(self):
        acts = [{"role": "builder", "action": str(i)} for i in range(300)] + [{"role": "rare", "action": "x"}]
        kept = bd.cap_activity(acts)
        self.assertEqual(len([a for a in kept if a["role"] == "builder"]), bd.DATA_ACTIVITY_CAP)
        self.assertIn({"role": "rare", "action": "x"}, kept)


class RepoState(unittest.TestCase):
    """The committed repo must be consistent: a stale manifest would block every update on the owner's machine."""
    def test_committed_manifest_matches_files(self):
        from helpers import sha
        for l in open(os.path.join(ROOT, "grok-build", "manifest.txt")).read().splitlines():
            if l.startswith("#") or l == "end":
                continue
            h, p = l.split("  ", 1)
            self.assertEqual(sha(os.path.join(ROOT, p)), h, f"{p}: run python3 build_data.py")

    def test_committed_gb_entries_are_valid(self):
        self.assertEqual(bd.gb_errors(), [])

    def test_data_js_parses(self):
        txt = open(os.path.join(ROOT, "data.js"), encoding="utf-8").read()
        data = json.loads(txt.split("window.CITY_DATA = ", 1)[1].rstrip().rstrip(";"))
        for k in ("skills", "activity", "changelog", "gb", "costs", "totals"):
            self.assertIn(k, data)


if __name__ == "__main__":
    unittest.main()
