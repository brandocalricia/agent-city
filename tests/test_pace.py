"""tools/pace.py: estimated used %, reserve release, reset roll-forward, sessions left, tier choice, privacy of output."""
import datetime as dt, io, json, os, sys, unittest
from contextlib import redirect_stdout
from helpers import ROOT, TempDir
sys.path.insert(0, os.path.join(ROOT, "tools"))
import pace

T = pace.parse_t


def budget(**kw):
    b = {"reset_local": "2026-10-14T18:40", "reset_period_days": 7, "timezone": "America/Denver", "reserve_pct": 8,
         "reserve_release_hours_before_reset": 12, "target_used_pct_at_reset": 97,
         "readings": [{"at": "2026-10-07T23:27", "used_pct": 7, "source": "test"}],
         "calibration": {"pct_per_tier": {"S": 0.75, "M": 1.5, "L": 2.5}},
         "session_times_local": ["08:49", "20:49", "23:49"], "sessions": [], "adhoc": []}
    b.update(kw)
    return b


class Pace(unittest.TestCase):
    def test_parse_t_accepts_space_seconds_and_offsets(self):
        want = dt.datetime(2026, 10, 8, 22, 55)
        for raw in ("2026-10-08T22:55", "2026-10-08 22:55", "2026-10-08T22:55:07-06:00", " 2026-10-08 22:55:00 "):
            self.assertEqual(T(raw), want, raw)

    def test_mixed_timestamp_formats_do_not_break_pacing(self):
        b = budget(sessions=[{"at": "2026-10-08 00:10", "tier": "S", "what": "x"}],
                   adhoc=[{"at": "2026-10-08T00:20:00-06:00", "tier": "M", "task": "x"}])
        r = pace.compute(b, T("2026-10-08T01:15"))
        self.assertEqual(r["logged_since_reading"], 2)

    def test_sums_sessions_and_adhoc_after_latest_reading_only(self):
        b = budget(sessions=[{"at": "2026-10-07T20:00", "tier": "L", "what": "before reading"},
                             {"at": "2026-10-07T23:56", "tier": "S", "what": "x"}],
                   adhoc=[{"at": "2026-10-08T00:35", "tier": "L", "est_pct": 4, "task": "x"},
                          {"at": "2026-10-08T00:50", "tier": "M", "task": "x"}])
        r = pace.compute(b, T("2026-10-08T01:15"))
        self.assertEqual(r["est_used_pct"], 7 + 0.75 + 4 + 1.5)   # est_pct wins over tier; pre-reading entry ignored
        self.assertEqual(r["logged_since_reading"], 3)

    def test_newer_reading_replaces_estimates(self):
        b = budget(readings=[{"at": "2026-10-07T23:27", "used_pct": 7}, {"at": "2026-10-08T06:00", "used_pct": 20}],
                   adhoc=[{"at": "2026-10-08T01:00", "tier": "L"}, {"at": "2026-10-08T07:00", "tier": "S"}])
        self.assertEqual(pace.compute(b, T("2026-10-08T08:00"))["est_used_pct"], 20.75)

    def test_session_estimate_pct_key_is_read(self):
        b = budget(sessions=[{"at": "2026-10-08T01:00", "tier": "S", "estimate_pct": 2.0}])
        self.assertEqual(pace.compute(b, T("2026-10-08T08:00"))["est_used_pct"], 9)

    def test_future_entries_not_counted(self):
        b = budget(adhoc=[{"at": "2026-10-09T01:00", "tier": "L"}])
        self.assertEqual(pace.compute(b, T("2026-10-08T08:00"))["est_used_pct"], 7)

    def test_reserve_held_then_released_in_final_12h(self):
        early = pace.compute(budget(), T("2026-10-10T08:49"))
        late = pace.compute(budget(), T("2026-10-14T08:49"))
        self.assertEqual(early["reserve_held_pct"], 8)
        self.assertEqual(early["spendable_pct"], 97 - 7 - 8)
        self.assertEqual(late["reserve_held_pct"], 0)
        self.assertEqual(late["spendable_pct"], 90)

    def test_reset_rolls_forward_and_old_reading_is_dropped(self):
        r = pace.compute(budget(), T("2026-10-15T08:49"))
        self.assertEqual(r["reset"], "2026-10-21T18:40")
        self.assertEqual(r["reset_rolled_forward"], 1)
        self.assertEqual(r["est_used_pct"], 0)          # last week's reading does not carry over
        r2 = pace.compute(budget(), T("2026-10-30T08:00"))
        self.assertEqual(r2["reset"], "2026-11-04T18:40")
        self.assertEqual(r2["reset_rolled_forward"], 3)

    def test_sessions_left_counts_scheduled_slots_including_this_one(self):
        r = pace.compute(budget(), T("2026-10-14T08:49"))
        self.assertEqual(r["sessions_left"], 1)          # 08:49 today; 20:49 is after the 18:40 reset
        r = pace.compute(budget(), T("2026-10-13T20:49"))
        self.assertEqual(r["sessions_left"], 3)          # 20:49, 23:49, 08:49
        self.assertGreaterEqual(pace.compute(budget(), T("2026-10-14T18:00"))["sessions_left"], 1)

    def test_tiers_scale_with_budget(self):
        self.assertEqual(pace.compute(budget(), T("2026-10-08T08:49"))["recommend"], "L")
        mid = budget(readings=[{"at": "2026-10-12T08:00", "used_pct": 80}])
        self.assertEqual(pace.compute(mid, T("2026-10-12T08:49"))["recommend"], "S")         # 9% over 7 sessions
        heavy = budget(readings=[{"at": "2026-10-12T08:00", "used_pct": 85}])
        self.assertEqual(pace.compute(heavy, T("2026-10-12T08:49"))["recommend"], "minimal")  # 4% over 7 sessions
        spent = budget(readings=[{"at": "2026-10-12T08:00", "used_pct": 95}])
        self.assertEqual(pace.compute(spent, T("2026-10-12T08:49"))["recommend"], "skip")

    def test_way_over_pace_forces_minimal_or_skip(self):
        b = budget(readings=[{"at": "2026-10-08T06:00", "used_pct": 40}])   # ~4% pace line, 36 pts over
        self.assertEqual(pace.compute(b, T("2026-10-08T08:49"))["recommend"], "minimal")
        b = budget(readings=[{"at": "2026-10-08T06:00", "used_pct": 50}])
        self.assertEqual(pace.compute(b, T("2026-10-08T08:49"))["recommend"], "skip")

    def test_cli_prints_numbers_but_never_task_text(self):
        with TempDir() as d:
            p = os.path.join(d, "budget.json")
            with open(p, "w") as f:
                json.dump(budget(adhoc=[{"at": "2026-10-08T00:35", "tier": "L", "task": "SECRET-TASK-TEXT", "source": "SECRET-SRC"}],
                                 sessions=[{"at": "2026-10-07T23:56", "tier": "S", "what": "SECRET-WHAT"}]), f)
            for args in ([], ["--json"]):
                out = io.StringIO()
                with redirect_stdout(out):
                    self.assertEqual(pace.main(["--budget", p, "--now", "2026-10-08T08:49"] + args), 0)
                self.assertNotIn("SECRET", out.getvalue())
                self.assertIn("recommend", out.getvalue())
            self.assertEqual(json.loads(io.StringIO(out.getvalue()).read())["est_used_pct"], 10.25)

    def test_missing_budget_is_fine(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(pace.main(["--budget", "/nonexistent/budget.json"]), 0)
        self.assertIn("no budget.json", out.getvalue())

    def test_default_slots_match_every_3_hours_routine(self):
        self.assertEqual(pace.DEFAULT_SLOTS, ["%02d:49" % h for h in range(2, 24, 3)])
        b = budget()
        del b["session_times_local"]                      # falls back to the 8 default slots
        self.assertEqual(pace.compute(b, T("2026-10-14T02:49"))["sessions_left"], 6)   # 02:49 ... 17:49 before 18:40
        self.assertEqual(pace.compute(b, T("2026-10-13T20:49"))["sessions_left"], 8)   # 20:49, 23:49 + 6 on reset day

    def test_deterministic(self):
        b = budget(adhoc=[{"at": "2026-10-08T00:35", "tier": "M"}])
        self.assertEqual(pace.compute(b, T("2026-10-09T08:49")), pace.compute(b, T("2026-10-09T08:49")))


    def test_per_source_breakdown_counts_all_bots_and_reading_drift(self):
        # Prev reading 7; logged 1.5 Agent City ad-hoc before next reading 10 -> other drift = 1.5
        # After latest reading: one session, one math-tutor adhoc, one default Agent City adhoc
        b = budget(
            readings=[{"at": "2026-10-07T23:27", "used_pct": 7}, {"at": "2026-10-08T06:00", "used_pct": 10}],
            sessions=[{"at": "2026-10-08T07:00", "tier": "S", "estimate_pct": 0.75}],
            adhoc=[
                {"at": "2026-10-08T01:00", "tier": "M", "est_pct": 1.5, "source": "agent-city"},
                {"at": "2026-10-08T07:30", "tier": "L", "est_pct": 2.0, "source": "math-tutor"},
                {"at": "2026-10-08T08:00", "tier": "M", "est_pct": 1.0},
            ],
        )
        r = pace.compute(b, T("2026-10-08T08:49"))
        self.assertEqual(r["est_used_pct"], 13.75)
        bs = r["by_source"]
        self.assertEqual(bs["sessions_pct"], 0.75)
        self.assertEqual(bs["math_tutor_pct"], 2.0)
        self.assertEqual(bs["agent_city_adhoc_pct"], 1.0)
        self.assertEqual(bs["other_pct"], 1.5)
        with TempDir() as d:
            path = os.path.join(d, "budget.json")
            with open(path, "w") as f:
                json.dump(b, f)
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(pace.main(["--budget", path, "--now", "2026-10-08T08:49"]), 0)
            text = out.getvalue()
            self.assertIn("by source:", text)
            self.assertIn("sessions 0.75%", text)
            self.assertIn("Agent City ad-hoc 1.0%", text)
            self.assertIn("math-tutor 2.0%", text)
            self.assertIn("other (reading drift) 1.5%", text)


if __name__ == "__main__":
    unittest.main()
