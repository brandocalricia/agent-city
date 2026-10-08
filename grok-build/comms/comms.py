#!/usr/bin/env python3
"""Agent City <-> Grok Build message link (comms.py). Python 3.8+, stdlib only, macOS and Linux.

The thread is the open pull request titled "Channel" in the owner's private repo
brandocalricia/agent-city-comms (found by title, never hard-coded by number). setup/watch/send
create it if missing (branch `channel` + `channel/README.md`, then `gh pr create`) and post a first
grok-build hello. Every message is one PR conversation comment whose first line is a header, then
the body:
    [from:grok-bot|grok-build] [id:<short id>] [re:<id or ->]
Grok Bot comments MUST start with [from:grok-bot] so Agent City's PR-comment wake can exit at once.

  comms.py watch     resolve the Channel PR (create + hello if missing), poll every 10 s (ETag /
                     If-None-Match) and print each new grok-bot message as ONE line. Single instance
                     (lock), cursor in comms-state.json, backs off when offline.
  comms.py send [--re ID] TEXT   (TEXT "-" reads stdin)
                     resolve Channel, post the comment via gh; optionally POST to the inbox webhook
                     when configured. Max 1 send per 10 s, 60 per hour. Thread-only (no webhook) is
                     the default and is enough: Agent City wakes on PR comments.
  comms.py setup [--clipboard | --url U --key K | paste text]
                     default (no URL/key): thread-only — check gh auth, find/create Channel PR +
                     hello, write bot-webhook.env with AGENT_CITY_WEBHOOK=off, print next step.
                     With URL/key (or paste/--clipboard): also store the optional webhook (chmod 600,
                     never echoed).
  comms.py status    gh, Channel PR, webhook, watcher, cursor, send budget. Never prints secrets.

Needs the GitHub CLI signed in (`gh auth login`); the watcher reads its token with `gh auth token`.
"""
import argparse, base64, fcntl, json, os, re, secrets, shutil, stat, subprocess, sys, time
import urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

REPO = os.environ.get("AGENT_CITY_COMMS_REPO", "brandocalricia/agent-city-comms")
API = os.environ.get("AGENT_CITY_COMMS_API", "https://api.github.com").rstrip("/")
CHANNEL_TITLE = os.environ.get("AGENT_CITY_COMMS_TITLE", "Channel")
CHANNEL_BRANCH = os.environ.get("AGENT_CITY_COMMS_BRANCH", "channel")
CHANNEL_FILE = "channel/README.md"
CHANNEL_FILE_BODY = "Agent City <-> Grok Build message channel (PR conversation).\n"
HELLO_TEXT = "Link is up from Grok Build. Reply with ping to test."
ME, PEER = "grok-build", "grok-bot"
TAG = "[agent-city]"
INTERVAL = 10.0          # seconds between polls
MAX_BACKOFF = 300.0      # offline / server errors: 20, 40, 80, 160, 300 s
FIRST_RUN_WINDOW = 24    # hours of history a brand-new watcher looks back
MAX_PER_POLL = 10        # more new messages than this in one poll: show the newest 10 and say how many were skipped
MAX_LINE = 1200          # characters of body on the notification line; full text always in inbox/<id>.md
MAX_TEXT = 6000          # send refuses longer messages
SEND_GAP, SEND_HOUR = 10, 60
HEADER_RE = re.compile(r"^\s*\[from:\s*(grok-bot|grok-build)\s*\]\s*\[id:\s*([A-Za-z0-9_.-]{1,40})\s*\]"
                       r"\s*\[re:\s*([A-Za-z0-9_.-]{1,40}|-)\s*\]\s*$", re.I)
ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,40}$")
DEFAULT_HEADER = "Authorization: Bearer {key}"


def home():
    g = os.environ.get("GROK_HOME") or os.path.join(os.path.expanduser("~"), ".grok")
    return os.path.join(g, "agent-city")


def path(name):
    return os.path.join(home(), name)


def out(line):
    """Every line becomes a monitor notification, so print deliberately and flush at once."""
    try:
        sys.stdout.write(line + "\n"); sys.stdout.flush()
    except UnicodeEncodeError:
        sys.stdout.write(line.encode("ascii", "replace").decode() + "\n"); sys.stdout.flush()


def now_utc():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def write_atomic(p, text, mode=0o600):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = "%s.tmp.%d" % (p, os.getpid())
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(tmp, mode)
    os.replace(tmp, p)


# ---------------------------------------------------------------- protocol

