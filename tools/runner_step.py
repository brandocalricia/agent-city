#!/usr/bin/env python3
"""One pass of the Agent City runner. The shell loop calls this and then sleeps.

Posts use stable ids so a resume does not ACK or DONE the same task twice.
"""

import json
import os
import re
import signal
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass
from datetime import datetime, timezone
from pathlib import Path

from done_gate import (
    CHANNEL_TOKEN_KEYS,
    approve_worker_done,
    blocked_has_lane_detail,
    command_a_may_post,
    newer_open_rejection,
    post_worker_done as gate_post_worker_done,
    strike_decision as gate_strike,
)

ROOT = Path.home() / ".agent-city"
STATE = ROOT / "state.json"
STATUS = ROOT / "status.json"
TASK_PID = ROOT / "task.pid"
SEND = Path.home() / ".grok" / "agent-city" / "channel-send.py"
CURSOR = Path.home() / ".grok" / "agent-city" / "channel-cursor.json"
ACTIVITY = Path.home() / ".omniroute" / "activity.json"
GROK = Path.home() / ".grok" / "bin" / "grok"
PROMPTS = ROOT / "prompts"


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path, default):
    try:
        data = json.loads(path.read_text())
    except Exception:
        return default
    return data if isinstance(data, dict) else default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    os.replace(tmp, path)


