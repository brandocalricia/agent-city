#!/usr/bin/env python3
"""Regenerate data.js (window.CITY_DATA) from REAL state on this box.

Sources:
  - /home/box/agent-data/workflows/*/SKILL.md   (user-created skills; frontmatter name/description)
  - /home/box/agent-data/agents/*/profile.json  (agent roster: name, title, description, avatar)
  - ./CHANGELOG.md                              (city build history)
  - ./finds.json                                (Market scout finds: [{date,title,url,source,why_useful,status?}])
  - ./activity.json                             (role log, append-only: [{date,session,role,action,details,link?,...}])
  - /home/box/agent-data/agents/*/automations/  (saved routines, shown on the Office board)
  - ./IDEALS.md                                 (the user's ideals; the Council checks every ruling against them)
  - activity.json / finds.json entries with a "gb" field  -> grok-build/suggestions.md (Grok Build feed, validated:
    a malformed gb entry stops the build so the session cannot publish) + grok-build/manifest.txt (sha256 per file)
  - ./costs.json                                (Meter Reader ledger + Optimizer savings, shown in the Treasury;
    tools/treasury.py adds lifetime totals and, on the local copy only, weekly pacing numbers from budget.json via tools/pace.py)
  - ./data/omniroute.json                       (sanitized OmniRoute snapshot for the Router Exchange and Treasury Savings Hub;
    missing file -> {}; never publish budget.json)
  - ./news.json                                 (Reporter's morning digest: [{date,title,url,source,why,tag,for?}], validated;
    stories older than NEWS_KEEP_DAYS drop out of data.js; `for` routes a story to the Council, Scout, Prompt Smith, Tutor, or GB)
  - ./private.json (gitignored) -> ./private.js (gitignored): Courier/Timekeeper notes, local copy only
No data is invented: empty sources stay empty and the city shows an empty state.
Run:  python3 build_data.py
"""
import json, os, re, glob, datetime, hashlib, sys

ROOT = "/home/box/agent-data"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "grok-build"))
sys.path.insert(0, os.path.join(HERE, "tools"))
from city_apply import command_problem, PLACEHOLDERS  # one command allowlist for both ends

GB_TARGET_RE = re.compile(r"^(global|repo:[A-Za-z0-9._-]+)$")
GB_KEEP_DAYS = 60            # Apply-queue items older than this drop off the feed
GB_MAX_PER_DAY = 3           # at most 3 new Grok Build items per day: each one costs the owner a council run
DATA_ACTIVITY_CAP = 150      # data.js keeps the newest 150 actions + each role's newest 12 (Optimizer, 2026-10-08)
DATA_ROLE_KEEP = 12
NEWS_KEEP_DAYS = 14          # the Newsroom digest only covers the last 2 weeks (keeps data.js small)
NEWS_MAX_PER_DAY = 8
NEWS_TAGS = ("model", "agents", "grok", "grok-build", "technique", "tokens", "tools", "school")
NEWS_FOR = ("council", "scout", "promptsmith", "tutor", "gb")
# files Grok Build's updater may install; manifest.txt carries their sha256 (order = update order)
GB_MANIFEST = ["grok-build/suggestions.md", "grok-build/prompts.md", "IDEALS.md", "grok-build/skills/city-council/SKILL.md",
               "grok-build/skills/city-apply/SKILL.md", "grok-build/rules/40-agent-city.md", "grok-build/hooks/agent-city.json",
               "grok-build/city_apply.py", "grok-build/comms/bot-link/SKILL.md", "grok-build/comms/comms.py", "grok-build/update.sh"]


