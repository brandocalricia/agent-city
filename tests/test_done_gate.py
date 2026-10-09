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
    post_worker_done,
    recur_done_evidence,
    strike_decision,
    worker_cannot_post,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
BAD_IDS = ("gdb9recur1", "gdb9recur1-2", "gdb9recur1-3", "gdb9recur1-4")


def main():
    step = "\n".join(
        [
            "refusal with no evidence",
            "model: command-a-03-2025",
            "lane: cohere/command-a-03-2025 HTTP 200",
            "step: b9mods1bre1",
            "log: timeout noted",
        ]
    )
    first = strike_decision(0, step, "", 1000)
    second = strike_decision(first["fail_count"], step, "", 1000)
    assert first["action"] == "retry" and first["retry_after"] is None, first
    assert first["split"] is False, first
    assert second["action"] == "retry" and second["retry_after"] is None, second
    assert second["split"] is True, second
    assert second["post_blocked"] is False, second
    print("PASS refusal fails over at once")
    print("PASS two refusals on the same step split the prompt and one refusal does not")

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

    other = "The dashboard is done and everything passed."
    assert approve_worker_done("b9mods1", other) is False
    print("PASS a non-b9recur bad draft is refused")
    assert approve_worker_done("b9stats1", "PASS total 8565050\n") is False
    print("PASS total 8565050 with no as-of is refused")
    assert approve_worker_done("b9stats1", "as of now\nPASS total 8565050\n") is False
    print("PASS as of now is refused")

    posted = []

    def capture(body):
        posted.append(body)
        return True

    assert post_worker_done("b9mods1", other, capture, done_id="gdb9mods1") is False
    assert posted == []
    live = "As-of 2026-10-09T21:53:36Z\nPASS live reading total 8565050\n"
    assert post_worker_done("b9mods1", live, capture, done_id="gdb9mods1") is True
    assert len(posted) == 1 and "\nDONE\n" in posted[0]
    print("PASS a bad worker draft is not posted")

    prompt = "Do not post to the Channel. Do not run gh. You have no Channel token."
    command = ["caffeinate", "-i", "grok", "--prompt-file", "task.md", "--no-subagents"]
    clean = {"PATH": "/usr/bin", "AGENT_CITY_HEADLESS": "1"}
    assert worker_cannot_post(command, clean, prompt) is True
    assert worker_cannot_post(command, {"GH_TOKEN": "nope"}, prompt) is False
    assert worker_cannot_post(command + ["gh", "api"], clean, prompt) is False
    print("PASS a worker process has no Channel token and no post call")

    import runner_step

    bad_calls = []
    runner_step.post_raw = lambda body, queue=True: bad_calls.append(body) or True
    assert runner_step.post_worker_done("b9stats1", "PASS total 8565050\n", "gdb9stats1") is False
    assert bad_calls == []
    print("PASS the runner post path makes zero calls for a bad draft")
    cmd, env, prompt = runner_step.worker_launch({"id": "b9testgate", "body": "ping"})
    assert worker_cannot_post(cmd, env, prompt) is True
    print("PASS the real worker launch has no Channel token and no post call")


if __name__ == "__main__":
    main()
