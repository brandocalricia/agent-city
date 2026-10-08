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
        files = re.findall(r"'(js/[\w/]+\.js)'", m) + [f"js/buildings/{b}.js" for b in re.findall(r"'(\w+)'", m.split("...[")[1].split("]")[0])]
        for f in files:
            self.assertTrue(os.path.exists(os.path.join(ROOT, f)), f)
        order = re.findall(r"'(js/\w+\.js)'", m)
        for f in ("js/visuals.js", "js/hud.js", "js/streaks.js"):
            self.assertLess(order.index(f), order.index("js/main.js"), f)

    def test_prompt_linter_checks_four_parts_locally(self):
        s = read("js", "buildings", "promptworkshop.js")
        self.assertIn("City.lintPrompt", s)
        self.assertIn('id="lintInput"', s)
        for part in ("'goal'", "'context'", "'done'", "'format'"):
            self.assertIn(part, s, part)
        self.assertNotRegex(s, r"fetch\(|XMLHttpRequest|sendBeacon")  # checked on the device only

    def test_publish_workflow_is_gated_guarded_and_one_commit(self):
        w = read(".github", "workflows", "publish.yml")
        self.assertIn("branches: [publish]", w)
        self.assertIn("contains(github.event.head_commit.message, '[publish]')", w)
        self.assertIn("unittest discover -s tests", w)
        self.assertIn("refusing to overwrite", w)  # never clobbers work that reached main meanwhile
        self.assertIn("commit-tree", w)
        self.assertNotIn("--force", w)

    def test_index_has_hud_elements_used_by_scripts(self):
        html = read("index.html")
        for el in ("topbar", "btnSearch", "btnDash", "btnOverview", "btnWalk", "btnTime", "btnSettings", "btnKeys", "chips", "palette",
                   "paletteInput", "paletteList", "shortcuts", "onboard", "onboardOk", "onboardTour", "toasts", "minimap", "panel",
                   "panelBody", "panelClose", "tip", "crosshair", "walkhint", "err", "loading", "ldBar", "dayTag"):
            self.assertIn(f'id="{el}"', html, el)

    def test_streaks_are_capped_and_respect_reduced_motion(self):
        s = read("js", "streaks.js")
        self.assertRegex(s, r"MAX:\s*[1-6]\b")
        self.assertIn("reducedMotion", s)
        self.assertIn("C.HUB", s)

    def test_town_hall_is_the_central_hub_and_old_anchors_redirect(self):
        th = read("js", "buildings", "townhall.js")
        self.assertRegex(th, r"pos:\s*\[0,\s*0\]")
        self.assertIn("Town Hall (Council)", th)
        al = read("js", "buildings", "council.js")
        for old in ("council", "cityhall"):
            self.assertRegex(al, rf"'?{old}'?:\s*'townhall'")
        roles = read("js", "roles.js")
        self.assertIn("id: 'council', name: 'Council', icon: '\u2696\ufe0f', color: 0xe040fb, building: 'townhall'", roles)

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
        k = read("js", "buildings", "kiosk.js")
        self.assertIn("if (!P) return", k)                       # public site: empty state before any private access
        for bad in ("fetch(", "XMLHttpRequest", "private.json", "localStorage"):
            self.assertNotIn(bad, k)
        self.assertNotIn("[1, 1]", read("js", "world.js").split("Central plaza")[1][:900])   # no planter under the kiosk


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
        for given, want in (("y = pi^3 - pi^2*x", "right"), ("-\u03c0^2(x-pi)", "right"), ("-pi^2x+pi^3", "right"),
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
