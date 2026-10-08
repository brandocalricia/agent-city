#!/usr/bin/env python3
"""Agent City -> Grok Build: deterministic helper for the city-apply skill (stdlib only, Python 3.8+).

The model decides (city-council); this script does the bookkeeping that must never go wrong:
which items are pending, at most 3 begun per hour, claims so two sessions never take the same item,
snapshots + rollback of exactly the declared files, mandatory checks/tests, commits of only its own
files, and an append-only log so a corrupted applied.json never causes an item to be reprocessed.

  city_apply.py status [--write-pending]     count pending items (writes pending.txt)
  city_apply.py next [--repo PATH]           up to 3 items actionable here (JSON)
  city_apply.py begin ID --repo PATH --paths P [P ...]
  city_apply.py verify ID --phase before|after
  city_apply.py rollback ID
  city_apply.py commit ID
  city_apply.py finish ID --status applied|declined|failed|deferred --reason TEXT [--commit SHA]
State: $GROK_HOME/agent-city (default ~/.grok/agent-city).
"""
import argparse, datetime, json, os, re, shlex, shutil, subprocess, sys, time

try:
    import fcntl
except ImportError:  # pragma: no cover (Windows)
    fcntl = None

MAX_PER_HOUR = 3
MAX_ATTEMPTS = 3
CLAIM_TTL = 2 * 3600
FINAL = ("applied", "declined", "failed")
GLOBAL_FILE = "rules/45-agent-city-applied.md"
ID_RE = re.compile(r"^AC-[0-9a-f]{8}$")
HEADER_RE = re.compile(r"^- \*\*(AC-[0-9a-f]{8})\*\* \| size hint: (Quick|Full) \| target: (global|repo:[A-Za-z0-9._-]+) \| from: (.+)$")
FIELD_RE = re.compile(r"^  - (change|why|check|test): (.+)$")
PLACEHOLDERS = ("{id}", "{rules_file}", "{repo}", "{test_cmd}", "{lint_cmd}", "{build_cmd}")
SAFE_FIRST = {"grep", "egrep", "fgrep", "test", "[", "ls", "cat", "wc", "head", "tail", "diff", "cmp", "find", "sort",
              "uniq", "true", "false", "jq", "shellcheck", "pytest", "ruff", "mypy", "tsc", "eslint", "echo"}
SAFE_SUB = {"git": {"status", "diff", "log", "show", "ls-files", "grep", "rev-parse"}, "grok": {"inspect"},
            "npm": {"test", "run"}, "make": {"test", "lint", "check", "build"}, "cargo": {"test", "check", "clippy", "build"},
            "go": {"test", "vet", "build"}, "bash": {"-n"}, "sh": {"-n"}, "node": {"--check"}, "npx": {"tsc", "eslint"},
            "python3": {"-m"}, "python": {"-m"}}
SAFE_PY_MODULES = {"pytest", "unittest", "py_compile", "compileall", "json.tool"}


def G():
    return os.environ.get("GROK_HOME") or os.path.join(os.path.expanduser("~"), ".grok")


def D(*p):
    return os.path.join(G(), "agent-city", *p)


def now():
    return time.time()


def today():
    return datetime.date.today().isoformat()


# ---------- feed parsing ----------
def item_problems(it):
    """Same rules as build_data.validate_gb, applied to a parsed feed item. [] = well-formed."""
    p = []
    if len(it.get("change", "")) < 20:
        p.append("change missing or too short")
    if not it.get("why"):
        p.append("why missing")
    ch, ts = it.get("checks", []), it.get("tests", [])
    if len(ch) < 2 or not any(c.startswith("$ ") for c in ch):
        p.append("needs >= 2 checks with at least one '$ ' command")
    if not 1 <= len(ts) <= 2 or not any(t.startswith("$ ") for t in ts):
        p.append("needs 1-2 tests with at least one '$ ' command")
    for c in ch + ts:
        if c.startswith("$ "):
            err = command_problem(c[2:])
            if err:
                p.append(f"unsafe command '{c[2:]}': {err}")
    return p


