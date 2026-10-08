"""install.sh / update.sh with a file:// copy of the repo: fresh install, idempotency, backups, uninstall, offline,
corrupt or partial downloads, never clobbering foreign files, throttle, lock, kill switch, pin, bash 3.2 rules."""
import os, re, shutil, time, unittest
from helpers import BASH, GB, TempDir, env, make_raw, rewrite_manifest, run, sha

INSTALLED = ["rules/40-agent-city.md", "skills/city-council/SKILL.md", "skills/city-apply/SKILL.md", "skills/bot-link/SKILL.md", "agent-city/comms.py",
             "hooks/agent-city.json", "agent-city/update.sh", "agent-city/city_apply.py"]


class Base(unittest.TestCase):
    def setUp(self):
        self.t = TempDir(); self.d = self.t.__enter__()
        self.home = os.path.join(self.d, "home"); os.makedirs(self.home)
        self.raw_dir = os.path.join(self.d, "raw")
        self.raw = make_raw(self.raw_dir)
        self.G = os.path.join(self.home, ".grok"); self.D = os.path.join(self.G, "agent-city")
        self.e = env(self.home, self.raw)

    def tearDown(self):
        self.t.__exit__()

    def install(self, *args, e=None):
        return run([BASH, os.path.join(GB, "install.sh")] + list(args), e or self.e)

    def update(self, *args, e=None):
        return run([BASH, os.path.join(self.D, "update.sh")] + list(args), e or self.e)

    def snapshot(self):
        out = {}
        for root, _, files in os.walk(self.G):
            for f in files:
                p = os.path.join(root, f)
                if ".last-update" not in p and "backup" not in p and ".lock" not in p:
                    out[os.path.relpath(p, self.G)] = sha(p)
        return out

    def change_raw(self, rel, text, manifest=True):
        open(os.path.join(self.raw_dir, rel), "a").write(text)
        if manifest:
            rewrite_manifest(self.raw_dir)


class Install(Base):
    def test_fresh_install(self):
        r = self.install()
        self.assertEqual(r.returncode, 0, r.stderr)
        for f in INSTALLED:
            self.assertTrue(os.path.getsize(os.path.join(self.G, f)) > 0, f)
        for f in ("suggestions.md", "IDEALS.md", "prompts.md", "applied.json", "pending.txt"):
            self.assertTrue(os.path.exists(os.path.join(self.D, f)), f)
        self.assertTrue(os.access(os.path.join(self.D, "update.sh"), os.X_OK))
        self.assertRegex(open(os.path.join(self.D, "pending.txt")).read(), r"^\d+\nrepos: ")

    def test_rerun_is_idempotent(self):
        self.install(); before = self.snapshot()
        r = self.install()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(os.path.exists(os.path.join(self.D, "backup")))

    def test_foreign_file_is_backed_up_then_replaced(self):
        os.makedirs(os.path.join(self.G, "rules"))
        mine = os.path.join(self.G, "rules", "40-agent-city.md")
        open(mine, "w").write("the owner's own rule\n")
        self.assertEqual(self.install().returncode, 0)
        backups = [os.path.join(r, f) for r, _, fs in os.walk(os.path.join(self.D, "backup")) for f in fs]
        self.assertTrue(any(open(b).read() == "the owner's own rule\n" for b in backups))
        self.assertIn("Agent City", open(mine).read())

    def test_other_files_untouched(self):
        os.makedirs(os.path.join(self.G, "rules")); os.makedirs(os.path.join(self.G, "hooks"))
        keep = {"config.toml": "[x]\n", "rules/10-auto-route.md": "route\n", "hooks/collision.json": "{}\n"}
        for k, v in keep.items():
            open(os.path.join(self.G, k), "w").write(v)
        self.install(); self.install("--uninstall")
        for k, v in keep.items():
            self.assertEqual(open(os.path.join(self.G, k)).read(), v)

    def test_uninstall_keeps_state(self):
        self.install()
        open(os.path.join(self.D, "applied.log"), "a").write('{"id":"AC-00000000","status":"applied"}\n')
        r = self.install("--uninstall")
        self.assertEqual(r.returncode, 0, r.stderr)
        for f in INSTALLED:
            self.assertFalse(os.path.exists(os.path.join(self.G, f)), f)
        self.assertTrue(os.path.exists(os.path.join(self.D, "applied.log")))

    def test_uninstall_keeps_message_link_config(self):
        self.install()
        for f in ("bot-webhook.env", "comms-state.json"):
            with open(os.path.join(self.D, f), "w") as fh:
                fh.write("kept\n")
        self.install("--uninstall")
        self.assertFalse(os.path.exists(os.path.join(self.D, "comms.py")))
        self.assertFalse(os.path.exists(os.path.join(self.G, "skills", "bot-link")))
        for f in ("bot-webhook.env", "comms-state.json"):
            self.assertTrue(os.path.exists(os.path.join(self.D, f)), f)

    def test_update_installs_message_link(self):
        self.install()
        for f in ("agent-city/comms.py", "skills/bot-link/SKILL.md"):
            os.remove(os.path.join(self.G, f))
        self.update("--force")
        self.assertTrue(os.access(os.path.join(self.D, "comms.py"), os.X_OK))
        self.assertTrue(os.path.exists(os.path.join(self.G, "skills", "bot-link", "SKILL.md")))

    def test_offline_install_changes_nothing(self):
        r = self.install(e=env(self.home, "file://" + os.path.join(self.d, "nowhere")))
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(os.path.exists(os.path.join(self.G, "rules", "40-agent-city.md")))

    def test_checksum_mismatch_aborts_before_touching_anything(self):
        self.install(); before = self.snapshot()
        self.change_raw("grok-build/skills/city-apply/SKILL.md", "tampered\n", manifest=False)
        self.change_raw("grok-build/rules/40-agent-city.md", "new line\n", manifest=False)
        r = self.install()
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_truncated_installer_runs_nothing(self):
        src = open(os.path.join(GB, "install.sh")).read()
        for cut in (0.3, 0.6, 0.95):
            r = run([BASH], self.e, input=src[: int(len(src) * cut)])
            self.assertFalse(os.path.exists(self.G), f"cut at {cut}: {r.stdout}{r.stderr}")


