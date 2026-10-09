"""Pure DONE and refusal gates for the Agent City runner. No I/O."""

import re

SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b", re.IGNORECASE)
PASS_LINE_RE = re.compile(r"(?m)^[ \t]*PASS\s+\S")
ASOF_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
CHANNEL_TOKEN_KEYS = {"GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN"}


def recur_done_evidence(text):
    """A b9recur DONE needs a commit SHA and a pasted PASS line."""
    body = text or ""
    return bool(SHA_RE.search(body)) and bool(PASS_LINE_RE.search(body))


def blocked_has_lane_detail(text):
    """A BLOCKED post must name the model, the lane, and the log line."""
    low = (text or "").lower()
    return "model:" in low and "lane:" in low and "log:" in low


def is_refusal_error(error):
    low = (error or "").lower()
    return "refusal" in low or "worker draft rejected" in low


def strike_decision(fail_count, error, log_tail_text, now):
    """A refusal fails over at once. A BLOCKED body without lane detail is not posted.

    A real outage still backs off on the third strike, and only when the body
    names the model, the lane, and the log line. "max turns reached" retries
    immediately and does not post BLOCKED.
    """
    if "max turns reached" in (error or "").lower():
        return {
            "action": "retry",
            "fail_count": 0,
            "retry_after": None,
            "blocked": "",
            "post_blocked": False,
            "split": False,
        }
    count = int(fail_count or 0) + 1
    err = (error or "")[:500]
    tail = log_tail_text or ""
    detail = "\n".join(part for part in (err, tail) if part)
    if is_refusal_error(error):
        return {
            "action": "retry",
            "fail_count": count,
            "retry_after": None,
            "blocked": detail,
            "post_blocked": False,
            "split": count >= 2,
        }
    if count < 3:
        return {
            "action": "retry",
            "fail_count": count,
            "retry_after": None,
            "blocked": "",
            "post_blocked": False,
            "split": False,
        }
    if not blocked_has_lane_detail(detail):
        return {
            "action": "retry",
            "fail_count": count,
            "retry_after": None,
            "blocked": detail,
            "post_blocked": False,
            "split": False,
        }
    return {
        "action": "backoff",
        "fail_count": 0,
        "retry_after": int(now) + 600,
        "blocked": detail,
        "post_blocked": True,
        "split": False,
    }


def has_reading(text):
    """A commit SHA or a live reading with an as-of time."""
    body = text or ""
    if SHA_RE.search(body):
        return True
    low = body.lower()
    if "as-of" in low or "as of " in low:
        return True
    return bool(ASOF_RE.search(body))


def approve_worker_done(task_id, report):
    """Every DONE needs a SHA or an as-of reading, plus a PASS line."""
    text = report or ""
    if not str(task_id).strip() or not text.strip():
        return False
    if not PASS_LINE_RE.search(text):
        return False
    return has_reading(text)


def command_a_may_post(lane_text, report):
    """command-a-03-2025 stays off DONE posts until the draft passes the gate."""
    if "command-a-03-2025" not in (lane_text or "").lower():
        return True
    return approve_worker_done("command-a", report or "")


def post_worker_done(task_id, report, post, lane_text="", done_id=None):
    """The runner's only DONE post. A bad draft does not call post."""
    if not approve_worker_done(task_id, report):
        return False
    if not command_a_may_post(lane_text, report):
        return False
    marker = done_id or f"gd{task_id}"
    body = f"[from:grok-build] [id:{marker}] [re:{task_id}]\nDONE\n{report}\n"
    return bool(post(body))


def worker_cannot_post(command, env, prompt):
    """True when this worker launch has no Channel token and no post call."""
    joined = " ".join(str(part) for part in (command or [])).lower()
    if "gh api" in joined or "issues/1/comments" in joined or "post_raw" in joined:
        return False
    for key in env or {}:
        upper = str(key).upper()
        if upper in CHANNEL_TOKEN_KEYS:
            return False
        if "GITHUB" in upper and "TOKEN" in upper:
            return False
    low = (prompt or "").lower()
    if "do not post to the channel" not in low or "do not run gh" not in low:
        return False
    if "gh api" in low or "issues/1/comments" in low:
        return False
    return True


def newer_open_rejection(task_id, rows):
    """True when a later grok-bot note rejected this task and is still open."""
    short = str(task_id)
    low_id = short.lower()
    for row in rows:
        body = row.get("body") or ""
        first = body.lstrip().splitlines()[0] if body.strip() else ""
        if "grok-bot" not in first.lower():
            continue
        match = re.search(r"\[id:([A-Za-z0-9_-]+)\]", first)
        own = match.group(1) if match else ""
        if own.lower() == low_id:
            continue
        low = body.lower()
        if "not accepted" not in low:
            continue
        if (
            f"gd{low_id}" in low
            or f"{low_id} stays open" in low
            or f"done for {low_id}" in low
        ):
            return True
    return False
