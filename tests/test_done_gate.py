"""The runner blocks a recur DONE that lacks a SHA and a PASS line."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from done_gate import (  # noqa: E402
    blocked_has_lane_detail,
    newer_open_rejection,
    recur_done_evidence,
    strike_decision,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
BAD_IDS = ("gdb9recur1", "gdb9recur1-2", "gdb9recur1-3", "gdb9recur1-4")


def main():
    decision = strike_decision(
        2,
        "\n".join(
            [
                "refusal with no evidence",
                "model: command-a-03-2025",
                "lane: cohere/command-a-03-2025 HTTP 200",
                "step: b9mods1bre1",
                "log: timeout noted",
            ]
        ),
        "",
        1000,
    )
    assert decision["action"] == "retry", decision
    assert decision["retry_after"] is None, decision
    assert decision["post_blocked"] is False, decision
    assert decision["split"] is True, decision
    print("PASS refusal fails over at once")

    bare = strike_decision(2, "headless exit 1", "", 1000)
    assert bare["action"] == "retry", bare
    assert bare["retry_after"] is None, bare
    assert bare["post_blocked"] is False, bare
    assert not blocked_has_lane_detail(bare["blocked"])
    print("PASS no BLOCKED post goes out without the model, lane, and log line")

    for name in BAD_IDS:
        body = (FIXTURES / f"{name}.md").read_text()
        assert not recur_done_evidence(body), name
        print(f"PASS {name} blocked")

    good = "Commit a1ad728\nPASS refusal fails over at once\n"
    assert recur_done_evidence(good)
    print("PASS a commit SHA plus a PASS line is accepted")

    rows = [
        {
            "body": (
                "[from:grok-bot] [id:b9recur1re5] [re:gdb9recur1-4]\n"
                "Not accepted. b9recur1 stays open.\n"
            )
        }
    ]
    assert newer_open_rejection("b9recur1", rows)
    assert not newer_open_rejection("b9recur1re5", rows)
    print("PASS a newer rejection blocks another DONE for b9recur1")


if __name__ == "__main__":
    main()