def parse_frontmatter(text):
    meta = {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    body = text
    if m:
        body = m.group(2)
        key = None
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                key, v = k.strip(), v.strip()
                meta[key] = "" if v in (">", ">-", "|", "|-") else v.strip('"').strip("'")
            elif key and line.startswith(" "):  # folded/literal block continuation
                meta[key] = (meta[key] + " " + line.strip()).strip()
    return meta, body


def load_skills():
    skills = []
    for path in sorted(glob.glob(os.path.join(ROOT, "workflows", "*", "SKILL.md"))):
        try:
            with open(path, encoding="utf-8") as f:
                meta, body = parse_frontmatter(f.read())
        except OSError:
            continue
        folder = os.path.basename(os.path.dirname(path))
        skills.append({
            "id": folder,
            "name": meta.get("name") or folder,
            "description": meta.get("description", ""),
            # blockquoted notes (e.g. "> Source: private repo ...") stay out of the public preview
            "preview": "\n".join(l for l in body.splitlines() if not l.lstrip().startswith(">")).strip()[:600],
            "updated": datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d"),
        })
    return skills


def load_agents():
    active = None
    try:
        with open(os.path.join(ROOT, "agents", "active-agent.json")) as f:
            a = json.load(f)
            active = (a.get("activeAgentId") or a.get("agentId") or a.get("id")) if isinstance(a, dict) else a
    except Exception:
        pass
    agents = []
    for path in sorted(glob.glob(os.path.join(ROOT, "agents", "*", "profile.json"))):
        try:
            with open(path, encoding="utf-8") as f:
                p = json.load(f)
        except Exception:
            continue
        aid = os.path.basename(os.path.dirname(path))
        agents.append({
            "id": aid,
            "name": p.get("name") or "Unnamed agent",
            "title": p.get("title") or "",
            "description": p.get("description") or "",
            "color": p.get("avatarColor") or "",
            "shape": p.get("avatarShape") or "",
            "active": aid == active,
        })
    return agents


def load_changelog():
    path = os.path.join(HERE, "CHANGELOG.md")
    entries, cur = [], None
    if not os.path.exists(path):
        return entries
    for line in open(path, encoding="utf-8"):
        line = line.rstrip()
        h = re.match(r"^##\s+(.*)", line)
        if h:
            cur = {"title": h.group(1).strip(), "items": []}
            entries.append(cur)
        elif cur and re.match(r"^\s*[-*]\s+", line):
            cur["items"].append(re.sub(r"^\s*[-*]\s+", "", line))
    return entries


def load_finds():
    path = os.path.join(HERE, "finds.json")
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, ValueError):
        return []
    keys = ("date", "title", "url", "source", "why_useful", "course")
    finds = [dict({k: str(x.get(k, "")) for k in keys}, status=str(x.get("status", "new"))) for x in raw if isinstance(x, dict) and x.get("title")]
    return sorted(finds, key=lambda x: x["date"], reverse=True)


def load_ideals():
    """IDEALS.md numbered lines -> [{n, title, text}] (shown in the Council Chamber)."""
    path = os.path.join(HERE, "IDEALS.md")
    out = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            m = re.match(r"^(\d+)\.\s+\*\*(.+?)\*\*\s*(.*)", line.strip())
            if m:
                out.append({"n": int(m.group(1)), "title": m.group(2).rstrip("."), "text": m.group(3)})
    return out


def load_json(name, default):
    try:
        with open(os.path.join(HERE, name), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def load_activity():
    raw = load_json("activity.json", [])
    items = [x for x in raw if isinstance(x, dict) and x.get("role") and x.get("action")]
    # file is append-only (oldest first); show newest first, stable within a date
    return [x for _, x in sorted(enumerate(items), key=lambda p: (p[1].get("date", ""), p[0]), reverse=True)]


def load_routines():
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, "agents", "*", "automations", "*"))):
        try:
            with open(path, encoding="utf-8") as f:
                r = json.load(f)
        except Exception:
            continue
        if isinstance(r, dict):
            out.append({
                "name": str(r.get("name") or r.get("title") or os.path.basename(path)),
                "schedule": str(r.get("schedule") or r.get("cron") or r.get("rrule") or ""),
                "description": str(r.get("description") or r.get("prompt") or "")[:300],
            })
    return out


