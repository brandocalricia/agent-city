#!/usr/bin/env bash
# Agent City for Grok Build: one-command installer (macOS and Linux, bash 3.2+).
#   curl -fsSL https://raw.githubusercontent.com/brandocalricia/agent-city/main/grok-build/install.sh | bash
# Installs into ~/.grok (or $GROK_HOME):
#   skills/city-council/SKILL.md, skills/city-apply/SKILL.md, rules/40-agent-city.md,
#   hooks/agent-city.json (SessionStart -> agent-city/update.sh), agent-city/ (feed, ideals, prompts, state).
# Idempotent. Anything it would overwrite is copied to ~/.grok/agent-city/backup/<time>/ first.
# Does not touch config.toml, other rules, other skills, or other hooks.
# Uninstall: same command with "bash -s -- --uninstall" (keeps applied.json and backups).
set -eu
RAW="${AGENT_CITY_RAW:-https://raw.githubusercontent.com/brandocalricia/agent-city/main}"
G="${GROK_HOME:-$HOME/.grok}"
D="$G/agent-city"
BK="$D/backup/$(date +%Y%m%d-%H%M%S)"
command -v curl >/dev/null || { echo "agent-city: curl is required" >&2; exit 1; }

OURS="$G/rules/40-agent-city.md $G/skills/city-council/SKILL.md $G/skills/city-apply/SKILL.md $G/hooks/agent-city.json $D/update.sh"

if [ "${1:-}" = "--uninstall" ]; then
  for f in $OURS; do [ -e "$f" ] && { mkdir -p "$BK"; cp "$f" "$BK/$(echo "$f" | sed "s|^$G/||; s|/|__|g")"; rm -f "$f"; }; done
  rmdir "$G/skills/city-council" "$G/skills/city-apply" 2>/dev/null || true
  echo "agent-city: removed the rule, skills, hook, and updater (backup in $BK; state kept in $D). Restart Grok."
  exit 0
fi

BACKED=0
mkdir -p "$D" "$G/rules" "$G/hooks" "$G/skills/city-council" "$G/skills/city-apply"

backup() { # backup <dest> <marker> <repo path>: copy aside if it would change; move it away if it is not ours
  [ -e "$1" ] || return 0
  if curl -fsSL --max-time 20 "$RAW/$3" 2>/dev/null | cmp -s - "$1"; then return 0; fi
  mkdir -p "$BK"; BACKED=1; cp "$1" "$BK/$(echo "$1" | sed "s|^$G/||; s|/|__|g")"
  grep -q "$2" "$1" || rm -f "$1"
}

backup "$G/rules/40-agent-city.md" "Agent City" grok-build/rules/40-agent-city.md
backup "$G/skills/city-council/SKILL.md" "name: city-council" grok-build/skills/city-council/SKILL.md
backup "$G/skills/city-apply/SKILL.md" "name: city-apply" grok-build/skills/city-apply/SKILL.md
backup "$D/update.sh" "Agent City -> Grok Build updater" grok-build/update.sh
backup "$G/hooks/agent-city.json" "agent-city/update.sh" grok-build/hooks/agent-city.json

tmp="$D/update.sh.tmp.$$"
curl -fsSL --max-time 20 "$RAW/grok-build/update.sh" -o "$tmp"
grep -q "Agent City -> Grok Build updater" "$tmp" || { rm -f "$tmp"; echo "agent-city: download failed" >&2; exit 1; }
mv -f "$tmp" "$D/update.sh"; chmod +x "$D/update.sh"

tmp="$G/hooks/agent-city.json.tmp.$$"
curl -fsSL --max-time 20 "$RAW/grok-build/hooks/agent-city.json" -o "$tmp"
grep -q "agent-city/update.sh" "$tmp" || { rm -f "$tmp"; echo "agent-city: download failed" >&2; exit 1; }
mv -f "$tmp" "$G/hooks/agent-city.json"

AGENT_CITY_RAW="$RAW" GROK_HOME="$G" "$D/update.sh" --force

ok=1
for f in $OURS "$D/suggestions.md" "$D/IDEALS.md" "$D/prompts.md" "$D/applied.json" "$D/pending.txt"; do
  [ -s "$f" ] || { echo "agent-city: missing $f" >&2; ok=0; }
done
[ $ok = 1 ] || exit 1
echo "agent-city: installed into $G ($(head -n 1 "$D/pending.txt") suggestion(s) pending)."
[ $BACKED = 1 ] && echo "agent-city: previous files backed up in $BK"
echo "agent-city: restart Grok, then run 'grok inspect' and look for 40-agent-city.md, city-council, city-apply, and the agent-city hook."