class Update(Base):
    def setUp(self):
        super().setUp()
        r = self.install()
        assert r.returncode == 0, r.stderr
        self.sugg = os.path.join(self.D, "suggestions.md")

    def test_offline_update_keeps_files_and_exits_0(self):
        before = self.snapshot()
        r = self.update("--force", e=env(self.home, "file://" + os.path.join(self.d, "nowhere")))
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_new_version_is_applied(self):
        self.change_raw("grok-build/suggestions.md", "\nnew line\n")
        self.update("--force")
        self.assertTrue(open(self.sugg).read().endswith("new line\n"))

    def test_corrupt_download_is_rejected(self):
        old = open(self.sugg).read()
        self.change_raw("grok-build/suggestions.md", "\ncorrupted\n", manifest=False)
        self.update("--force")
        self.assertEqual(open(self.sugg).read(), old)

    def test_partial_download_is_rejected(self):
        old = open(self.sugg).read()
        self.change_raw("grok-build/suggestions.md", "\nnew\n")
        p = os.path.join(self.raw_dir, "grok-build", "suggestions.md")
        data = open(p).read(); open(p, "w").write(data[: len(data) // 2])
        self.update("--force")
        self.assertEqual(open(self.sugg).read(), old)

    def test_truncated_manifest_updates_nothing(self):
        before = self.snapshot()
        self.change_raw("grok-build/suggestions.md", "\nnew\n")
        m = os.path.join(self.raw_dir, "grok-build", "manifest.txt")
        open(m, "w").write(open(m).read().replace("end\n", ""))
        self.update("--force")
        self.assertEqual(self.snapshot()["agent-city/suggestions.md"], before["agent-city/suggestions.md"])

    def test_manifest_cannot_write_arbitrary_paths(self):
        m = os.path.join(self.raw_dir, "grok-build", "manifest.txt")
        evil = os.path.join(self.raw_dir, "evil.sh"); open(evil, "w").write("Agent City\n")
        lines = open(m).read().replace("end\n", f"{sha(evil)}  evil.sh\n{sha(evil)}  ../../evil.sh\nend\n")
        open(m, "w").write(lines)
        self.update("--force")
        found = [f for r, _, fs in os.walk(self.d) for f in fs if f == "evil.sh" and r != self.raw_dir]
        self.assertEqual(found, [])

    def test_never_clobbers_foreign_file(self):
        p = os.path.join(self.G, "skills", "city-council", "SKILL.md")
        open(p, "w").write("the owner's own council skill\n")
        self.change_raw("grok-build/skills/city-council/SKILL.md", "\nnew\n")
        self.update("--force")
        self.assertEqual(open(p).read(), "the owner's own council skill\n")

    def test_throttle(self):
        old = open(self.sugg).read()
        self.change_raw("grok-build/suggestions.md", "\nnew\n")
        self.update()
        self.assertEqual(open(self.sugg).read(), old, "within 30 minutes: no download")
        open(os.path.join(self.D, ".last-update"), "w").write(str(int(time.time()) - 1801))
        self.update()
        self.assertNotEqual(open(self.sugg).read(), old)

    def test_fresh_lock_skips_stale_lock_is_cleared(self):
        old = open(self.sugg).read()
        self.change_raw("grok-build/suggestions.md", "\nnew\n")
        lock = os.path.join(self.D, ".update.lock"); os.mkdir(lock)
        self.update("--force")
        self.assertEqual(open(self.sugg).read(), old, "another session holds the lock")
        t = time.time() - 600; os.utime(lock, (t, t))
        self.update("--force")
        self.assertNotEqual(open(self.sugg).read(), old)
        self.assertFalse(os.path.exists(lock))

    def test_kill_switch_and_pin(self):
        open(os.path.join(self.D, "pin"), "w").close()
        rule = os.path.join(self.G, "rules", "40-agent-city.md"); old_rule = open(rule).read()
        self.change_raw("grok-build/rules/40-agent-city.md", "\npinned?\n")
        self.change_raw("grok-build/suggestions.md", "\nfeed still updates\n")
        self.update("--force")
        self.assertEqual(open(rule).read(), old_rule)
        self.assertTrue(open(self.sugg).read().endswith("feed still updates\n"))
        open(os.path.join(self.D, "off"), "w").close()
        self.change_raw("grok-build/suggestions.md", "\noff\n")
        self.update("--force")
        self.assertFalse(open(self.sugg).read().endswith("off\n"))
        self.assertEqual(open(os.path.join(self.D, "pending.txt")).read().split("\n")[0], "0")

    def test_code_updates_are_logged(self):
        self.change_raw("grok-build/rules/40-agent-city.md", "\nchanged\n")
        self.update("--force")
        self.assertIn("grok-build/rules/40-agent-city.md", open(os.path.join(self.D, "updates.log")).read())

    def test_self_update_while_running(self):
        self.change_raw("grok-build/update.sh", "\n# newer\n")
        r = self.update("--force")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(open(os.path.join(self.D, "update.sh")).read().endswith("# newer\n"))

    def test_applied_state_never_overwritten(self):
        p = os.path.join(self.D, "applied.json"); open(p, "w").write('{"AC-11111111": {"status": "applied"}}\n')
        self.install(); self.update("--force")
        self.assertIn("AC-11111111", open(p).read())


class Bash32(unittest.TestCase):
    def test_syntax(self):
        for f in ("install.sh", "update.sh"):
            r = run([BASH, "-n", os.path.join(GB, f)], dict(os.environ))
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_no_bash4_features(self):
        bad = [r"declare -A", r"\bmapfile\b", r"\breadarray\b", r"\$\{[A-Za-z_]+(,,|\^\^)", r"\|&", r"&>>", r"\bcoproc\b",
               r"\blocal -n\b", r"\bsed -i\b", r"readlink -f", r"\$\{[A-Za-z_]+:-?[0-9]+:"]
        for f in ("install.sh", "update.sh"):
            src = open(os.path.join(GB, f)).read()
            for pat in bad:
                self.assertIsNone(re.search(pat, src), f"{f}: {pat}")

    def test_wrapped_in_main(self):
        for f in ("install.sh", "update.sh"):
            lines = [l for l in open(os.path.join(GB, f)).read().splitlines() if l.strip() and not l.startswith("#")]
            self.assertTrue(lines[-1].startswith("main ") or lines[-2].startswith("main "), f)


if __name__ == "__main__":
    unittest.main()