def validate_gb(g):
    """Schema for a gb entry. Returns a list of problems ([] = valid). Mirrors city_apply.item_problems."""
    if not isinstance(g, dict):
        return ["gb must be an object"]
    p = []
    known = {"change", "target", "size", "why", "checks", "tests"}
    p += [f"unknown key '{k}'" for k in g if k not in known]
    strs = lambda v: isinstance(v, list) and all(isinstance(x, str) and x.strip() and "\n" not in x for x in v)
    if not isinstance(g.get("change"), str) or len(g["change"].strip()) < 20 or "\n" in g["change"]:
        p.append("change: one line, at least 20 characters")
    if not isinstance(g.get("target"), str) or not GB_TARGET_RE.match(g["target"]):
        p.append("target: 'global' or 'repo:<folder name>'")
    if g.get("size") not in ("Quick", "Full"):
        p.append("size: 'Quick' or 'Full'")
    if not isinstance(g.get("why"), str) or not g["why"].strip() or "\n" in g["why"]:
        p.append("why: one non-empty line")
    ch, ts = g.get("checks"), g.get("tests")
    if not strs(ch) or len(ch) < 2 or not any(c.startswith("$ ") for c in ch):
        p.append("checks: list of >= 2 one-line strings, at least one '$ ' command (wiring checks run before and after)")
    if not strs(ts) or not 1 <= len(ts) <= 2 or not any(t.startswith("$ ") for t in ts):
        p.append("tests: list of 1-2 one-line strings, at least one '$ ' command that proves the change")
    for c in (ch if strs(ch) else []) + (ts if strs(ts) else []):
        if re.search(r"AC-[0-9a-f]{8}", c):
            p.append(f"'{c}': use {{id}}, not a literal id")
        if c.startswith("$ "):
            bad = [t for t in re.findall(r"\{[a-z_]+\}", c) if t not in PLACEHOLDERS]
            if bad:
                p.append(f"'{c}': unknown placeholder {bad[0]} (allowed: {', '.join(PLACEHOLDERS)})")
            err = command_problem(c[2:])
            if err:
                p.append(f"'{c}': {err}")
    return p


def gb_entries():
    """(source label, entry) for every activity/finds entry that has a gb field, oldest first."""
    out = []
    for i, x in enumerate(load_json("activity.json", [])):
        if isinstance(x, dict) and "gb" in x:
            out.append((f"activity.json #{i} ({x.get('role', '?')}: {x.get('action', '')[:40]})", x))
    for i, x in enumerate(load_json("finds.json", [])):
        if isinstance(x, dict) and "gb" in x:
            out.append((f"finds.json #{i} ({x.get('title', '')[:40]})", x))
    return out


def gb_errors():
    errs = [f"{src}: {e}" for src, x in gb_entries() for e in validate_gb(x["gb"])]
    per_day = {}
    for src, x in gb_entries():
        per_day[x.get("date", "")] = per_day.get(x.get("date", ""), 0) + 1
    errs += [f"{d or 'undated'}: {n} gb items (max {GB_MAX_PER_DAY} per day)" for d, n in sorted(per_day.items()) if n > GB_MAX_PER_DAY]
    return errs


def news_errors():
    """Malformed news.json stories stop the build (like gb items): the digest is public and must have real sources."""
    p = os.path.join(HERE, "news.json")
    if os.path.exists(p) and load_json("news.json", None) is None:
        return ["news.json: not valid JSON"]
    raw = load_json("news.json", [])
    if not isinstance(raw, list):
        return ["news.json: must be a list of stories"]
    errs, per_day = [], {}
    for i, x in enumerate(raw):
        where = f"news.json #{i}"
        if not isinstance(x, dict):
            errs.append(f"{where}: not an object"); continue
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(x.get("date", ""))):
            errs.append(f"{where}: date must be YYYY-MM-DD")
        for k in ("title", "why", "source"):
            if not isinstance(x.get(k), str) or not x[k].strip():
                errs.append(f"{where}: missing {k}")
        if not isinstance(x.get("url"), str) or not re.match(r"^https://\S+$", x["url"]):
            errs.append(f"{where}: url must be an https link to the source")
        if x.get("tag") not in NEWS_TAGS:
            errs.append(f"{where}: tag must be one of {', '.join(NEWS_TAGS)}")
        f = x.get("for", [])
        if not isinstance(f, list) or any(d not in NEWS_FOR for d in f):
            errs.append(f"{where}: for must be a list from {', '.join(NEWS_FOR)}")
        per_day[x.get("date")] = per_day.get(x.get("date"), 0) + 1
    errs += [f"news.json: {n} stories on {d} (max {NEWS_MAX_PER_DAY})" for d, n in sorted(per_day.items(), key=str) if n > NEWS_MAX_PER_DAY]
    return errs


