#!/usr/bin/env python3
"""Regenerate data.js (window.CITY_DATA) from REAL state on this box.

Sources:
  - /home/box/agent-data/workflows/*/SKILL.md   (user-created skills; frontmatter name/description)
  - /home/box/agent-data/agents/*/profile.json  (agent roster: name, title, description, avatar)
  - ./CHANGELOG.md                              (city build history)
  - ./finds.json                                (Market scout finds: [{date,title,url,source,why_useful,status?}])
  - ./activity.json                             (role log, append-only: [{date,session,role,action,details,link?,...}])
  - /home/box/agent-data/agents/*/automations/  (saved routines, shown on the Office board)
  - ./private.json (gitignored) -> ./private.js (gitignored): Courier/Timekeeper notes, local copy only
No data is invented: empty sources stay empty and the city shows an empty state.
Run:  python3 build_data.py
"""
import json, os, re, glob, datetime

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
            "preview": body.strip()[:600],
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
    }
    out = os.path.join(HERE, "data.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write("// AUTO-GENERATED by build_data.py - do not edit by hand.\n")
        f.write("window.CITY_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"data.js: {len(data['skills'])} skills, {len(data['agents'])} agents, {len(data['changelog'])} changelog entries, {len(data['finds'])} finds, {len(data['activity'])} actions, {len(data['routines'])} routines; private.js: {'yes' if write_private() else 'no'}")


if __name__ == "__main__":
    main()