def parse_feed(text):
    items, cur, in_q = [], None, False
    for line in text.splitlines():
        if line.startswith("## "):
            in_q = line.startswith("## Apply queue")
            cur = None
            continue
        if not in_q:
            continue
        m = HEADER_RE.match(line)
        if m:
            cur = {"id": m.group(1), "size": m.group(2), "target": m.group(3), "from": m.group(4),
                   "change": "", "why": "", "checks": [], "tests": []}
            items.append(cur)
            continue
        f = FIELD_RE.match(line)
        if f and cur is not None:
            k, v = f.group(1), f.group(2).strip()
            if k in ("check", "test"):
                cur[k + "s"].append(v)
            else:
                cur[k] = v
    seen, out = set(), []
    for it in items:
        if it["id"] not in seen:
            seen.add(it["id"])
            it["problems"] = item_problems(it)
            out.append(it)
    return out


def load_feed():
    try:
        with open(D("suggestions.md"), encoding="utf-8") as f:
            return parse_feed(f.read())
    except OSError:
        return []


# ---------- command safety ----------
def command_problem(cmd):
    """None if the command only reads/tests, else the reason it is refused."""
    if "\n" in cmd or "`" in cmd or "$(" in cmd or "<(" in cmd or ";" in cmd:
        return "no newlines, backticks, $( ), <( ) or ;"
    scrubbed = re.sub(r"\s(2>&1|2>/dev/null|>/dev/null|1>/dev/null)(?=\s|$)", " ", " " + cmd)
    if ">" in scrubbed or "<" in scrubbed:
        return "no redirection except to /dev/null"
    if re.search(r"(^|[^&])&([^&]|$)", scrubbed):
        return "no background jobs"
    for seg in re.split(r"\|\||&&|\|", cmd):
        try:
            words = shlex.split(seg)
        except ValueError:
            return "unbalanced quotes"
        if not words:
            return "empty segment"
        w0 = words[0]
        if w0.startswith("{") and w0 in PLACEHOLDERS:
            continue
        if any(a.startswith("--output") or a.startswith("--open-files-in-pager") or (w0 == "git" and a.startswith("-O")) for a in words[1:]):
            return "no --output / pager options"
        if w0 in SAFE_FIRST:
            if w0 == "find" and any(a in ("-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprintf", "-fls") for a in words):
                return "find may not delete, exec, or write files"
            if w0 == "sort" and any(a == "-o" or a.startswith("--output") or (a.startswith("-") and not a.startswith("--") and "o" in a) for a in words[1:]):
                return "sort may not write files (-o)"
            if w0 == "uniq" and len([a for a in words[1:] if not a.startswith("-")]) > 1:
                return "uniq may not write an output file"
            if w0 in ("eslint", "ruff") and any(a.startswith("--fix") or a == "format" for a in words):
                return f"{w0} may only check, not fix"
            if w0 == "tsc" and "--noEmit" not in words:
                return "tsc needs --noEmit"
            continue
        if w0 in SAFE_SUB:
            if len(words) < 2 or words[1] not in SAFE_SUB[w0]:
                return f"'{w0} {words[1] if len(words) > 1 else ''}' not allowed"
            if w0 in ("python3", "python") and (len(words) < 3 or words[2] not in SAFE_PY_MODULES):
                return "python -m only with pytest/unittest/py_compile/compileall/json.tool"
            if w0 == "npx" and words[1] == "tsc" and "--noEmit" not in words:
                return "npx tsc needs --noEmit"
            if w0 == "npx" and words[1] == "eslint" and any(a.startswith("--fix") for a in words):
                return "eslint may only check, not fix"
            if w0 == "npm" and words[1] == "run" and (len(words) < 3 or words[2] not in ("test", "lint", "build", "typecheck", "check")):
                return "npm run only test/lint/build/typecheck/check"
            continue
        return f"'{w0}' is not on the read/test allowlist"
    return None


