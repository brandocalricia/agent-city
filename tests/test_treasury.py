"""tools/treasury.py: lifetime totals accumulate (all ledger entries + archived), money is derived from the stated price,
weekly numbers only appear when budget.json exists and never carry task text."""
import json, os, sys, unittest, datetime as dt
from helpers import ROOT, TempDir
sys.path.insert(0, os.path.join(ROOT, "tools"))
import treasury


def costs(n=15, archived=None, price=6.0):
    return {"price": {"usd_per_mtok": price, "basis": "test"},
            "ledger": [{"session": f"s{i}", "kb_pushed": 10.0, "est_tokens": 2500, "saved_tokens": 1000} for i in range(n)],
            "savings": [{"change": "a", "tokens_saved": 5}, {"change": "b", "tokens_saved": 50, "link": "https://x"},
                        {"change": "c"}, {"change": "d", "tokens_saved": 7}],
            **({"archived": archived} if archived else {})}


class Treasury(unittest.TestCase):
    def test_lifetime_counts_every_entry_and_archived(self):
        lt = treasury.lifetime(costs(15, {"sessions": 5, "kb_pushed": 50, "est_tokens": 12500, "saved_tokens": 4000}))
        self.assertEqual(lt["sessions"], 20)
        self.assertEqual(lt["est_tokens"], 15 * 2500 + 12500)
        self.assertEqual(lt["saved_tokens"], 15 * 1000 + 4000)
        self.assertEqual(lt["saved_usd"], round(19000 * 6 / 1e6, 2))
        self.assertEqual(lt["avg_tokens_per_build"], 2500)

    def test_trend_is_capped_but_lifetime_is_not(self):
        s = treasury.summarize(costs(15), "/nonexistent/budget.json")
        self.assertEqual(len(s["trend"]), treasury.LEDGER_IN_DATA)
        self.assertEqual(s["trend"][-1]["session"], "s14")
        self.assertEqual(s["lifetime"]["sessions"], 15)

    def test_no_price_means_no_dollars(self):
        lt = treasury.lifetime(costs(2, price=None))
        self.assertIsNone(lt["est_usd"]); self.assertIsNone(lt["saved_usd"])

    def test_biggest_savings_sorted(self):
        b = treasury.summarize(costs(1), "/nonexistent/budget.json")["biggest"]
        self.assertEqual([x["change"] for x in b], ["b", "d", "a"])

    def test_week_absent_without_budget_and_never_has_task_text(self):
        self.assertIsNone(treasury.summarize(costs(1), "/nonexistent/budget.json")["week"])
        with TempDir() as d:
            p = os.path.join(d, "budget.json")
            with open(p, "w") as f:
                json.dump({"reset_local": "2026-10-14T18:40", "readings": [{"at": "2026-10-07T23:27", "used_pct": 7, "source": "SECRET"}],
                           "adhoc": [{"at": "2026-10-08T00:30", "tier": "L", "task": "SECRET"}], "sessions": [{"at": "2026-10-08T00:40", "tier": "S", "what": "SECRET"}]}, f)
            w = treasury.summarize(costs(1), p, now=dt.datetime(2026, 10, 8, 8, 49))["week"]
            self.assertEqual(w["est_used_pct"], 7 + 2.5 + 0.75)
            self.assertNotIn("SECRET", json.dumps(w))

    def test_repo_costs_json_is_consistent(self):
        c = json.load(open(os.path.join(ROOT, "costs.json")))
        self.assertGreater(c["price"]["usd_per_mtok"], 0)
        self.assertTrue(c["price"]["source"].startswith("https://"))
        for e in c["ledger"]:
            self.assertEqual(e["est_tokens"] % 100, 0)
            self.assertAlmostEqual(e["est_tokens"], e["kb_pushed"] * 1024 / 4, delta=150)   # tokens = bytes / 4


if __name__ == "__main__":
    unittest.main()