def save_status(payload):
    """Atomic status write. Shares status.lock with the shell heartbeat."""
    import fcntl

    lock = ROOT / "status.lock"
    with lock.open("a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        save_json(STATUS, payload)


def default_state():
    cursor = load_json(CURSOR, {})
    handled = []
    for key in ("finished_ids", "noted_ids"):
        for item in cursor.get(key) or []:
            if item not in handled:
                handled.append(item)
    if "b9auto1" not in handled:
        handled.append("b9auto1")
    return {
        "handled_ids": handled,
        "acked_ids": [],
        "claimed": {},
        "last_handled_comment_id": 0,
        "last_heartbeat_epoch": int(time.time()),
        "last_change_epoch": 0,
        "updated": now_iso(),
        "current_task": "",
    }


def load_state():
    state = load_json(STATE, {})
    base = default_state()
    if not state:
        return base
    for key, value in base.items():
        state.setdefault(key, value)
    if not isinstance(state.get("handled_ids"), list):
        state["handled_ids"] = base["handled_ids"]
    if not isinstance(state.get("claimed"), dict):
        state["claimed"] = {}
    return state


def activity():
    data = load_json(ACTIVITY, {})
    lanes_up = data.get("lanes_up")
    lanes_total = data.get("lanes_total")
    if isinstance(lanes_up, int) and isinstance(lanes_total, int):
        health = f"{lanes_up}/{lanes_total} up"
    elif data.get("health") == "up":
        health = "up"
    else:
        health = "down" if not port_open() else "unknown"
    saved = data.get("free_tokens")
    if isinstance(saved, bool) or not isinstance(saved, int):
        saved = None
    mode = data.get("mode") if isinstance(data.get("mode"), str) else ""
    return health, saved, mode


def port_open():
    """Lane address lives in a local file so this source can be published."""
    try:
        host, port = (ROOT / "lane_addr.txt").read_text().split()
    except (OSError, ValueError):
        return False
    if not port.isdigit():
        return False
    try:
        proc = subprocess.run(
            ["nc", "-z", "-G", "2", host, port],
            capture_output=True,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return proc.returncode == 0


def write_status(state, queue_length):
    health, saved, mode = activity()
    payload = {
        "last_loop": now_iso(),
        "current_task": state.get("current_task") or "idle",
        "next_task": state.get("next_task") or "",
        "queue_length": queue_length,
        "provider_health": health,
        "saved_today": saved,
        "mode": mode or "unknown",
        "runner_pid": os.getppid(),
    }
    save_status(payload)
    state["updated"] = payload["last_loop"]
    save_json(STATE, state)


def fetch_comments():
    proc = subprocess.run(
        [
            "gh",
            "api",
            "--paginate",
            "repos/brandocalricia/agent-city-comms/issues/1/comments",
            "--jq",
            ".[] | {id:.id,created:.created_at,body:.body}",
        ],
        capture_output=True,
        text=True,
        timeout=40,
    )
    if proc.returncode != 0:
        err = (proc.stderr or "") + (proc.stdout or "")
        low = err.lower()
        if any(token in low for token in ("auth", "login", "401", "403", "bad credentials")):
            raise RuntimeError("auth")
        raise RuntimeError("network")
    rows = []
    for line in proc.stdout.splitlines():
        if line.strip():
            rows.append(json.loads(line))
    rows.sort(key=lambda row: (row.get("created") or "", row.get("id") or 0))
    return rows


def parse_task(body):
    import re

    if not isinstance(body, str):
        return None
    first = body.lstrip().splitlines()[0] if body.strip() else ""
    match = re.search(r"\[from:([^\]]+)\]\s*\[id:([A-Za-z0-9_-]+)\]", first)
    if not match:
        return None
    return match.group(1).lower(), match.group(2)


def claim_alive(pid):
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def pending_tasks(rows, state):
    handled = set(state.get("handled_ids") or [])
    claimed = state.get("claimed") or {}
    tasks = []
    for row in rows:
        parsed = parse_task(row.get("body") or "")
        if not parsed:
            continue
        sender, short = parsed
        if sender == "grok-build":
            continue
        if newer_open_rejection(short, rows):
            continue
        if short in handled and short not in set(state.get("reopen_ids") or []):
            continue
        owner = claimed.get(short)
        if owner and claim_alive(owner):
            continue
        retry_after = (state.get("retry_after") or {}).get(short) or 0
        try:
            if int(time.time()) < int(retry_after):
                continue
        except (TypeError, ValueError):
            pass
        tasks.append(
            {
                "id": short,
                "comment_id": row.get("id") or 0,
                "created": row.get("created") or "",
                "body": row.get("body") or "",
            }
        )
    def created(task):
        return task.get("created") or ""

    tests = [task for task in tasks if str(task["id"]).startswith("b9test")]
    rest = [task for task in tasks if not str(task["id"]).startswith("b9test")]
    tops = sorted([task for task in rest if is_top(task["body"])], key=created, reverse=True)
    highs = sorted(
        [task for task in rest if is_high(task["body"]) and not is_top(task["body"])],
        key=created,
        reverse=True,
    )
    later = [task for task in rest if not is_top(task["body"]) and not is_high(task["body"])]
    return tests + tops + highs + later


def is_continuation_note(body):
    """Status notes are not tasks. Numbered steps or "Report DONE" are real work."""
    lines = [line.strip() for line in (body or "").splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    raw = body or ""
    blob = " ".join(lines[1:]).lower()
    if "report done" in blob or "done when" in blob or "prove" in blob:
        return False
    if re.search(r"(?:^|\n)\s*\d+\.\s", raw):
        return False
    if "stays open" in blob or "repost" in blob:
        return False
    if "accepted and closed" in blob:
        return True
    informational = (
        "informational" in blob
        or "no reply needed" in blob
        or "no further action" in blob
    )
    if not informational:
        return False
    if "stays open" in blob or "repost" in blob:
        return False
    return True


def is_no_reply(body):
    """The city said not to answer. Skip it with no canned post."""
    return "no reply needed" in (body or "").lower()


def is_top(body):
    return "priority:top" in (body or "")[:800].lower()


def is_high(body):
    return "priority:high" in (body or "")[:800].lower()


QUEUE = ROOT / "queue.json"


def load_queue():
    data = load_json(QUEUE, {})
    items = data.get("open") if isinstance(data, dict) else None
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def save_queue(items):
    save_json(QUEUE, {"updated": now_iso(), "open": items})


def task_priority(task):
    if str(task.get("id") or "").startswith("b9test"):
        return "test"
    body = task.get("body") or ""
    if is_top(body):
        return "top"
    if is_high(body):
        return "high"
    return "normal"


def sync_queue(tasks, state):
    """Persist the open queue. Newest TOP/HIGH stay in front. seen is first-seen."""
    previous = {item.get("id"): item for item in load_queue()}
    acked_ids = set(state.get("acked_ids") or [])
    now = now_iso()
    items = []
    for task in tasks:
        if is_continuation_note(task.get("body") or ""):
            continue
        old = previous.get(task["id"]) or {}
        items.append(
            {
                "id": task["id"],
                "priority": task_priority(task),
                "status": "open",
                "acked": task["id"] in acked_ids or bool(old.get("acked")),
                "seen": old.get("seen") or now,
                "created": task.get("created") or "",
            }
        )
    save_queue(items)
    return items


def ensure_ack(state, task):
    """Post ACK once. True when the task is acked or already was."""
    marker = f"[id:ga{task['id']}]"
    acked = state.setdefault("acked_ids", [])
    if task["id"] in acked or already(marker):
        if task["id"] not in acked:
            acked.append(task["id"])
        return True
    full = (
        f"[from:grok-build] [id:ga{task['id']}] [re:{task['id']}]\n"
        f"ACK\nPicking up {task['id']}.\n"
    )
    if not post_raw(full):
        print("ack failed", task["id"])
        return False
    acked.append(task["id"])
    print("ack", task["id"])
    return True


def state_lock():
    import fcntl
    from contextlib import contextmanager

    @contextmanager
    def locked():
        path = ROOT / "state.lock"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            yield

    return locked()


def same_body(bodies, marker, label):
    """True only when marker and label share one comment. A label in a different comment does not count."""
    needle = f"\n{label}\n"
    return any(marker in body and needle in f"\n{body}\n" for body in bodies)


def comment_bodies():
    """One string per Channel comment. Never join them into a single blob."""
    try:
        proc = subprocess.run(
            [
                "gh",
                "api",
                "--paginate",
                "repos/brandocalricia/agent-city-comms/issues/1/comments",
            ],
            capture_output=True,
            text=True,
            timeout=40,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []
    if proc.returncode != 0 or not proc.stdout.strip():
        return []
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [c.get("body") or "" for c in data if isinstance(c, dict)]


def already(marker):
    return any(marker in body for body in comment_bodies())


def already_kind(marker, label):
    """True when one comment with this id has label as its own line."""
    return same_body(comment_bodies(), marker, label)


def extra_facts(task_id):
    """Cloudflare fact only for the city-live reports that asked for it."""
    if task_id not in {"b9citylive1", "b9citylive1b", "b9citylive1bre", "b9citylive1c"}:
        return []
    return [
        "Also put this measured fact in the report, in your own words:",
        "Cloudflare chat to llama-3.3-70b-instruct-fp8-fast returned HTTP 200. The row stays at priority 1 only while that chat stays green. A later 401 or 429 demotes it to last.",
        "Health checks use the user verify endpoint. An account-scoped 401 error 1000 on a user key is not a failed key.",
        "A connection-test HTTP 200 is not a chat probe.",
        "Do not put citation markup or angle-bracket tags in the result.",
        "",
    ]


def write_prompt(task):
    PROMPTS.mkdir(parents=True, exist_ok=True)
    path = PROMPTS / f"{task['id']}.md"
    body = task["body"]
    if len(body) > 8000:
        body = body[:8000] + "\n…"
    path.write_text(
        "\n".join(
            [
                f"You are the single-task headless worker for Agent City task {task['id']}.",
                "You are not the orchestrator. Ignore the standing Channel loop.",
                "Do this task only. Do not use tools unless the task needs a file change.",
                "Do not post to the Channel. Do not run gh. You have no Channel token.",
                "Do not spawn agents. Do not start LaunchAgents.",
                "Do not kill processes. Do not bootout LaunchAgents. Do not change Wi-Fi.",
                "Do not edit ~/.agent-city. Print a short result and stop.",
                "Do not print secrets, keys, webhook files, or home-directory paths.",
                "No spending, no paid keys, never put SuperGrok or grok.com OAuth in OmniRoute.",
                "Do not delete the owner's data. Back up a config file before you change it.",
                "Do not force-push. Do not push main.",
                "Do not spawn subagents. This worker stays on the OmniRoute model already selected.",
                "",
                *(
                    [
                        "This same step already refused twice. Split it.",
                        "Do only piece A. Print that piece's evidence and stop.",
                        "Piece A: a real terminal capture of the live dashboard, with the chat text and the column width.",
                        "Piece B, later: session A sends a message and session B ACKs, with both timestamps.",
                        "Piece C, later: the auto-spawn log line.",
                        "Do not use cohere/command-a-03-2025. Do not post to the Channel.",
                        "",
                    ]
                    if task.get("split")
                    else []
                ),
                f"Task {task['id']}:",
                body,
                "",
                *extra_facts(task["id"]),
            ]
        )
    )
    return path


CANNED_REPORTS = {"headless run finished", "headless exit 0 with no result"}
REFUSAL_BITS = (
    "i'm sorry",
    "i am sorry",
    "unable to assist",
    "don't have the capability",
    "do not have the capability",
    "cannot assist",
    "can't assist",
)
EVIDENCE_BITS = (
    ".sh",
    ".py",
    ".toml",
    ".json",
    "http",
    "latency",
    "passed",
    "failed",
    "changed",
    "tested",
    "backup",
    "columns",
    "priority",
)


PLAN_BITS = (
    "i will",
    "i'll",
    "i'm unable",
    "i am unable",
    "follow these steps",
    "to address task",
    "assuming",
    "replace placeholder",
)


def is_refusal(text):
    low = (text or "").lower()
    return any(bit in low for bit in REFUSAL_BITS)


def is_plan(text):
    """Future tense is a promise, not a result. Reject it even when it names a file."""
    low = (text or "").lower()
    return any(bit in low for bit in PLAN_BITS)


def has_evidence(text):
    """A report names a result. A restatement of the rules does not."""
    low = (text or "").lower()
    return any(bit in low for bit in EVIDENCE_BITS)


PLACEHOLDER_BITS = (
    "[insert",
    "[x]",
    "[$y]",
    "[n]",
    "e.g., https://github.com/",
)


def has_placeholder(text):
    """An unfilled template is not a reading."""
    low = (text or "").lower()
    return any(bit in low for bit in PLACEHOLDER_BITS)


def usable_report(text):
    """A real summary. Empty, canned, refusal, plan, or no-evidence output is not a report."""
    cleaned = (text or "").strip()
    if not cleaned or cleaned.lower() in CANNED_REPORTS:
        return ""
    if is_refusal(cleaned) or is_plan(cleaned) or has_placeholder(cleaned) or not has_evidence(cleaned):
        return ""
    sample = cleaned[:800]
    if "<|" in sample or "reserved_token" in sample:
        return ""
    weird = sum(1 for ch in sample if ord(ch) > 127)
    if weird / max(len(sample), 1) > 0.08:
        return ""
    words = [word for word in sample.split() if word.isascii() and any(ch.isalpha() for ch in word)]
    if len(words) < 8:
        return ""
    return cleaned[:1800]


def result_text(chunk):
    """Last JSON object in a headless log that carries a usable report."""
    decoder = json.JSONDecoder()
    index = len(chunk)
    while index > 0:
        index = chunk.rfind("{", 0, index)
        if index < 0:
            break
        try:
            data, _ = decoder.raw_decode(chunk[index:])
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        report = usable_report(str(data.get("text") or data.get("result") or ""))
        if report:
            return report
    return ""


LAST_LANE = ""


def format_lane(chunk, task_id):
    """Model, lane, and last log line from one headless chunk. No secrets."""
    model = "unknown"
    last_line = ""
    decoder = json.JSONDecoder()
    index = 0
    while index < len(chunk):
        start = chunk.find("{", index)
        if start < 0:
            break
        try:
            data, end = decoder.raw_decode(chunk[start:])
        except Exception:
            index = start + 1
            continue
        index = start + max(end, 1)
        if not isinstance(data, dict):
            continue
        usage = data.get("modelUsage")
        if isinstance(usage, dict) and usage:
            model = str(next(iter(usage)))
        text = str(data.get("text") or data.get("result") or "").strip()
        if text:
            last_line = text.splitlines()[-1].strip()[:200]
    if not last_line:
        lines = [
            line.strip()
            for line in chunk.splitlines()
            if line.strip() and not line.startswith("---") and line.strip() not in ("{", "}")
        ]
        last_line = lines[-1][:200] if lines else "(empty)"
    if model.startswith("grok-"):
        lane = "main " + model
    else:
        lanes = [line for line in recent_lane_lines().splitlines() if line.strip()]
        lane = lanes[-1] if lanes else "omniroute " + model
    return (
        f"model: {model}\n"
        f"lane: {lane}\n"
        f"step: {task_id}\n"
        f"log: {redact_log(last_line)}"
    )


def worker_launch(task, allow_grok_retry=True):
    """The real argv, env, and prompt for one worker. Does not start it."""
    prompt = write_prompt(task)
    prompt_text = prompt.read_text()
    test = str(task["id"]).startswith("b9test")
    turns = "2" if test else "48"
    deny = "Agent,task"
    if test:
        deny = "Agent,task,run_terminal_cmd,web_search,web_fetch,search_replace,todo_write,grep,list_dir,read_file"
    cwd = str(Path.home() / "grok-sandbox") if test else str(Path.home() / "code" / "agent-city")
    if not Path(cwd).is_dir():
        cwd = str(Path.home())
    cmd = ["caffeinate", "-i", str(GROK)]
    # A free lane often refuses and posts that as DONE.
    # The one retry uses the main Grok model, with no --model flag.
    if allow_grok_retry:
        cmd.extend(["--model", "omniroute"])
    cmd.extend(
        [
            "--prompt-file",
            str(prompt),
            "--always-approve",
            "--output-format",
            "json",
            "--cwd",
            cwd,
            "--max-turns",
            turns,
            "--no-subagents",
            "--disallowed-tools",
            deny,
        ]
    )
    if test:
        cmd.append("--disable-web-search")
    env = worker_env(os.environ)
    env["AGENT_CITY_HEADLESS"] = "1"
    return cmd, env, prompt_text


def run_grok(task, allow_grok_retry=True):
    global LAST_LANE
    # cohere/command-a-03-2025 already refused this family. Start on the other lane.
    if allow_grok_retry and str(task["id"]).startswith("b9mods"):
        print("skip-refused-lane", task["id"])
        return run_grok(task, allow_grok_retry=False)
    cmd, env, _prompt_text = worker_launch(task, allow_grok_retry)
    log_path = ROOT / "logs" / "task.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    # A line of its own. The reader must not fall back to another task's output.
    marker_line = f"--- task {task['id']} {now_iso()} ---"
    with log_path.open("a") as handle:
        handle.write(f"\n{marker_line}\n")
        handle.flush()
        env = worker_env(os.environ)
        env["AGENT_CITY_HEADLESS"] = "1"
        proc = subprocess.Popen(
            cmd,
            stdout=handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=env,
        )
        TASK_PID.write_text(str(proc.pid) + "\n")
        try:
            code = proc.wait(timeout=720)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
            # A hung free lane used to die here, so the main-model retry never ran.
            if allow_grok_retry:
                print("retry-on-grok", task["id"])
                return run_grok(task, allow_grok_retry=False)
            return False, "timed out after 12 minutes"
    TASK_PID.unlink(missing_ok=True)
    raw = log_path.read_text(errors="replace")
    marker = f"--- task {task['id']} "
    start = raw.rfind(marker)
    chunk = raw[start:] if start >= 0 else ""
    text = result_text(chunk)
    LAST_LANE = format_lane(chunk, task["id"])
    if code != 0:
        err = headless_error(chunk)
        # grok exits 1 when it hits the turn cap, after it has already written a reply.
        if text and "max turns reached" in chunk:
            return True, text[:1800]
        if allow_grok_retry:
            print("retry-on-grok", task["id"])
            return run_grok(task, allow_grok_retry=False)
        return False, err or f"headless exit {code}"
    if not text.strip():
        if allow_grok_retry:
            print("retry-on-grok", task["id"])
            return run_grok(task, allow_grok_retry=False)
        return False, "refusal with no evidence\n" + LAST_LANE
    return True, text.strip()[:1800]


def worker_env(base):
    """The worker process does not receive a Channel token."""
    env = dict(base)
    for key in list(env):
        upper = str(key).upper()
        if upper in CHANNEL_TOKEN_KEYS or ("GITHUB" in upper and "TOKEN" in upper):
            env.pop(key, None)
    return env


def post_worker_done(task_id, report, done_id):
    """Post one DONE. A draft that fails the gate never reaches the network."""
    return gate_post_worker_done(task_id, report, post_raw, LAST_LANE, done_id)


def headless_error(chunk):
    """The grok error message, including a multi-line JSON body."""
    decoder = json.JSONDecoder()
    message = ""
    index = len(chunk)
    while index > 0:
        index = chunk.rfind("{", 0, index)
        if index < 0:
            break
        try:
            data, _end = decoder.raw_decode(chunk[index:])
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        if data.get("type") == "error" or "promptUsage" in data:
            message = str(data.get("message") or "")
            break
    if message.startswith("Internal error:"):
        inner = message.split(":", 1)[1].strip()
        try:
            payload = json.loads(inner)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict) and payload.get("message"):
            message = str(payload["message"])
        elif isinstance(payload, str):
            message = payload
    if not message:
        for line in chunk.splitlines():
            if line.startswith("Error:"):
                message = line
                break
    lanes = recent_lane_lines()
    report = redact_log(message)
    if lanes:
        report = (report + "\nlanes:\n" + lanes).strip()
    return report[:1800]


def recent_lane_lines():
    """Provider and status for the last few minutes. No request bodies."""
    root = Path.home() / ".omniroute" / "call_logs"
    if not root.is_dir():
        return ""
    cutoff = time.time() - 180
    rows = []
    for path in root.glob("*/*.json"):
        try:
            if path.stat().st_mtime < cutoff:
                continue
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        summary = data.get("summary") if isinstance(data, dict) else None
        if not isinstance(summary, dict):
            continue
        provider = str(summary.get("provider") or "")
        model = str(summary.get("model") or "")
        status = summary.get("status")
        if not provider or provider == "auto" or not model or model.startswith("auto/"):
            continue
        rows.append((summary.get("timestamp") or "", f"{provider}/{model} HTTP {status}"))
    rows.sort()
    seen = []
    for _stamp, line in rows:
        if line not in seen:
            seen.append(line)
    return "\n".join(seen[:24])


def redact_log(text):
    cleaned = (text or "").replace(str(Path.home()), "~")
    cleaned = re.sub(r"\b(?:sk|ghp|github_pat)[_-][A-Za-z0-9_\-]{8,}\b", "[redacted]", cleaned)
    cleaned = re.sub(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*\S+", r"\1=[redacted]", cleaned)
    return cleaned


def log_tail(path, count=20):
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return ""
    return redact_log("\n".join(lines[-count:]))


def strike_decision(fail_count, error, log_tail_text, now):
    """Refusal fails over at once. See done_gate.strike_decision."""
    decision = gate_strike(
        fail_count,
        redact_log(error or ""),
        redact_log(log_tail_text or ""),
        now,
    )
    decision["blocked"] = redact_log(decision.get("blocked") or "")
    return decision


def remember(state, task, done_ok):
    handled = state.setdefault("handled_ids", [])
    if task["id"] not in handled:
        handled.append(task["id"])
    state["reopen_ids"] = [
        item for item in (state.get("reopen_ids") or []) if item != task["id"]
    ]
    comment_id = task.get("comment_id") or 0
    if isinstance(comment_id, int) and comment_id > int(state.get("last_handled_comment_id") or 0):
        state["last_handled_comment_id"] = comment_id
    state["current_task"] = ""
    state["last_change_epoch"] = int(time.time())
    claimed = state.setdefault("claimed", {})
    claimed.pop(task["id"], None)
    cursor = load_json(CURSOR, {})
    key = "finished_ids" if done_ok else "finished_ids"
    ids = cursor.setdefault(key, [])
    if task["id"] not in ids:
        ids.append(task["id"])
    open_ids = [item for item in cursor.get("open_ids") or [] if item != task["id"]]
    cursor["open_ids"] = open_ids
    save_json(CURSOR, cursor)
    save_json(STATE, state)


def maybe_heartbeat(state, changed):
    last = int(state.get("last_heartbeat_epoch") or 0)
    elapsed = int(time.time()) - last
    due = (changed and elapsed >= 3600) or elapsed >= 21600
    if not due:
        return
    stamp = time.strftime("%Y%m%d%H")
    marker = f"[id:ghb{stamp}]"
    if already(marker):
        state["last_heartbeat_epoch"] = int(time.time())
        save_json(STATE, state)
        return
    body = f"[from:grok-build] {marker} [re:b9auto2]\nHEARTBEAT runner alive\n"
    if post_raw(body):
        state["last_heartbeat_epoch"] = int(time.time())
        save_json(STATE, state)


def is_work_task(body):
    """Numbered work, a proof, or DONE-when criteria cannot be closed as a note."""
    raw = body or ""
    low = raw.lower()
    if "done when" in low or "report done" in low or "prove" in low:
        return True
    return re.search(r"(?:^|\n)\s*\d+\.\s", raw) is not None


def close_note(state, task):
    if is_work_task(task.get("body") or ""):
        print("keep-open", task["id"])
        return True
    state["current_task"] = task["id"]
    save_json(STATE, state)
    ack_marker = f"[id:ga{task['id']}]"
    if task["id"] not in (state.get("acked_ids") or []) and not already(ack_marker):
        full = (
            f"[from:grok-build] [id:ga{task['id']}] [re:{task['id']}]\n"
            f"ACK\nContinuation note {task['id']}. No separate work.\n"
        )
        if not post_raw(full):
            print("ack failed")
            return False
        time.sleep(11)
    acked = state.setdefault("acked_ids", [])
    if task["id"] not in acked:
        acked.append(task["id"])
    save_json(STATE, state)
    remember(state, task, True)
    print("note", task["id"])
    return True


def id_mentioned(body, task_id):
    """Match the whole id. b9mods1 must not match b9mods1b or gdb9mods1."""
    return re.search(
        rf"(?<![A-Za-z0-9]){re.escape(str(task_id))}(?![A-Za-z0-9])",
        body or "",
        re.I,
    ) is not None


def later_note_retires(task_id, rows):
    """A later city note closed this exact id. Mentioning it is not a close."""
    short = str(task_id)
    low_id = short.lower()
    for row in rows:
        body = row.get("body") or ""
        first = body.lstrip().splitlines()[0] if body.strip() else ""
        if "grok-bot" not in first.lower():
            continue
        if not id_mentioned(body, short):
            continue
        low = body.lower()
        if f"{low_id} stays open" in low or f"{low_id} stay open" in low:
            continue
        own = parse_task(body)
        own_id = own[1] if own else ""
        explicit = (
            f"stop retrying {low_id}" in low
            or f"{low_id}: closed as superseded" in low
            or f"{low_id} closed as superseded" in low
        )
        if explicit:
            return True
        if own_id == short and "no reply needed" in low:
            return True
    return False


def missing_task_evidence(task_id, report):
    """Reject a draft that borrows another task's fact or skips this task's proof."""
    text = report or ""
    low = text.lower()
    short = str(task_id)
    if short.startswith("b9mods") and "cloudflare chat to" in low:
        return "foreign cloudflare fact"
    if short.startswith("b9mods"):
        missing = []
        if "github.com/" not in low:
            missing.append("pull request url")
        if "column" not in low:
            missing.append("column width")
        if len(re.findall(r"\d{4}-\d{2}-\d{2}t", low)) < 2:
            missing.append("two timestamps")
        if "spawn" not in low:
            missing.append("auto-spawn line")
        if missing:
            return "missing " + ", ".join(missing)
    if short.startswith("b9citylive") and "~" in text:
        return "estimated number"
    return ""


def fresh_done_id(task_id, bodies):
    """A second post for the same task gets a new id. Never reuse gd{id}."""
    base = f"gd{task_id}"
    used = set()
    for body in bodies:
        used.update(re.findall(r"\[id:(gd[^\]\s]+)\]", body or ""))
    if base not in used:
        return base
    number = 2
    while f"{base}-{number}" in used:
        number += 1
    return f"{base}-{number}"


def real_done(marker):
    """True when this id has a DONE whose text is a real report."""
    for body in comment_bodies():
        if marker not in body or "\nDONE\n" not in f"\n{body}\n":
            continue
        report = body.split("\nDONE\n", 1)[1].strip()
        low = report.lower()
        if "continuation note" in low and "no separate work" in low:
            continue
        if usable_report(report):
            return True
    return False


def work(state):
    refused = state.setdefault("retry_after", {})
    if refused.pop("b9mods1bre1", None) is not None:
        print("cleared refusal backoff b9mods1bre1")
    try:
        rows = fetch_comments()
    except RuntimeError as exc:
        print(f"fetch {exc}")
        return 2
    flush_outbox()
    tasks = pending_tasks(rows, state)
    for task in list(tasks):
        if is_no_reply(task.get("body") or ""):
            remember(state, task, True)
            print("quiet", task["id"])
    tasks = [task for task in tasks if not is_no_reply(task.get("body") or "")]
    notes = [task for task in tasks if is_continuation_note(task["body"])]
    tasks = [task for task in tasks if not is_continuation_note(task["body"])]
    sync_queue(tasks, state)
    write_status(state, len(tasks) + len(notes))
    for task in notes:
        if not close_note(state, task):
            return 1
    if not tasks:
        state["current_task"] = "idle"
        state["next_task"] = ""
        save_json(STATE, state)
        write_status(state, 0)
        maybe_heartbeat(state, False)
        print("idle")
        return 0
    task = tasks[0]
    if later_note_retires(task["id"], rows):
        state.setdefault("retry_after", {}).pop(task["id"], None)
        print("retired", task["id"])
        if not close_note(state, task):
            return 1
        return 0
    state["current_task"] = task["id"]
    state["next_task"] = tasks[1]["id"] if len(tasks) > 1 else ""
    save_json(STATE, state)
    write_status(state, len(tasks))
    if not ensure_ack(state, task):
        return 1
    save_json(STATE, state)
    sync_queue(tasks, state)
    if task["id"] in set(state.get("split_ids") or []):
        task["split"] = True
    ok, detail = run_grok(task)
    merge_acked(state)
    bodies = [row.get("body") or "" for row in rows]
    done_id = fresh_done_id(task["id"], bodies)
    done_marker = f"[id:{done_id}]"
    text = detail.replace(str(Path.home()), "~")
    if ok:
        report = usable_report(text)
        gap = missing_task_evidence(task["id"], report or text)
        if report and not approve_worker_done(task["id"], report):
            gap = gap or "worker draft did not pass the gate"
            report = ""
        if report and not command_a_may_post(LAST_LANE, report):
            gap = gap or "command-a-03-2025 draft has no SHA and no PASS line"
            report = ""
        if not report or gap:
            ok = False
            text = "worker draft rejected: " + (gap or "plan or no evidence")
            if LAST_LANE and "model:" not in text.lower():
                text = text + "\n" + LAST_LANE
        elif later_note_retires(task["id"], rows):
            remember(state, task, True)
            print("retired", task["id"])
            return 0
        else:
            try:
                fresh_rows = fetch_comments()
            except RuntimeError:
                fresh_rows = rows
            if newer_open_rejection(task["id"], fresh_rows):
                print("stale-rejection", task["id"])
                state["current_task"] = ""
                save_json(STATE, state)
                return 0
            if not real_done(done_marker):
                if not post_worker_done(task["id"], report, done_id):
                    print("gate-blocked", task["id"])
                    ok = False
                    text = "worker draft rejected: gate"
                else:
                    time.sleep(11)
        if ok:
            remember(state, task, True)
            state["next_task"] = tasks[1]["id"] if len(tasks) > 1 else ""
            write_status(state, max(0, len(tasks) - 1))
            maybe_heartbeat(state, True)
            print("done", task["id"])
            return 0
    fails = state.setdefault("fail_counts", {})
    decision = strike_decision(
        fails.get(task["id"]) or 0,
        text,
        "",
        int(time.time()),
    )
    fails[task["id"]] = decision["fail_count"]
    if decision.get("split"):
        splits = state.setdefault("split_ids", [])
        if task["id"] not in splits:
            splits.append(task["id"])
    if decision["action"] == "backoff":
        state.setdefault("retry_after", {})[task["id"]] = decision["retry_after"]
        blocked = decision.get("blocked") or ""
        if decision.get("post_blocked") and blocked_has_lane_detail(blocked):
            stamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
            marker = f"[id:gs{task['id']}{stamp}]"
            if not already(marker):
                full = (
                    f"[from:grok-build] {marker} [re:{task['id']}]\n"
                    f"BLOCKED\n{blocked}\nRetrying after 10 minutes.\n"
                )
                if not post_raw(full):
                    print("done post failed")
                    return 1
                time.sleep(11)
        else:
            print("blocked-suppressed", task["id"])
        print("backoff", task["id"])
    else:
        print("retry", task["id"])
    save_json(STATE, state)
    write_status(state, len(tasks))
    return 0


def post_raw(body, queue=True):
    """Post an already-headed comment. Queue it locally if the network drops."""
    gh = subprocess.run(
        [
            "gh",
            "api",
            "--method",
            "POST",
            "repos/brandocalricia/agent-city-comms/issues/1/comments",
            "--input",
            "-",
        ],
        input=json.dumps({"body": body}),
        capture_output=True,
        text=True,
        timeout=40,
    )
    if gh.returncode == 0:
        print("posted")
        return True
    err = ((gh.stderr or "") + (gh.stdout or "")).lower()
    if any(token in err for token in ("could not resolve", "timed out", "connection", "network")):
        if queue:
            queued = ROOT / "outbox.jsonl"
            with queued.open("a") as handle:
                handle.write(json.dumps({"body": body, "created": now_iso()}) + "\n")
            print("queued")
            return True
        return False
    sys.stderr.write((gh.stderr or "")[:300])
    return False


def flush_outbox():
    path = ROOT / "outbox.jsonl"
    if not path.exists():
        return
    rows = []
    for line in path.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    kept = []
    for index, row in enumerate(rows):
        body = row.get("body") or ""
        marker = ""
        start = body.find("[id:")
        end = body.find("]", start)
        if start >= 0 and end > start:
            marker = body[start : end + 1]
        if marker and already(marker):
            continue
        if post_raw(body, queue=False):
            if index != len(rows) - 1:
                time.sleep(11)
            continue
        kept.extend(rows[index:])
        break
    if kept:
        path.write_text("".join(json.dumps(row) + "\n" for row in kept))
    else:
        path.unlink(missing_ok=True)


def ack_pass(state):
    """ACK every new task and refresh the queue. Does not run a task."""
    try:
        rows = fetch_comments()
    except RuntimeError as exc:
        print(f"fetch {exc}")
        return 2
    tasks = pending_tasks(rows, state)
    for task in tasks:
        if is_no_reply(task.get("body") or ""):
            remember(state, task, True)
            print("quiet", task["id"])
    tasks = [
        task
        for task in tasks
        if not is_no_reply(task.get("body") or "")
        and not is_continuation_note(task.get("body") or "")
    ]
    posted = False
    for task in tasks:
        if task["id"] in (state.get("acked_ids") or []):
            continue
        if not ensure_ack(state, task):
            break
        posted = True
        time.sleep(11)
    if posted:
        time.sleep(0)
    sync_queue(tasks, state)
    state["next_task"] = tasks[0]["id"] if tasks else ""
    if tasks and not state.get("current_task"):
        state["current_task"] = "idle"
    save_json(STATE, state)
    write_status(state, len(tasks))
    print("ack-pass", len(tasks))
    return 0


def merge_acked(state):
    """Keep ACKs a parallel poll recorded while a task was running."""
    fresh = load_state()
    acked = state.setdefault("acked_ids", [])
    for item in fresh.get("acked_ids") or []:
        if item not in acked:
            acked.append(item)
    reopen = state.setdefault("reopen_ids", [])
    for item in fresh.get("reopen_ids") or []:
        if item not in reopen:
            reopen.append(item)
    handled = state.setdefault("handled_ids", [])
    for item in fresh.get("handled_ids") or []:
        if item not in handled and item not in reopen:
            handled.append(item)
    for item in list(reopen):
        if item in handled:
            handled.remove(item)


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "logs").mkdir(parents=True, exist_ok=True)
    if "--ack-only" in sys.argv:
        with state_lock():
            return ack_pass(load_state())
    code = work(load_state())
    write_status(load_state(), len(load_queue()))
    return code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"step error {type(exc).__name__}")
        sys.exit(1)