def load_news(today=None):
    """Stories from the last NEWS_KEEP_DAYS days, newest first (ties keep the Reporter's order)."""
    today = today or datetime.date.today()
    cutoff = (today - datetime.timedelta(days=NEWS_KEEP_DAYS)).isoformat()
    keys = ("date", "title", "url", "source", "why", "tag")
    raw = [x for x in load_json("news.json", []) if isinstance(x, dict) and str(x.get("date", "")) >= cutoff]
    out = [dict({k: str(x.get(k, "")).strip() for k in keys}, **{"for": list(x.get("for", []))}) for x in raw]
    return sorted(out, key=lambda x: x["date"], reverse=True)


def gb_items(today=None):
    """Valid gb entries -> Apply-queue items. id = AC- + sha1(change)[:8]: stable across edits of anything but the change."""
    today = today or datetime.date.today()
    cutoff = (today - datetime.timedelta(days=GB_KEEP_DAYS)).isoformat()
    out, seen = [], set()
    for src, x in sorted(gb_entries(), key=lambda e: e[1].get("date", "")):
        g = x["gb"]
        if validate_gb(g) or x.get("date", "") < cutoff:
            continue
        iid = "AC-" + hashlib.sha1(g["change"].strip().encode("utf-8")).hexdigest()[:8]
        if iid in seen:
            continue
        seen.add(iid)
        out.append({"id": iid, "date": x.get("date", ""), "from": x.get("role") or "scout", "change": g["change"].strip(),
                    "target": g["target"], "size": g["size"], "why": g["why"].strip(), "checks": g["checks"], "tests": g["tests"]})
    return out


def next_steps(n=5):
    path, out = os.path.join(HERE, "ROADMAP.md"), []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            m = re.match(r"^\d+\.\s+\[ \]\s+(.*)", line.strip())
            if m and len(out) < n:
                out.append(m.group(1))
    return out


