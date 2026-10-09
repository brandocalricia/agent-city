"""The runner blocks a recur DONE that lacks a SHA and a PASS line."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from done_gate import (  # noqa: E402
    approve_worker_done,
    blocked_has_lane_detail,
    command_a_may_post,
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
    print("PASS the same step splits the prompt after two refusals")

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

    bad = (FIXTURES / "gdb9recur1.md").read_text()
    assert approve_worker_done("b9recur1", bad) is False
    good = (
        "Commit 98bea30\n"
        "PASS a worker-drafted DONE goes through the gate before it is posted\n"
    )
    assert approve_worker_done("b9recur1", good) is True
    print("PASS a worker-drafted DONE goes through the gate before it is posted")

    lane = "lane: cohere/command-a-03-2025 HTTP 200"
    assert command_a_may_post(lane, bad) is False
    assert command_a_may_post(lane, good) is True
    assert command_a_may_post("lane: main grok-4.7-build", "HTTP 200 and a real count") is True
    print("PASS command-a-03-2025 cannot post a DONE until the draft passes the gate")


if __name__ == "__main__":
    main()