def detect(repo):
    """Project commands for {test_cmd} {lint_cmd} {build_cmd}; missing ones are None."""
    out = {"test_cmd": None, "lint_cmd": None, "build_cmd": None}
    j = lambda *p: os.path.join(repo, *p)
    try:
        with open(j("package.json"), encoding="utf-8") as f:
            scripts = (json.load(f).get("scripts") or {})
        if "test" in scripts:
            out["test_cmd"] = "npm test"
        for k in ("lint", "typecheck"):
            if k in scripts and not out["lint_cmd"]:
                out["lint_cmd"] = "npm run " + k
        if "build" in scripts:
            out["build_cmd"] = "npm run build"
    except (OSError, ValueError, AttributeError):
        pass
    if os.path.exists(j("Makefile")):
        targets = set(re.findall(r"^([A-Za-z0-9_-]+):", open(j("Makefile"), encoding="utf-8", errors="replace").read(), re.M))
        out["test_cmd"] = out["test_cmd"] or ("make test" if "test" in targets else None)
        out["lint_cmd"] = out["lint_cmd"] or ("make lint" if "lint" in targets else ("make check" if "check" in targets else None))
        out["build_cmd"] = out["build_cmd"] or ("make build" if "build" in targets else None)
    if os.path.exists(j("Cargo.toml")):
        out["test_cmd"] = out["test_cmd"] or "cargo test"
        out["build_cmd"] = out["build_cmd"] or "cargo build"
    if os.path.exists(j("go.mod")):
        out["test_cmd"] = out["test_cmd"] or "go test ./..."
        out["lint_cmd"] = out["lint_cmd"] or "go vet ./..."
    if not out["test_cmd"] and (os.path.exists(j("pytest.ini")) or os.path.exists(j("pyproject.toml")) or os.path.exists(j("setup.cfg"))):
        out["test_cmd"] = "python3 -m pytest -q"
    if not out["test_cmd"] and os.path.isdir(j("tests")):
        out["test_cmd"] = "python3 -m unittest discover -s tests"
    return out


# ---------- state: append-only log + json view ----------
class Lock:
    def __enter__(self):
        os.makedirs(D(), exist_ok=True)
        self.f = open(D(".state.lock"), "a")
        if fcntl:
            fcntl.flock(self.f, fcntl.LOCK_EX)
        return self

    def __exit__(self, *a):
        if fcntl:
            fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()


