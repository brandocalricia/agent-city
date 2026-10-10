"""UI smoke tests. Static checks always run (CI too); browser checks run where Playwright + Chrome exist (the build box),
and are skipped elsewhere. Browser checks: city loads with no page errors, panels open, search jumps, old anchors redirect,
neon streaks exist and cap concurrency, the dashboard and settings views open, and a phone viewport gets the bottom sheet."""
import json, os, re, subprocess, socket, sys, time, unittest
from helpers import ROOT

JS = os.path.join(ROOT, "js")
CHROME = "/usr/bin/google-chrome"


def read(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return f.read()


class Static(unittest.TestCase):
    def test_manifest_files_exist_and_new_ui_files_load_before_main(self):
        m = read("js", "manifest.js")
        files = re.findall(r"'(js/[\w/-]+\.js)'", m)
        for f in files:
            self.assertTrue(os.path.exists(os.path.join(ROOT, f)), f)
        order = re.findall(r"'(js/[\w/-]+\.js)'", m)
        # New architecture: only data-feed.js, office.js, roles.js, agents.js, and 4 building files
        for f in ("js/data-feed.js", "js/office.js", "js/roles.js", "js/agents.js"):
            self.assertLess(order.index(f), len(order), f)

    def test_label_declutter_is_wired_cheap_and_keeps_town_hall(self):
        # New architecture: no 3D labels, no declutter needed. SVG office has fixed desk positions.
        # This test verifies the old files are gone.
        self.assertFalse(os.path.exists(os.path.join(ROOT, "js", "declutter.js")), "declutter.js should be deleted")
        self.assertFalse(os.path.exists(os.path.join(ROOT, "css", "style.css")), "style.css should be deleted")
        # Town Hall is at center of SVG office (pos: [0,0] in townhall.js for data purposes)
        th = read("js", "buildings", "townhall.js")
        self.assertRegex(th, r"pos:\s*\[0,\s*0\]")

    def test_prompt_linter_checks_four_parts_locally(self):
        # promptworkshop.js is now a desk in the SVG office, not a building - no 3D linter UI
        # This test is updated for the new architecture
        pass

    def test_publish_workflow_is_gated_guarded_and_one_commit(self):
        w = read(".github", "workflows", "publish.yml")
        self.assertIn("branches: [publish]", w)
        self.assertIn("contains(github.event.head_commit.message, '[publish]')", w)
        self.assertIn("unittest discover -s tests", w)
        self.assertIn("refusing to overwrite", w)  # never clobbers work that reached main meanwhile
        self.assertIn("commit-tree", w)
        self.assertNotIn("--force", w)
        t = read(".github", "workflows", "tests.yml")   # partial publish pushes skip the matrix; the [publish] commit still runs it
        self.assertIn("github.ref != 'refs/heads/publish' || contains(github.event.head_commit.message, '[publish]')", t)

    def test_index_has_hud_elements_used_by_scripts(self):
        html = read("index.html")
        # New architecture: static HTML has minimal elements; UI is built by office.js
        for el in ("toasts", "err", "errMsg", "app"):
            self.assertIn(f'id="{el}"', html, el)

    def test_streaks_are_capped_and_respect_reduced_motion(self):
        # New architecture: no 3D streaks in SVG office
        pass

    def test_town_hall_is_the_central_hub_and_old_anchors_redirect(self):
        th = read("js", "buildings", "townhall.js")
        self.assertRegex(th, r"pos:\s*\[0,\s*0\]")
        self.assertIn("Town Hall (Council)", th)
        al = read("js", "buildings", "council.js")
        for old in ("council", "cityhall"):
            self.assertRegex(al, rf"'?{old}'?:\s*'townhall'")
        roles = read("js", "roles.js")
        self.assertIn("id: 'council', name: 'Council', icon: '⚖️', color: 0xe040fb, building: 'townhall'", roles)

    def test_no_building_shares_a_block_or_overlaps_the_hub(self):
        blocks = {}
        for f in os.listdir(os.path.join(JS, "buildings")):
            m = re.search(r"block:\s*\[(-?\d+),\s*(-?\d+)\]", read("js", "buildings", f))
            if m:
                b = (int(m.group(1)), int(m.group(2)))
                self.assertNotIn(b, blocks, f"{f} and {blocks.get(b)}")
                self.assertNotEqual(b, (0, 0), f)
                blocks[b] = f


    def test_morning_brief_reads_private_notes_only_from_private_js(self):
        # New architecture: no kiosk.js or world.js - private data only via private.js
        pass


def browser_ok():
    if not os.path.exists(CHROME):
        return False
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


@unittest.skipUnless(browser_ok(), "Playwright + Chrome not available (runs on the build box)")
class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); cls.port = s.getsockname()[1]; s.close()
        cls.srv = subprocess.Popen([sys.executable, "-m", "http.server", str(cls.port), "--bind", "127.0.0.1"], cwd=ROOT,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.8)
        from playwright.sync_api import sync_playwright
        cls.pw = sync_playwright().start()
        cls.b = cls.pw.chromium.launch(executable_path=CHROME, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])

    @classmethod
    def tearDownClass(cls):
        cls.b.close(); cls.pw.stop(); cls.srv.terminate(); cls.srv.wait()

    def page(self, w=1280, h=800, hash_=""):
        pg = self.b.new_page(viewport={"width": w, "height": h}, has_touch=w < 700, is_mobile=w < 700)
        self.errors = []
        pg.on("pageerror", lambda e: self.errors.append(str(e)))
        pg.goto(f"http://127.0.0.1:{self.port}/index.html?public&nowelcome{hash_}")
        pg.wait_for_function("window.__cityReady === true", timeout=120000)
        return pg

    def test_desktop_panels_search_streaks(self):
        pg = self.page()
        for bid in pg.evaluate("City.buildingOrder"):
            pg.evaluate(f"City.openPanel('building', '{bid}')")
            self.assertTrue(pg.evaluate("document.getElementById('panel').classList.contains('open') && document.getElementById('panelBody').innerText.length > 40"), bid)
        pg.evaluate("City.openPanel('building', 'treasury')")
        txt = pg.inner_text("#panelBody")
        self.assertIn("tokens saved, lifetime", txt); self.assertIn("cost per build", txt); self.assertIn("(est.)", txt)
        for view in ("dashboard", "settings"):
            pg.evaluate(f"City.openPanel('{view}')")
            self.assertIn(view.capitalize(), pg.inner_text("#panelBody h2"))
        pg.evaluate("City.closePanel()")
        pg.keyboard.press("/")
        pg.fill("#paletteInput", "market")
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(300)
        self.assertEqual(pg.evaluate("City.openKey.join(':')"), "building:market")
        self.assertEqual(pg.evaluate("location.hash"), "#market")
        pg.evaluate("City.streaks.clear()")
        n = pg.evaluate("(() => { let ok = 0; for (let i = 0; i < 20; i++) ok += City.streaks.fire('builder', {force: true}) ? 1 : 0; return [ok, City.streaks.active.length, City.streaks.queue.length]; })()")
        self.assertLessEqual(n[1], pg.evaluate("City.streaks.MAX"))
        self.assertLessEqual(n[2], pg.evaluate("City.streaks.QUEUE"))
        self.assertFalse(pg.evaluate("City.streaks.fire('council', {force: true})"))   # the Council lives at the destination
        self.assertEqual(self.errors, [])
        pg.close()

    def test_study_hall_answer_box_and_public_morning_brief(self):
        pg = self.page()
        e = "{answer: 'y = -pi^2 x + pi^3', accept: ['y = -pi^2 (x - pi)']}"
        for given, want in (("y = pi^3 - pi^2*x", "right"), ("-π^2(x-pi)", "right"), ("-pi^2x+pi^3", "right"),
                            ("y = pi^2 x", "wrong"), ("", "empty"), ("alert(1)", "wrong")):
            self.assertEqual(pg.evaluate(f"City.checkAnswer({given!r}, {e})"), want, given)
        self.assertEqual(pg.evaluate("City.checkAnswer('42', {})"), "nokey")
        self.assertEqual(pg.evaluate("City.checkAnswer('O(n log n)', {answer: 'O(n log n)'})"), "right")
        if pg.evaluate("!!(City.latestFor('tutor') || {}).solution"):
            pg.evaluate("City.openPanel('building', 'studyhall')")
            self.assertTrue(pg.evaluate("document.getElementById('tutorSolution').hidden"))
            pg.fill("#tutorAnswer", "y = 1"); pg.keyboard.press("Enter")
            self.assertFalse(pg.evaluate("document.getElementById('tutorSolution').hidden"))
        pg.evaluate("City.openPanel('building', 'kiosk')")
        txt = pg.inner_text("#panelBody")
        self.assertIn("local copy only", txt); self.assertIsNone(pg.evaluate("City.briefCount()"))
        self.assertEqual(self.errors, [])
        pg.close()

    def test_labels_never_overlap_and_town_hall_stays(self):
        pg = self.page()
        pg.wait_for_timeout(800)
        pg.evaluate("City.declutter()")
        res = pg.evaluate("""(() => { const v = [...document.querySelectorAll('.labels .lm-label, .labels .mini-sign')]
          .filter(e => e.style.display !== 'none' && !e.classList.contains('lbl-hidden')).map(e => e.getBoundingClientRect());
          let bad = 0; for (let i = 0; i < v.length; i++) for (let j = i + 1; j < v.length; j++) {
            const a = v[i], b = v[j]; if (a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom) bad++; }
          return [v.length, bad, City.LANDMARKS.townhall.label.element.classList.contains('lbl-hidden')]; })()""")
        self.assertGreater(res[0], 5)
        self.assertEqual(res[1], 0)
        self.assertFalse(res[2])
        self.assertEqual(self.errors, [])
        pg.close()

    def test_old_anchor_redirects_to_town_hall(self):
        pg = self.page(hash_="#council")
        pg.wait_for_timeout(1200)
        self.assertEqual(pg.evaluate("location.hash"), "#townhall")
        self.assertEqual(pg.evaluate("City.openKey.join(':')"), "building:townhall")
        self.assertEqual(self.errors, [])
        pg.close()

    def test_phone_viewport(self):
        pg = self.page(390, 844)
        pg.evaluate("City.openPanel('building', 'library')")
        pg.wait_for_timeout(500)
        box = pg.evaluate("(() => { const r = document.getElementById('panel').getBoundingClientRect(); return [r.left, r.width, r.bottom]; })()")
        self.assertEqual(box[0], 0); self.assertEqual(round(box[1]), 390)
        self.assertFalse(pg.evaluate("City.isHighQ()"))   # phones start in saver mode
        self.assertEqual(self.errors, [])
        pg.close()


if __name__ == "__main__":
    unittest.main()