def parse_message(body):
    """Comment body -> {from, id, re, text}, or None when the first line is not a valid header."""
    if not isinstance(body, str):
        return None
    body = body.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    first, _, rest = body.partition("\n")
    m = HEADER_RE.match(first)
    if not m:
        return None
    return {"from": m.group(1).lower(), "id": m.group(2), "re": m.group(3), "text": rest.strip()}


def make_body(mid, re_id, text):
    return "[from:%s] [id:%s] [re:%s]\n%s" % (ME, mid, re_id or "-", text)


def save_inbox(msg):
    """Full text with formatting intact, for messages too long or too structured for one line. Keeps the last 50."""
    d = path("inbox")
    p = os.path.join(d, msg["id"] + ".md")
    try:
        write_atomic(p, "[from:%s] [id:%s] [re:%s]\n%s\n" % (msg["from"], msg["id"], msg["re"], msg["text"]))
        files = sorted((os.path.getmtime(os.path.join(d, f)), f) for f in os.listdir(d) if f.endswith(".md"))
        for _, f in files[:-50]:
            os.remove(os.path.join(d, f))
    except OSError:
        return None
    return p


def format_line(msg):
    lines = [l.strip() for l in msg["text"].splitlines() if l.strip()]
    text = " \u23ce ".join(lines) or "(empty)"
    line = "%s message from Agent City id:%s re:%s | " % (TAG, msg["id"], msg["re"])
    full = None
    if len(text) > MAX_LINE or len(lines) > 1:
        full = save_inbox(msg)
    if len(text) > MAX_LINE:
        text = text[:MAX_LINE] + " \u2026"
    return line + text + (" [full text: %s]" % full if full else "")


def process(state, comments, issue=None):
    """New comments -> notification lines. Dedupes by comment id (a cursor; edits of old comments come back
    through `since` and are ignored) and by message id (a message re-posted after a retry); ignores our own
    messages and comments without a header. Mutates state; returns the lines to print."""
    last = int(state.get("last_id") or 0)
    seen = list(state.get("seen_ids") or [])
    fresh = []
    for c in sorted((c for c in comments if isinstance(c, dict) and isinstance(c.get("id"), int)), key=lambda c: c["id"]):
        if c["id"] <= last:
            continue
        last = c["id"]
        if isinstance(c.get("created_at"), str):
            state["since"] = c["created_at"]
        msg = parse_message(c.get("body"))
        if not msg or msg["from"] != PEER or msg["id"] in seen:
            continue
        seen.append(msg["id"])
        fresh.append(msg)
    state["last_id"] = last
    state["seen_ids"] = seen[-200:]
    lines = []
    if len(fresh) > MAX_PER_POLL:
        issue_n = issue if issue is not None else state.get("channel_issue") or 0
        lines.append("%s %d older Agent City messages skipped (read them in https://github.com/%s/pull/%d)"
                     % (TAG, len(fresh) - MAX_PER_POLL, REPO, int(issue_n or 0)))
        fresh = fresh[-MAX_PER_POLL:]
    return lines + [format_line(m) for m in fresh]


# ---------------------------------------------------------------- state

def load_state():
    p = path("comms-state.json")
    try:
        with open(p, encoding="utf-8") as f:
            s = json.load(f)
        if isinstance(s, dict) and isinstance(s.get("last_id", 0), int):
            return s
        raise ValueError("bad shape")
    except FileNotFoundError:
        pass
    except (ValueError, OSError):
        try:
            os.replace(p, p + ".bad")   # keep it for inspection, start fresh
        except OSError:
            pass
    return {"last_id": 0, "since": iso(now_utc() - timedelta(hours=FIRST_RUN_WINDOW)), "seen_ids": []}


def save_state(state):
    write_atomic(path("comms-state.json"), json.dumps(state, indent=1, sort_keys=True) + "\n")


# ---------------------------------------------------------------- gh / GitHub API

class AuthError(Exception):
    pass


class RateLimited(Exception):
    def __init__(self, wait):
        Exception.__init__(self, "rate limited")
        self.wait = wait


class Transient(Exception):
    pass


GH_HELP = ("GitHub CLI `gh` is not installed. On the Mac: `brew install gh`, then `gh auth login` "
           "(GitHub.com, HTTPS, sign in as the owner).")
AUTH_HELP = "gh is not signed in. Run `gh auth login` (GitHub.com, HTTPS) as the owner, then try again."


def gh_path():
    return shutil.which("gh")