def load_state():
    """applied.json overlaid with applied.log (log wins). A corrupt applied.json is set aside, never trusted blindly."""
    state = {}
    p = D("applied.json")
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("not an object")
            state.update({k: v for k, v in data.items() if ID_RE.match(k) and isinstance(v, dict)})
        except (OSError, ValueError):
            try:
                os.replace(p, p + ".corrupt-" + str(int(now())))
            except OSError:
                pass
    try:
        with open(D("applied.log"), encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if isinstance(e, dict) and ID_RE.match(str(e.get("id", ""))):
                    state[e["id"]] = {k: v for k, v in e.items() if k != "id"}
    except OSError:
        pass
    return state


def write_json(path, data):
    tmp = path + ".tmp." + str(os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def record(item_id, entry):
    """Caller holds Lock. Log first (source of truth), then the json view."""
    with open(D("applied.log"), "a", encoding="utf-8") as f:
        f.write(json.dumps(dict(entry, id=item_id), sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())
    state = load_state()
    write_json(D("applied.json"), state)
    return state


# ---------- claims, rate limit, journal ----------
def claim_path(item_id):
    return D("claims", item_id)


def claim_active(item_id):
    try:
        return now() - os.path.getmtime(claim_path(item_id)) < CLAIM_TTL
    except OSError:
        return False


def begun_last_hour():
    n = 0
    try:
        with open(D("runs.log"), encoding="utf-8") as f:
            for line in f:
                try:
                    if now() - float(line.split()[0]) < 3600:
                        n += 1
                except (ValueError, IndexError):
                    continue
    except OSError:
        pass
    return n


def jdir(item_id):
    return D("journal", item_id)


def load_journal(item_id):
    with open(os.path.join(jdir(item_id), "journal.json"), encoding="utf-8") as f:
        return json.load(f)


def save_journal(item_id, j):
    write_json(os.path.join(jdir(item_id), "journal.json"), j)


def pending(state, feed):
    out = []
    for it in feed:
        st = state.get(it["id"], {})
        if it["problems"] or st.get("status") in FINAL or int(st.get("attempts", 0)) >= MAX_ATTEMPTS:
            continue
        if claim_active(it["id"]):
            continue
        out.append(it)
    return out


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def toplevel(path):
    try:
        return git(path, "rev-parse", "--show-toplevel").strip()
    except (RuntimeError, OSError):
        return None


def porcelain(repo, paths=None, untracked=True):
    """Changed paths (staged, unstaged, and optionally untracked), NUL-safe for spaces and renames."""
    args = ["status", "--porcelain", "-z", "--untracked-files=" + ("all" if untracked else "no")]
    if paths:
        args += ["--"] + list(paths)
    parts, out, i = git(repo, *args).split("\0"), [], 0
    while i < len(parts):
        e = parts[i]
        if len(e) > 3:
            out.append(e[3:])
            if e[0] in "RC":
                i += 1
        i += 1
    return sorted(out)


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(code)


def ok(**kw):
    print(json.dumps(dict(ok=True, **kw), indent=1))


# ---------- commands ----------
def write_pending(state, feed):
    """pending.txt line 1: global items waiting; line 2: 'repos: a b' with items waiting for those repos."""
    P = pending(state, feed)
    glob_n = sum(1 for it in P if it["target"] == "global")
    repos = sorted({it["target"][5:] for it in P if it["target"].startswith("repo:")})
    tmp = D("pending.txt.tmp." + str(os.getpid()))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(f"{glob_n}\nrepos: {' '.join(repos)}\n")
    os.replace(tmp, D("pending.txt"))
    return glob_n, repos


def cmd_status(a):
    feed, state = load_feed(), load_state()
    if a.write_pending:
        glob_n, repos = write_pending(state, feed)
    else:
        P = pending(state, feed)
        glob_n = sum(1 for it in P if it["target"] == "global")
        repos = sorted({it["target"][5:] for it in P if it["target"].startswith("repo:")})
    ok(pending_global=glob_n, pending_repos=repos, malformed=[it["id"] for it in feed if it["problems"]])


def cmd_next(a):
    feed, state = load_feed(), load_state()
    top = toplevel(a.repo) if a.repo else None
    name = os.path.basename(top) if top else None
    room = max(0, MAX_PER_HOUR - begun_last_hour())
    here = [it for it in pending(state, feed) if it["target"] == "global" or (name and it["target"] == "repo:" + name)]
    ok(items=[{k: it[k] for k in ("id", "size", "target", "change", "why", "checks", "tests")} for it in here[:room]],
       skipped_malformed=[{"id": it["id"], "problems": it["problems"]} for it in feed if it["problems"]], room=room,
       unfinished=unfinished(state))


def unfinished(state):
    """Journals begun but never finished (a crashed or killed session). Their files may hold a half-applied change."""
    out = []
    try:
        names = sorted(os.listdir(D("journal")))
    except OSError:
        return out
    for iid in names:
        if not ID_RE.match(iid) or state.get(iid, {}).get("status") in FINAL or claim_active(iid):
            continue
        try:
            j = load_journal(iid)
        except (OSError, ValueError):
            continue
        if not j.get("rolled_back") and not j.get("finished"):
            out.append({"id": iid, "base": j["base"], "paths": [p["path"] for p in j["paths"]]})
    return out


def cmd_begin(a):
    feed = {it["id"]: it for it in load_feed()}
    it = feed.get(a.id)
    if not it:
        fail("unknown id")
    if it["problems"]:
        fail("malformed item (missing checks/tests?): " + "; ".join(it["problems"]))
    with Lock():
        state = load_state()
        st = state.get(a.id, {})
        if st.get("status") in FINAL:
            fail(f"already {st['status']}: processed once")
        if begun_last_hour() >= MAX_PER_HOUR:
            fail(f"limit: {MAX_PER_HOUR} items per hour")
        if claim_active(a.id):
            fail("claimed by another session")
        if it["target"] == "global":
            base, is_git = G(), False
            paths = [GLOBAL_FILE]
            if a.paths and [os.path.normpath(p) for p in a.paths] != [GLOBAL_FILE]:
                fail(f"global items may only touch {GLOBAL_FILE}")
        else:
            base = toplevel(a.repo or ".")
            if not base or "repo:" + os.path.basename(base) != it["target"]:
                fail(f"run this in the repo named by {it['target']}")
            is_git = True
            if not a.paths:
                fail("--paths required: declare every file you will create, edit, or delete")
            paths = []
            for p in a.paths:
                full = os.path.realpath(os.path.join(base, p))
                if not full.startswith(os.path.realpath(base) + os.sep):
                    fail(f"path outside the repo: {p}")
                paths.append(os.path.relpath(full, os.path.realpath(base)))
            dirty = porcelain(base, paths)
            if dirty:
                fail("uncommitted changes in declared paths (the owner's work is never touched): " + ", ".join(dirty))
        jd = jdir(a.id)
        if os.path.isdir(jd):
            shutil.rmtree(jd)
        os.makedirs(os.path.join(jd, "files"))
        snap = []
        for i, p in enumerate(paths):
            full = os.path.join(base, p)
            e = {"path": p, "existed": os.path.isfile(full)}
            if e["existed"]:
                shutil.copy2(full, os.path.join(jd, "files", str(i)))
            snap.append(e)
        j = {"id": a.id, "base": base, "git": is_git, "paths": snap, "began": now(),
             "head": git(base, "rev-parse", "HEAD").strip() if is_git else None,
             "dirty_before": porcelain(base) if is_git else [], "verified_before": False, "verified_after": False}
        save_journal(a.id, j)
        os.makedirs(D("claims"), exist_ok=True)
        with open(claim_path(a.id), "w") as f:
            f.write(str(os.getpid()))
        with open(D("runs.log"), "a") as f:
            f.write(f"{now()} {a.id}\n")
    ok(base=base, paths=paths, git=is_git)


def expand(cmd, j, cmds):
    for k, v in (("{id}", j["id"]), ("{rules_file}", os.path.join(G(), GLOBAL_FILE)), ("{repo}", j["base"])):
        cmd = cmd.replace(k, shlex.quote(v) if k != "{id}" else v)
    for k in ("test_cmd", "lint_cmd", "build_cmd"):
        if "{" + k + "}" in cmd:
            if not cmds[k]:
                return None
            cmd = cmd.replace("{" + k + "}", cmds[k])
    return cmd


def run_cmd(cmd, cwd):
    err = command_problem(cmd)
    if err:
        return {"cmd": cmd, "pass": False, "out": "refused: " + err}
    try:
        r = subprocess.run(["bash", "-c", cmd], cwd=cwd, capture_output=True, text=True, timeout=300,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        return {"cmd": cmd, "pass": r.returncode == 0, "out": (r.stdout + r.stderr)[-600:]}
    except subprocess.TimeoutExpired:
        return {"cmd": cmd, "pass": False, "out": "timed out after 300s"}


def builtin_checks(j, phase):
    res = []
    if j["git"] and phase == "after":
        declared, before = {p["path"] for p in j["paths"]}, set(j["dirty_before"])
        extra = sorted(set(porcelain(j["base"], untracked=False)) - before - declared)
        res.append({"cmd": "builtin: no undeclared tracked file changed", "pass": not extra,
                    "out": ("changed but not declared: " + ", ".join(extra)) if extra else ""})
        # new untracked files are never committed (commit takes declared paths only); build/test artifacts are normal
        new = sorted(set(porcelain(j["base"])) - set(porcelain(j["base"], untracked=False)) - before - declared)
        if new:
            res.append({"cmd": "builtin: new untracked files (not committed; delete any you created by mistake)", "pass": True,
                        "out": ", ".join(new[:20])})
    if not j["git"]:
        rf = os.path.join(G(), GLOBAL_FILE)
        heads = re.findall(r"^## (AC-[0-9a-f]{8})\b", open(rf, encoding="utf-8").read(), re.M) if os.path.exists(rf) else []
        dup = sorted({h for h in heads if heads.count(h) > 1})
        res.append({"cmd": "builtin: one section per id in " + GLOBAL_FILE, "pass": not dup, "out": ("duplicates: " + ", ".join(dup)) if dup else ""})
        if phase == "after":
            res.append({"cmd": f"builtin: section ## {j['id']} present", "pass": j["id"] in heads, "out": ""})
    return res


def cmd_verify(a):
    feed = {it["id"]: it for it in load_feed()}
    it = feed.get(a.id)
    try:
        j = load_journal(a.id)
    except (OSError, ValueError):
        fail("no journal: run begin first")
    if not it or it["problems"]:
        fail("item missing or malformed")
    cmds = detect(j["base"]) if j["git"] else {"test_cmd": None, "lint_cmd": None, "build_cmd": None}
    results, manual, ran_tests = [], [], 0
    groups = [("check", it["checks"])] + ([("test", it["tests"])] if a.phase == "after" else [])
    for kind, lst in groups:
        for c in lst:
            if not c.startswith("$ "):
                manual.append(f"{kind}: {c}")
                continue
            cmd = expand(c[2:], j, cmds)
            if cmd is None:
                results.append({"cmd": c[2:], "pass": True, "out": "skipped: project has no such command", "skipped": True})
                continue
            r = run_cmd(cmd, j["base"])
            r["kind"] = kind
            results.append(r)
            if kind == "test" and r["pass"]:
                ran_tests += 1
    results += builtin_checks(j, a.phase)
    passed = all(r["pass"] for r in results)
    if a.phase == "after" and ran_tests == 0:
        passed = False
        results.append({"cmd": "builtin: at least one test ran and passed", "pass": False, "out": ""})
    j["verified_" + a.phase] = passed
    save_journal(a.id, j)
    print(json.dumps({"ok": passed, "phase": a.phase, "results": results, "manual": manual}, indent=1))
    sys.exit(0 if passed else 1)


def cmd_rollback(a):
    try:
        j = load_journal(a.id)
    except (OSError, ValueError):
        fail("no journal")
    restored = []
    for i, e in enumerate(j["paths"]):
        full = os.path.join(j["base"], e["path"])
        if e["existed"]:
            os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
            shutil.copy2(os.path.join(jdir(a.id), "files", str(i)), full)
        elif os.path.exists(full):
            os.remove(full)
        restored.append(e["path"])
    j["verified_after"] = False
    j["rolled_back"] = True
    save_journal(a.id, j)
    ok(restored=restored)


def cmd_commit(a):
    try:
        j = load_journal(a.id)
    except (OSError, ValueError):
        fail("no journal")
    if not j["git"]:
        fail("not a git target: nothing to commit (the snapshot is the backup)")
    if not j.get("verified_after"):
        fail("verify --phase after has not passed")
    feed = {it["id"]: it for it in load_feed()}
    change = feed.get(a.id, {}).get("change", "")
    paths = [e["path"] for e in j["paths"]]
    git(j["base"], "add", "-A", "--", *paths)
    msg = f"city: {a.id} {change[:60]}".strip()
    r = subprocess.run(["git", "-C", j["base"], "commit", "-q", "-m", msg, "--only", "--"] + paths, capture_output=True, text=True)
    if r.returncode != 0:
        fail("commit failed (roll back and finish as failed): " + (r.stderr or r.stdout).strip()[-300:])
    sha = git(j["base"], "rev-parse", "--short", "HEAD").strip()
    j["commit"] = sha
    save_journal(a.id, j)
    ok(commit=sha)


def cmd_finish(a):
    with Lock():
        state = load_state()
        st = state.get(a.id, {})
        if st.get("status") in FINAL:
            fail(f"already {st['status']}")
        status, attempts = a.status, int(st.get("attempts", 0))
        try:
            j = load_journal(a.id)
        except (OSError, ValueError):
            j = None
        if status == "applied" and not (j and j.get("verified_after") and not j.get("rolled_back")):
            fail("applied requires a passing verify --phase after")
        if status == "applied" and j and j["git"] and not (a.commit or j.get("commit")):
            fail("applied in a git repo requires a commit (run commit first)")
        if status == "deferred":
            attempts += 1
            if attempts >= MAX_ATTEMPTS:
                status, a.reason = "failed", f"deferred {attempts} times: {a.reason}"
        entry = {"status": status, "date": today(), "reason": a.reason[:300], "attempts": attempts,
                 "where": (j or {}).get("base", ""), "commit": a.commit or (j or {}).get("commit", "")}
        record(a.id, entry)
        if j:
            j["finished"] = True
            save_journal(a.id, j)
        try:
            os.remove(claim_path(a.id))
        except OSError:
            pass
        write_pending(load_state(), load_feed())
    ok(id=a.id, **entry)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="city_apply.py")
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("status"); s.add_argument("--write-pending", action="store_true")
    s = sp.add_parser("next"); s.add_argument("--repo")
    s = sp.add_parser("begin"); s.add_argument("id"); s.add_argument("--repo"); s.add_argument("--paths", nargs="*")
    s = sp.add_parser("verify"); s.add_argument("id"); s.add_argument("--phase", choices=("before", "after"), required=True)
    s = sp.add_parser("rollback"); s.add_argument("id")
    s = sp.add_parser("commit"); s.add_argument("id")
    s = sp.add_parser("finish"); s.add_argument("id"); s.add_argument("--status", choices=("applied", "declined", "failed", "deferred"), required=True)
    s.add_argument("--reason", required=True); s.add_argument("--commit", default="")
    a = ap.parse_args(argv)
    if hasattr(a, "id") and not ID_RE.match(a.id):
        fail("bad id")
    os.makedirs(D(), exist_ok=True)
    {"status": cmd_status, "next": cmd_next, "begin": cmd_begin, "verify": cmd_verify, "rollback": cmd_rollback,
     "commit": cmd_commit, "finish": cmd_finish}[a.cmd](a)


if __name__ == "__main__":
    main()
