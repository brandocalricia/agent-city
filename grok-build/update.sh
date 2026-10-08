#!/usr/bin/env bash
# Agent City -> Grok Build updater. Runs from the SessionStart hook (~/.grok/hooks/agent-city.json).
# Refreshes the city's skills, rule, ideals, prompts, and suggestions feed, then writes pending.txt.
# Fail-open and quiet: always exits 0. Downloads at most once per 30 minutes (use --force to skip that).
# Only overwrites files that are missing or already belong to Agent City; never touches applied.json.
set -u
RAW="${AGENT_CITY_RAW:-https://raw.githubusercontent.com/brandocalricia/agent-city/main}"
G="${GROK_HOME:-$HOME/.grok}"
D="$G/agent-city"
mkdir -p "$D" "$G/rules" "$G/skills/city-council" "$G/skills/city-apply" 2>/dev/null || exit 0

fetch() { # fetch <repo path> <dest> <marker>
  local tmp="$2.tmp.$$"
  if curl -fsSL --max-time 8 "$RAW/$1" -o "$tmp" 2>/dev/null && grep -q "$3" "$tmp"; then
    if [ ! -e "$2" ] || grep -q "$3" "$2"; then
      cmp -s "$tmp" "$2" || mv -f "$tmp" "$2"
    fi
  fi
  rm -f "$tmp"
}

now=$(date +%s); last=$(cat "$D/.last-update" 2>/dev/null || echo 0)
case "$last" in ''|*[!0-9]*) last=0 ;; esac
if [ "${1:-}" = "--force" ] || [ $((now - last)) -ge 1800 ]; then
  fetch grok-build/suggestions.md "$D/suggestions.md" "Agent City"
  fetch grok-build/prompts.md "$D/prompts.md" "Agent City"
  fetch IDEALS.md "$D/IDEALS.md" "Agent City - Ideals"
  fetch grok-build/skills/city-council/SKILL.md "$G/skills/city-council/SKILL.md" "name: city-council"
  fetch grok-build/skills/city-apply/SKILL.md "$G/skills/city-apply/SKILL.md" "name: city-apply"
  fetch grok-build/rules/40-agent-city.md "$G/rules/40-agent-city.md" "Agent City"
  fetch grok-build/update.sh "$D/update.sh" "Agent City -> Grok Build updater"
  chmod +x "$D/update.sh" 2>/dev/null
  echo "$now" > "$D/.last-update"
fi

# pending.txt: line 1 = number of Apply-queue ids not yet in applied.json, then the ids.
[ -f "$D/applied.json" ] || echo '{}' > "$D/applied.json"
ids=$(awk '/^## /{q=($0 ~ /^## Apply queue/)} q' "$D/suggestions.md" 2>/dev/null | grep -o 'AC-[0-9a-f]\{8\}' | awk '!s[$0]++')
pend=""; n=0
for id in $ids; do
  grep -q "\"$id\"" "$D/applied.json" 2>/dev/null || { pend="$pend$id
"; n=$((n + 1)); }
done
printf '%s\n%s' "$n" "$pend" > "$D/pending.txt"
exit 0