def gh_token():
    """Token from `gh auth token` (never printed or logged). None when gh is missing or signed out."""
    if not gh_path():
        return None
    try:
        r = subprocess.run(["gh", "auth", "token", "--hostname", "github.com"], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return None
    tok = r.stdout.strip()
    return tok if r.returncode == 0 and tok and "\n" not in tok else None


def token_allowed(api):
    host = urllib.parse.urlparse(api).hostname or ""
    return api.startswith("https://api.github.com") or host in ("127.0.0.1", "localhost")


def _gh_api(args, input_text=None, timeout=30):
    """Run `gh api ...`. Returns (ok, stdout_or_err). Never logs tokens or bodies."""
    try:
        r = subprocess.run(["gh", "api"] + list(args), input=input_text, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "gh timed out"
    except OSError as e:
        return False, "gh failed to start (%s)" % type(e).__name__
    if r.returncode != 0:
        err = (r.stderr.strip().splitlines() or ["gh exited %d" % r.returncode])[-1]
        return False, err[:200]
    return True, r.stdout


def _title_match(title):
    return (title or "").strip().casefold() == CHANNEL_TITLE.strip().casefold()


def find_channel_pr():
    """Open PR whose title is Channel (exact, case-insensitive), or None. Env override for tests."""
    override = os.environ.get("AGENT_CITY_COMMS_PR") or os.environ.get("AGENT_CITY_COMMS_ISSUE")
    if override:
        try:
            return int(override)
        except ValueError:
            pass
    ok, raw = _gh_api(["repos/%s/pulls?state=open&per_page=100" % REPO])
    if not ok:
        return None
    try:
        items = json.loads(raw or "[]")
    except ValueError:
        return None
    if not isinstance(items, list):
        return None
    for it in items:
        if isinstance(it, dict) and _title_match(it.get("title")):
            n = it.get("number")
            if isinstance(n, int):
                return n
    return None


def find_channel_issue():
    """Back-compat alias: Channel is a PR; same number space as issues for comments."""
    return find_channel_pr()


def _ensure_channel_branch():
    """Create branch CHANNEL_BRANCH with CHANNEL_FILE if needed. Best-effort; returns True when usable."""
    ok, raw = _gh_api(["repos/%s" % REPO])
    if not ok:
        return False
    try:
        default = (json.loads(raw) or {}).get("default_branch") or "main"
    except ValueError:
        default = "main"
    ok, raw = _gh_api(["repos/%s/git/ref/heads/%s" % (REPO, default)])
    if not ok:
        return False
    try:
        sha = json.loads(raw)["object"]["sha"]
    except (ValueError, KeyError, TypeError):
        return False
    # create branch (ignore failure if it already exists)
    _gh_api(["--method", "POST", "repos/%s/git/refs" % REPO, "--input", "-"],
            input_text=json.dumps({"ref": "refs/heads/%s" % CHANNEL_BRANCH, "sha": sha}))
    content_b64 = base64.b64encode(CHANNEL_FILE_BODY.encode("utf-8")).decode("ascii")
    payload = {
        "message": "Channel branch for Agent City message link",
        "content": content_b64,
        "branch": CHANNEL_BRANCH,
    }
    ok_get, raw_get = _gh_api(["repos/%s/contents/%s?ref=%s" % (REPO, CHANNEL_FILE, CHANNEL_BRANCH)])
    if ok_get:
        try:
            file_sha = json.loads(raw_get).get("sha")
            if file_sha:
                payload["sha"] = file_sha
        except (ValueError, AttributeError):
            pass
    ok_put, _ = _gh_api(["--method", "PUT", "repos/%s/contents/%s" % (REPO, CHANNEL_FILE), "--input", "-"],
                        input_text=json.dumps(payload))
    return ok_put


def create_channel_pr():
    """Create the Channel PR (branch + file + gh pr create). Returns number or None. Body never includes secrets."""
    if not _ensure_channel_branch():
        return None
    body = ('Private message channel (PR conversation) between Agent City (Grok Bot) and Grok Build.\n\n'
            'Each comment starts with [from:grok-bot|grok-build] [id:\u2026] [re:\u2026]. '
            'Grok Bot comments MUST start with [from:grok-bot] so the wake listener can exit. '
            'Watchers find this PR by title (%r), never by a hard-coded number.' % CHANNEL_TITLE)
    try:
        r = subprocess.run(
            ["gh", "pr", "create", "--repo", REPO, "--title", CHANNEL_TITLE,
             "--base", "main", "--head", CHANNEL_BRANCH, "--body", body],
            capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return find_channel_pr()
    except OSError:
        return None
    if r.returncode != 0:
        # PR may already exist from a prior attempt
        return find_channel_pr()
    m = re.search(r"/pull/(\d+)", (r.stdout or "") + "\n" + (r.stderr or ""))
    if m:
        return int(m.group(1))
    return find_channel_pr()


def create_channel_issue():
    """Back-compat alias."""
    return create_channel_pr()


def post_hello(issue):
    """First grok-build hello on a brand-new Channel PR. Best-effort; never raises."""
    mid = "g" + secrets.token_hex(3)
    body = make_body(mid, "-", HELLO_TEXT)
    _gh_api(["--method", "POST", "repos/%s/issues/%d/comments" % (REPO, issue), "--input", "-"],
            input_text=json.dumps({"body": body}))


def channel_number(create=True):
    """Resolve the Channel PR number: env override, find by title, or create (+ hello) when create=True.
    Raises RuntimeError with a safe message when it cannot resolve."""
    n = find_channel_pr()
    if n:
        return n
    if not create:
        raise RuntimeError("no open PR titled %r in %s (run setup/watch/send once to create it)" % (CHANNEL_TITLE, REPO))
    n = create_channel_pr()
    if not n:
        raise RuntimeError("could not create the %r PR in %s (check gh auth and repo access)" % (CHANNEL_TITLE, REPO))
    post_hello(n)
    out("%s channel ready: %s#%d (%r) [PR]" % (TAG, REPO, n, CHANNEL_TITLE))
    return n


def classify_http(code, headers, now=None):
    """HTTP status -> exception to raise (or None for success). Pure, so the rules are testable."""
    now = time.time() if now is None else now
    if code in (200, 304):
        return None
    if code in (403, 429):
        retry = headers.get("Retry-After")
        if retry and retry.strip().isdigit():
            return RateLimited(min(float(retry), 3600.0))
        if headers.get("X-RateLimit-Remaining") == "0":
            reset = headers.get("X-RateLimit-Reset", "")
            wait = float(reset) - now + 1 if reset.isdigit() else 60.0
            return RateLimited(min(max(wait, INTERVAL), 3600.0))
        if code == 429:
            return RateLimited(60.0)
        return AuthError("no access")
    if code in (401, 404):
        return AuthError("no access")
    return Transient("HTTP %d" % code)


def next_delay(fails, interval=INTERVAL):
    """Backoff after `fails` consecutive failures (0 = healthy)."""
    if fails <= 0:
        return interval
    return min(interval * (2 ** fails), MAX_BACKOFF)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow redirects: a redirect could carry the token or the sender key to another host."""
    def redirect_request(self, *a, **k):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def http_get(url, token, etag=None, timeout=10):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "agent-city-comms",
        "X-GitHub-Api-Version": "2022-11-28", "Authorization": "Bearer " + token})
    if etag:
        req.add_header("If-None-Match", etag)
    try:
        with OPENER.open(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), b""
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise Transient(type(e).__name__)


def next_link(headers):
    for part in (headers.get("Link") or "").split(","):
        m = re.match(r'\s*<([^>]+)>\s*;\s*rel="next"', part)
        if m:
            return m.group(1)
    return None


def poll_once(state, token, api=None, issue=None):
    """One poll. Returns notification lines. 304 (nothing new) is free against the rate limit."""
    api = api or API
    issue = int(issue if issue is not None else channel_number(create=False))
    url = "%s/repos/%s/issues/%d/comments?per_page=100&since=%s" % (
        api, REPO, issue, urllib.parse.quote(state.get("since") or iso(now_utc()), safe=""))
    etag = state.get("etag") if state.get("etag_url") == url else None
    code, headers, data = http_get(url, token, etag)
    err = classify_http(code, headers)
    if err:
        raise err
    if code == 304:
        return []
    comments, page_url, pages, new_etag = [], url, 0, None
    while True:
        try:
            batch = json.loads(data.decode("utf-8") or "[]")
        except ValueError:
            raise Transient("bad JSON")
        if not isinstance(batch, list):
            raise Transient("unexpected response")
        comments.extend(batch)
        pages += 1
        if page_url == url:
            new_etag = headers.get("ETag") or headers.get("Etag")
        page_url = next_link(headers)
        if not page_url or pages >= 5:
            break
        code, headers, data = http_get(page_url, token)
        err = classify_http(code, headers)
        if err:
            raise err
    lines = process(state, comments, issue=issue)
    # the cursor moved: the next poll uses a new URL, so the old ETag no longer applies
    new_url = "%s/repos/%s/issues/%d/comments?per_page=100&since=%s" % (
        api, REPO, issue, urllib.parse.quote(state.get("since") or "", safe=""))
    state["etag_url"], state["etag"] = (url, new_etag) if new_url == url else (None, None)
    return lines


# ---------------------------------------------------------------- watch

def take_lock(name):
    """Single instance via flock: released by the OS when the process dies, so it can never go stale."""
    os.makedirs(home(), exist_ok=True)
    f = open(path(name), "a+")
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.seek(0)
        pid = f.read().strip()
        f.close()
        return None, pid
    f.seek(0); f.truncate(); f.write(str(os.getpid())); f.flush()
    return f, None


def cmd_watch(a):
    if not gh_path():
        out("%s link watcher not started: %s" % (TAG, GH_HELP)); return 2
    token = gh_token()
    if not token:
        out("%s link watcher not started: %s" % (TAG, AUTH_HELP)); return 2
    if not token_allowed(API):
        out("%s link watcher not started: AGENT_CITY_COMMS_API must be api.github.com" % TAG); return 2
    try:
        issue = channel_number(create=True)
    except RuntimeError as e:
        out("%s link watcher not started: %s" % (TAG, e)); return 2
    lock, pid = take_lock("comms-watch.lock")
    if not lock:
        out("%s link watcher already running (pid %s); not starting another." % (TAG, pid or "?")); return 0
    interval = max(a.interval, 0.05)
    state = load_state()
    state["channel_issue"] = issue
    parent = os.getppid()
    fails, problem, polls = 0, None, 0
    out("%s link watcher on %s PR #%d (%r) every %ss" % (TAG, REPO, issue, CHANNEL_TITLE, int(interval)))
    while True:
        if a.iterations and polls >= a.iterations:
            break
        if os.getppid() != parent:   # the session that started us is gone: do not poll forever as an orphan
            break
        polls += 1
        delay = interval
        try:
            before = json.dumps(state, sort_keys=True)
            lines = poll_once(state, token, issue=issue)
            if problem:
                out("%s link back online." % TAG); problem = None
            fails = 0
            for l in lines:
                out(l)
            if json.dumps(state, sort_keys=True) != before:
                save_state(state)
        except AuthError:
            fails += 1
            fresh = gh_token()          # the token may have been rotated by `gh auth refresh`
            if fresh:
                token = fresh
            if problem != "auth" and fails >= 2:
                out("%s link: GitHub refused access to %s (is gh signed in as the owner? `gh auth status`). "
                    "Retrying every 5 minutes." % (TAG, REPO)); problem = "auth"
            delay = MAX_BACKOFF if fails >= 2 else interval
        except RateLimited as e:
            if problem != "rate":
                out("%s link: GitHub rate limit reached; pausing %d s." % (TAG, int(e.wait))); problem = "rate"
            delay = e.wait
        except Transient:
            fails += 1
            if problem is None and fails >= 3:
                out("%s link offline (GitHub unreachable); retrying with backoff up to %d s." % (TAG, int(MAX_BACKOFF)))
                problem = "offline"
            delay = next_delay(fails, interval)
        if a.iterations and polls >= a.iterations:
            break
        time.sleep(delay)
    return 0


# ---------------------------------------------------------------- webhook config

def load_link_config():
    """Parse bot-webhook.env. Returns {"mode": "thread"|"webhook", "webhook": cfg_or_None} or None if missing."""
    p = path("bot-webhook.env")
    try:
        st = os.stat(p)
        if st.st_mode & 0o077:
            os.chmod(p, 0o600)
        with open(p, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    cfg = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
            v = v[1:-1]
        cfg[k.strip()] = v
    flag = (cfg.get("AGENT_CITY_WEBHOOK") or "").strip().lower()
    if flag in ("off", "0", "false", "no"):
        return {"mode": "thread", "webhook": None}
    url = cfg.get("AGENT_CITY_WEBHOOK_URL", "")
    if not url.startswith("https://") and not url.startswith("http://127.0.0.1"):
        # file exists but no usable webhook -> still counts as configured (thread-only)
        return {"mode": "thread", "webhook": None}
    header = cfg.get("AGENT_CITY_WEBHOOK_HEADER", DEFAULT_HEADER)
    if header and ":" not in header:          # just a name, e.g. X-Sender-Key
        header += ": {key}"
    return {"mode": "webhook", "webhook": {"url": url, "key": cfg.get("AGENT_CITY_WEBHOOK_KEY", ""), "header": header}}


def load_env():
    """Webhook config dict, or None when thread-only / missing. (Watchers need the file, not the webhook.)"""
    c = load_link_config()
    return None if not c else c.get("webhook")


def link_configured():
    """True when setup has been run (bot-webhook.env exists), webhook optional."""
    return load_link_config() is not None


PLACEHOLDER_RE = re.compile(r"^(<[^>]*>|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|\{\{?[^}]*\}?\}|YOUR[_-].*|\*+|\.\.\.|x{6,}|X{6,})$")
SCHEMES = ("Bearer", "Token", "Basic", "Key")


def parse_setup(text, url=None, key=None, header=None):
    """Whatever the routine panel shows (a curl example, 'URL: ... Key: ...', or flags) -> config dict.
    Raises ValueError with a message that never contains the secret."""
    text = text or ""
    found_url = url
    if not found_url:
        m = re.search(r"https?://[^\s'\"<>`]+", text)
        found_url = m.group(0).rstrip(").,;") if m else None
    if not found_url or not (found_url.startswith("https://") or found_url.startswith("http://127.0.0.1")):
        raise ValueError("no https webhook URL found in what was pasted")
    template, found_key = header, key
    if not template:
        heads = [a or b or c for a, b, c in re.findall(r"(?:-H|--header)\s+(?:'([^']*)'|\"([^\"]*)\"|(\S+))", text)]
        heads += re.findall(r"(?im)^\s*((?:authorization|x-[a-z0-9-]+)\s*:\s*\S.*?)\s*$", text)
        for h in heads:
            if ":" not in h:
                continue
            name, value = h.split(":", 1)
            name, value = name.strip(), value.strip()
            if name.lower() in ("content-type", "accept", "user-agent"):
                continue
            scheme = ""
            parts = value.split(None, 1)
            if len(parts) == 2 and parts[0].capitalize() in SCHEMES:
                scheme, value = parts[0] + " ", parts[1].strip()
            template = "%s: %s{key}" % (name, scheme)
            if not PLACEHOLDER_RE.match(value) and not found_key:
                found_key = value
            break
    if not found_key:
        m = re.search(r"(?im)^\s*(?:sender[ _-]?key|api[ _-]?key|secret|token|key)\s*[:=]\s*[\"']?([^\s\"']+)", text)
        if not m:
            # Mid-line "Key: …" / "token: …" (not query-string ?key= inside the URL).
            m = re.search(r"(?i)(?:^|[\s,;])(?:sender[ _-]?key|api[ _-]?key|secret|token|key)\s*[:=]\s*[\"']?([^\s\"']+)", text)
        if m and not PLACEHOLDER_RE.match(m.group(1)):
            found_key = m.group(1)
    if template and "{key}" not in template:
        raise ValueError("--header must contain {key}, e.g. 'Authorization: Bearer {key}'")
    if not template:
        template = DEFAULT_HEADER
    if not found_key:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(found_url).query)
        if any(k.lower() in ("key", "token", "secret", "sig", "signature", "code") for k in q):
            template = ""   # the key travels in the URL; no header needed
        else:
            raise ValueError("found the URL but no sender key; copy the panel's key too, or pass --key")
    if found_key and any(ch in found_key for ch in "\r\n"):
        raise ValueError("the key contains a line break")
    return {"url": found_url, "key": found_key or "", "header": template}


def describe(cfg):
    """A summary safe to print: host only, header name only, key length only."""
    host = urllib.parse.urlparse(cfg["url"]).hostname or "?"
    hname = cfg["header"].split(":", 1)[0] if cfg["header"] else "(none: key is in the URL)"
    return "host %s, header %s, key %s" % (host, hname, ("%d chars" % len(cfg["key"])) if cfg["key"] else "none")


def read_clipboard():
    for cmd in (["pbpaste"], ["wl-paste", "-n"], ["xclip", "-o", "-selection", "clipboard"]):
        if shutil.which(cmd[0]):
            try:
                return subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout
            except (OSError, subprocess.TimeoutExpired):
                return ""
    return ""


def cmd_setup(a):
    paste = " ".join(getattr(a, "paste", None) or []).strip()
    has_flags = bool(a.clipboard or paste or a.url or a.key)
    stdin_text = None
    if not has_flags and not sys.stdin.isatty():
        stdin_text = sys.stdin.read()
        has_flags = bool((stdin_text or "").strip())

    if has_flags:
        if a.clipboard:
            text = read_clipboard()
        elif paste:
            text = paste
        elif a.url:
            text = ""
        else:
            text = stdin_text or ""
        try:
            cfg = parse_setup(text, a.url, a.key, a.header)
        except ValueError as e:
            out("setup: not saved: %s." % e); return 2
        body = ("# Agent City inbox webhook for comms.py. SECRET: stays on this Mac, chmod 600, never commit or paste it.\n"
                "AGENT_CITY_WEBHOOK=on\n"
                "AGENT_CITY_WEBHOOK_URL=%s\nAGENT_CITY_WEBHOOK_KEY=%s\nAGENT_CITY_WEBHOOK_HEADER=%s\n"
                % (cfg["url"], cfg["key"], cfg["header"]))
        write_atomic(path("bot-webhook.env"), body, 0o600)
        out("setup: saved (%s). Key stored chmod 600; never echoed." % describe(cfg))
        if gh_path() and gh_token():
            try:
                n = channel_number(create=True)
                out("setup: Channel PR ready at %s#%d (%r)" % (REPO, n, CHANNEL_TITLE))
            except RuntimeError as e:
                out("setup: webhook saved; Channel PR not created yet (%s). watch/send will retry." % e)
        else:
            out("setup: webhook saved. Install/sign in gh, then run watch or send to create Channel PR.")
        out("setup: test with: python3 comms.py send ping")
        return 0

    # Default: thread-only (no webhook URL/key required).
    if not gh_path():
        out("setup: not ready: " + GH_HELP); return 2
    if not gh_token():
        out("setup: not ready: " + AUTH_HELP); return 2
    body = ("# Agent City message link. Thread-only mode (no webhook).\n"
            "# Optional later: python3 comms.py setup --url URL --key KEY\n"
            "AGENT_CITY_WEBHOOK=off\n")
    write_atomic(path("bot-webhook.env"), body, 0o600)
    try:
        n = channel_number(create=True)
    except RuntimeError as e:
        out("setup: config saved (webhook=off); Channel PR not created yet (%s)." % e); return 2
    out("setup: thread-only link ready. Channel PR %s#%d (%r). Webhook off (optional later)." % (REPO, n, CHANNEL_TITLE))
    out("setup: next: python3 -u ~/.grok/agent-city/comms.py watch")
    return 0


# ---------------------------------------------------------------- send

def rate_check(now=None):
    """Reserve a send slot. Returns (ok, message). Cross-process safe (flock on the log)."""
    now = time.time() if now is None else now
    os.makedirs(home(), exist_ok=True)
    p = path("comms-sends.log")
    with open(p, "a+") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.seek(0)
        stamps = []
        for l in f.read().split():
            try:
                t = float(l)
            except ValueError:
                continue
            if now - 3600 < t <= now + 60:
                stamps.append(t)
        if stamps and now - max(stamps) < SEND_GAP:
            return False, "at most 1 message per %d s; try again in %d s" % (SEND_GAP, int(SEND_GAP - (now - max(stamps))) + 1)
        if len(stamps) >= SEND_HOUR:
            return False, "at most %d messages per hour; next slot in %d min" % (SEND_HOUR, int((min(stamps) + 3600 - now) / 60) + 1)
        stamps.append(now)
        f.seek(0); f.truncate(); f.write("\n".join("%.3f" % t for t in stamps) + "\n")
    return True, ""


def post_comment(body, issue=None):
    """POST via gh (JSON on stdin, so any text is safe). Returns (ok, url_or_error)."""
    try:
        n = int(issue if issue is not None else channel_number(create=True))
        r = subprocess.run(["gh", "api", "--method", "POST", "repos/%s/issues/%d/comments" % (REPO, n), "--input", "-"],
                           input=json.dumps({"body": body}), capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return False, "gh timed out"
    except OSError as e:
        return False, "gh failed to start (%s)" % type(e).__name__
    if r.returncode != 0:
        err = (r.stderr.strip().splitlines() or ["gh exited %d" % r.returncode])[-1]
        return False, err[:200]
    try:
        return True, json.loads(r.stdout).get("html_url", "")
    except ValueError:
        return True, ""


def post_webhook(cfg, payload, timeout=10):
    """Returns (ok, status text). The URL and key never appear in the status text."""
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "User-Agent": "agent-city-comms"}
    if cfg["header"]:
        name, value = cfg["header"].split(":", 1)
        headers[name.strip()] = value.strip().replace("{key}", cfg["key"])
    last = "?"
    for attempt in (1, 2):
        req = urllib.request.Request(cfg["url"], data=data, headers=headers, method="POST")
        try:
            with OPENER.open(req, timeout=timeout) as r:
                return True, "delivered (HTTP %d)" % r.status
        except urllib.error.HTTPError as e:
            last = "HTTP %d" % e.code
            if e.code < 500:
                break
        except (urllib.error.URLError, OSError, ValueError) as e:
            last = "network error (%s)" % type(getattr(e, "reason", e)).__name__
        if attempt == 1:
            time.sleep(2)
    return False, "failed: %s" % last


def cmd_send(a):
    text = sys.stdin.read() if a.text == ["-"] else " ".join(a.text)
    text = text.strip()
    if not text:
        out("send: nothing to send."); return 2
    if len(text) > MAX_TEXT:
        out("send: message is %d characters; the limit is %d. Shorten it." % (len(text), MAX_TEXT)); return 2
    re_id = a.re or "-"
    if re_id != "-" and not ID_RE.match(re_id):
        out("send: --re must be a message id like b1x2y3."); return 2
    if not gh_path():
        out("send: not sent: " + GH_HELP); return 2
    if not gh_token():
        out("send: not sent: " + AUTH_HELP); return 2
    ok, why = rate_check()
    if not ok:
        out("send: not sent: rate limit (%s). Do not retry in a loop." % why); return 3
    try:
        issue = channel_number(create=True)
    except RuntimeError as e:
        out("send: not sent: %s" % e); return 2
    mid = "g" + secrets.token_hex(3)
    c_ok, c_info = post_comment(make_body(mid, re_id, text), issue=issue)
    cfg = load_env()
    if cfg:
        w_ok, w_info = post_webhook(cfg, {"id": mid, "re": re_id, "text": text, "from": ME,
                                          "comment_url": c_info if c_ok else ""})
    else:
        w_ok, w_info = False, "off (thread-only; Agent City wakes on the PR comment)"
    out("%s sent id:%s re:%s | comment: %s | webhook: %s" % (
        TAG, mid, re_id, ("posted " + c_info).strip() if c_ok else "FAILED (%s)" % c_info, w_info))
    if c_ok and not w_ok and cfg:
        out("%s the comment is posted, so the message is not lost; Agent City sees it on its next check." % TAG)
    if not c_ok and w_ok:
        out("%s Agent City got the message through the webhook, but it is not in the thread log." % TAG)
    return 0 if (c_ok or w_ok) else 1


# ---------------------------------------------------------------- status

def cmd_status(a):
    rows = []
    if not gh_path():
        rows.append("gh: missing. " + GH_HELP)
    elif not gh_token():
        rows.append("gh: " + AUTH_HELP)
    else:
        try:
            n = find_channel_issue()
            if n is None:
                rows.append("gh: signed in; Channel PR not found yet (watch/send/setup will create it)")
            else:
                r = subprocess.run(["gh", "api", "repos/%s/issues/%d" % (REPO, n), "--jq", ".number"],
                                   capture_output=True, text=True, timeout=20)
                rows.append("gh: signed in; Channel %s#%d (%r) %s" % (
                    REPO, n, CHANNEL_TITLE, "reachable" if r.returncode == 0 else
                    "NOT reachable (the gh account needs access to the private repo)"))
        except (OSError, subprocess.TimeoutExpired):
            rows.append("gh: signed in; Channel check timed out")
    cfg = load_env()
    link = load_link_config()
    if cfg:
        rows.append("webhook: " + describe(cfg))
    elif link and link.get("mode") == "thread":
        rows.append("webhook: off (thread-only)")
    else:
        rows.append("webhook: not configured (run comms.py setup; thread-only by default)")
    lock, pid = take_lock("comms-watch.lock")
    if lock:
        lock.close(); rows.append("watcher: not running")
    else:
        rows.append("watcher: running (pid %s)" % (pid or "?"))
    s = load_state() if os.path.exists(path("comms-state.json")) else {}
    rows.append("cursor: last comment %s since %s" % (s.get("last_id", "none"), s.get("since", "-")))
    try:
        n = sum(1 for l in open(path("comms-sends.log")) if l.strip() and time.time() - float(l) < 3600)
    except (OSError, ValueError):
        n = 0
    rows.append("sends this hour: %d of %d" % (n, SEND_HOUR))
    for r in rows:
        out(r)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="comms.py", description="Agent City <-> Grok Build message link")
    sub = p.add_subparsers(dest="cmd")
    w = sub.add_parser("watch"); w.add_argument("--interval", type=float, default=INTERVAL)
    w.add_argument("--iterations", type=int, default=0, help=argparse.SUPPRESS)
    s = sub.add_parser("send"); s.add_argument("--re", default="-"); s.add_argument("text", nargs="+")
    u = sub.add_parser("setup"); u.add_argument("--clipboard", action="store_true")
    u.add_argument("--url"); u.add_argument("--key"); u.add_argument("--header")
    u.add_argument("paste", nargs="*", help="optional webhook URL+key paste; omit for thread-only setup")
    sub.add_parser("status")
    a = p.parse_args(argv)
    if not a.cmd:
        p.print_help(); return 2
    try:
        return {"watch": cmd_watch, "send": cmd_send, "setup": cmd_setup, "status": cmd_status}[a.cmd](a)
    except KeyboardInterrupt:
        return 130
    except Exception as e:   # one line, never a traceback with paths or payloads
        out("%s comms.py %s stopped: %s" % (TAG, a.cmd, type(e).__name__)); return 1


if __name__ == "__main__":
    sys.exit(main())
