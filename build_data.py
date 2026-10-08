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
  - activity.json / finds.json entries with a "gb" field  -> grok-build/suggestions.md (Grok Build feed)
  - ./private.json (gitignored) -> ./private.js (gitignored): Courier/Timekeeper notes, local copy only
No data is invented: empty sources stay empty and the city shows an empty state.
Run:  python3 build_data.py
"""
import json, os, re, glob, datetime, hashlib

ROOT = "/home/box/agent-data"
HERE = os.path.dirname(os.path.abspath(__file__))


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


def gb_items(activity, finds):
    """Entries with a gb field {change, target, size?, why?} become Grok Build Apply-queue items (stable ids)."""
    out = []
    for src, x in [("activity", a) for a in reversed(activity)] + [("find", f) for f in load_json("finds.json", [])]:
        g = x.get("gb") if isinstance(x, dict) else None
        if not isinstance(g, dict) or not g.get("change"):
            continue
        out.append({
            "id": "AC-" + hashlib.sha1(g["change"].encode("utf-8")).hexdigest()[:8],
            "date": x.get("date", ""), "from": (x.get("role") or "scout") if src == "activity" else "scout",
            "change": g["change"], "target": g.get("target", "any repo"), "size": g.get("size", "Quick"),
            "why": g.get("why") or x.get("action") or x.get("title", ""),
        })
    seen, uniq = set(), []
    for it in sorted(out, key=lambda i: i["date"]):
        if it["id"] not in seen:
            seen.add(it["id"]); uniq.append(it)
    return uniq


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
         "Only the Apply queue is actionable. Each id is processed once; local state is `~/.grok/agent-city/applied.json`.", "",
         "## Apply queue", ""]
    for it in items:
        L += [f"- **{it['id']}** | size hint: {it['size']} | target: {it['target']} | from: {it['from']}, {it['date']}",
              f"  - change: {it['change']}", f"  - why: {it['why']}"]
    if not items:
        L.append("(empty)")
    L += ["", "## Latest Council verdicts (context; already handled in the city)", ""]
    V = [a for a in activity if a.get("role") == "council" and a.get("verdict")][:5]
    L += [f"- {a.get('date','')} {a.get('size','')} {a['verdict']} {a.get('confidence','?')}/10: {a.get('question','')} Reason: {a.get('reason','')}" for a in V] or ["(none yet)"]
    L += ["", "## Next best steps for the city (context)", ""]
    L += [f"{i}. {t}" for i, t in enumerate(next_steps(), 1)] or ["(none)"]
    L += ["", "## Scout finds for Grok Build (context)", ""]
    F = [f for f in load_json("finds.json", []) if isinstance(f, dict) and f.get("gb")]
    L += [f"- [{f['title']}]({f.get('url','')}): {f.get('why_useful','')}" for f in F] or ["(none yet)"]
    os.makedirs(os.path.join(HERE, "grok-build"), exist_ok=True)
    with open(os.path.join(HERE, "grok-build", "suggestions.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


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


def main():
    data = {
        "generatedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "skills": load_skills(),
        "agents": load_agents(),
        "changelog": load_changelog(),
        "finds": load_finds(),
        "activity": load_activity(),
        "routines": load_routines(),
        "ideals": load_ideals(),
    }
    data["gb"] = [{k: i[k] for k in ("id", "change", "target", "size", "date")} for i in gb_items(data["activity"], data["finds"])]
    write_gb_suggestions(data["activity"], gb_items(data["activity"], data["finds"]), data["generatedAt"])
    out = os.path.join(HERE, "data.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write("// AUTO-GENERATED by build_data.py - do not edit by hand.\n")
        f.write("window.CITY_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"data.js: {len(data['skills'])} skills, {len(data['agents'])} agents, {len(data['changelog'])} changelog entries, {len(data['finds'])} finds, {len(data['activity'])} actions, {len(data['routines'])} routines, {len(data['gb'])} Grok Build items; private.js: {'yes' if write_private() else 'no'}")


if __name__ == "__main__":
    main()
