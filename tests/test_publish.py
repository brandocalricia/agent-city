"""Publishing: the publish Action regenerates data.js off the box without losing the box-only parts (skills, agents, routines)."""
import json, os, shutil, sys, unittest
from helpers import ROOT, TempDir
sys.path.insert(0, ROOT)
import build_data as bd


class OffBoxRegeneration(unittest.TestCase):
    def test_skills_agents_routines_carry_over_from_committed_data_js(self):
        with TempDir() as d:
            old = {"skills": [{"name": "council"}], "agents": [{"name": "Agent City"}], "routines": [{"name": "r"}], "activity": []}
            with open(os.path.join(d, "data.js"), "w", encoding="utf-8") as f:
                f.write("// AUTO-GENERATED\nwindow.CITY_DATA = " + json.dumps(old) + ";\n")
            saved = (bd.HERE, bd.ROOT)
            try:
                bd.HERE, bd.ROOT = d, os.path.join(d, "no-agent-data")
                self.assertEqual(bd.previous_box_state(), {k: old[k] for k in ("skills", "agents", "routines")})
                bd.ROOT = d                                  # on the box (agent-data exists): live data wins
                self.assertIsNone(bd.previous_box_state())
                bd.ROOT = os.path.join(d, "no-agent-data")
                os.remove(os.path.join(d, "data.js"))        # nothing committed yet: plain empty lists
                self.assertIsNone(bd.previous_box_state())
            finally:
                bd.HERE, bd.ROOT = saved

    def test_workflow_regenerates_before_testing_and_publishing(self):
        w = open(os.path.join(ROOT, ".github", "workflows", "publish.yml"), encoding="utf-8").read()
        self.assertLess(w.index("python3 build_data.py"), w.index("unittest discover"))
        self.assertLess(w.index("unittest discover"), w.index("commit-tree"))
        self.assertIn("git add data.js grok-build/suggestions.md grok-build/manifest.txt", w)


if __name__ == "__main__":
    unittest.main()