def write_gb_suggestions(activity, items, generated):
    """grok-build/suggestions.md: the feed Grok Build's city-apply skill reads (refreshed every session)."""
    L = ["# Agent City suggestions for Grok Build", "",
         f"Generated {generated} by build_data.py; refreshed every city session. Read by the `city-apply` skill.",
         "Only the Apply queue is actionable. Each id is processed once; local state is `~/.grok/agent-city/applied.json`.",
         "Every item carries checks (run before and after; `$ ` lines are commands) and tests (must pass). Items without them are skipped.", "",
         "## Apply queue", ""]
    for it in items:
        L += [f"- **{it['id']}** | size hint: {it['size']} | target: {it['target']} | from: {it['from']}, {it['date']}",
              f"  - change: {it['change']}", f"  - why: {it['why']}"]
        L += [f"  - check: {c}" for c in it["checks"]] + [f"  - test: {t}" for t in it["tests"]]
    if not items:
        L.append("(empty)")
    L += ["", "## Latest Council verdicts (context; already handled in the city)", ""]
    V = [a for a in activity if a.get("role") == "council" and a.get("verdict")][:5]
    L += [f"- {a.get('date','')} {a.get('size','')} {a['verdict']} {a.get('confidence','?')}/10: {a.get('question','')} Reason: {a.get('reason','')}" for a in V] or ["(none yet)"]
    L += ["", "## Next best steps for the city (context)", ""]
    L += [f"{i}. {t}" for i, t in enumerate(next_steps(), 1)] or ["(none)"]
    L += ["", "## Newsroom: recent news for Grok Build (context, not actionable)", ""]
    NW = [n for n in load_news() if "gb" in n["for"]][:5]
    L += [f"- {n['date']} [{n['title']}]({n['url']}) ({n['tag']}): {n['why']}" for n in NW] or ["(none yet)"]
    L += ["", "## Scout finds for Grok Build (context)", ""]
    F = [f for f in load_json("finds.json", []) if isinstance(f, dict) and f.get("gb")]
    L += [f"- [{f['title']}]({f.get('url','')}): {f.get('why_useful','')}" for f in F] or ["(none yet)"]
    os.makedirs(os.path.join(HERE, "grok-build"), exist_ok=True)
    with open(os.path.join(HERE, "grok-build", "suggestions.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def file_sha(rel):
    with open(os.path.join(HERE, rel), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def write_manifest():
    """grok-build/manifest.txt: '<sha256>  <path>' per installable file, then 'end' (a partial download lacks it)."""
    lines = [f"{file_sha(p)}  {p}" for p in GB_MANIFEST if os.path.exists(os.path.join(HERE, p))]
    with open(os.path.join(HERE, "grok-build", "manifest.txt"), "w", encoding="utf-8") as f:
        f.write("# Agent City -> Grok Build manifest (generated by build_data.py)\n" + "\n".join(lines) + "\nend\n")


def cap_activity(acts):
    """Newest DATA_ACTIVITY_CAP actions plus each role's newest DATA_ROLE_KEEP, in the original newest-first order."""
    keep, per = set(range(min(len(acts), DATA_ACTIVITY_CAP))), {}
    for i, a in enumerate(acts):
        r = a.get("role")
        if per.get(r, 0) < DATA_ROLE_KEEP:
            per[r] = per.get(r, 0) + 1
            keep.add(i)
    return [a for i, a in enumerate(acts) if i in keep]


def load_costs():
    c = load_json("costs.json", {})
    if not isinstance(c, dict):
        return {"ledger": [], "savings": []}
    return {"ledger": [x for x in c.get("ledger", []) if isinstance(x, dict)][-12:], "savings": [x for x in c.get("savings", []) if isinstance(x, dict)]}


def load_omniroute():
    o = load_json(os.path.join("data", "omniroute.json"), {})
    return o if isinstance(o, dict) else {}


def load_treasury(acts, capped):
    import treasury
    c = load_json("costs.json", {})
    size = lambda a: len(json.dumps(a, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    return treasury.summarize(c if isinstance(c, dict) else {}, os.path.join(HERE, "budget.json"), size(acts) - size(capped))


def write_private():
    """private.json -> private.js (both gitignored). Removes a stale private.js if private.json is gone."""
    src, out = os.path.join(HERE, "private.json"), os.path.join(HERE, "private.js")
    data = load_json("private.json", None)
    if data is None:
        if os.path.exists(out):
            os.remove(out)
        return False
    with open(out, "w", encoding="utf-8") as f:
        f.write("// LOCAL ONLY - generated from private.json, never commit.\n")
        f.write("window.CITY_PRIVATE = " + json.dumps(data, indent=1, ensure_ascii=False) + ";\n")
    return True


def previous_box_state():
    """Off the Grok box (e.g. the publish Action), keep the skills/agents/routines of the committed data.js
    instead of blanking them, so CI can regenerate data.js and sessions never have to push it (Optimizer, 2026-10-08)."""
    if os.path.isdir(ROOT):
        return None
    try:
        with open(os.path.join(HERE, "data.js"), encoding="utf-8") as f:
            line = next(l for l in f if l.startswith("window.CITY_DATA = "))
        old = json.loads(line[len("window.CITY_DATA = "):].rstrip().rstrip(";"))
        return {k: old.get(k) or [] for k in ("skills", "agents", "routines")}
    except (OSError, StopIteration, ValueError):
        return None


def main():
    errs = gb_errors() + news_errors()
    if errs:  # stop before writing anything, so a session can never publish a malformed feed
        print("build_data.py: invalid gb entries or news stories (fix them; nothing was written):\n  " + "\n  ".join(errs), file=sys.stderr)
        return 1
    acts = load_activity()
    capped = cap_activity(acts)
    data = {
        "generatedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "skills": load_skills(),
        "agents": load_agents(),
        "changelog": load_changelog(),
        "finds": load_finds(),
        "activity": capped,
        "totals": {"actions": len(acts), "sessions": len({a.get("session") for a in acts if a.get("session")})},
        "routines": load_routines(),
        "ideals": load_ideals(),
        "costs": load_costs(),
        "news": load_news(),
        "treasury": load_treasury(acts, capped),
        "omniroute": load_omniroute(),
    }
    prev = previous_box_state()
    if prev:
        data.update(prev)
    items = gb_items()
    data["gb"] = [{k: i[k] for k in ("id", "change", "target", "size", "date", "checks", "tests")} for i in items]
    write_gb_suggestions(acts, items, data["generatedAt"])
    write_manifest()
    out = os.path.join(HERE, "data.js")
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("// AUTO-GENERATED by build_data.py - do not edit by hand.\n")
        f.write("window.CITY_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    os.replace(tmp, out)
    print(f"data.js: {len(data['skills'])} skills, {len(data['agents'])} agents, {len(data['changelog'])} changelog entries, {len(data['finds'])} finds, {len(data['activity'])}/{len(acts)} actions, {len(data['routines'])} routines, {len(items)} Grok Build items, {len(data['news'])} news; private.js: {'yes' if write_private() else 'no'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
