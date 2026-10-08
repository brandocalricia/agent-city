#!/usr/bin/env bash
# Agent City -> Grok Build updater. Runs from the SessionStart hook (~/.grok/hooks/agent-city.json).
# Pulls grok-build/manifest.txt (sha256 per file), downloads only files whose hash changed, verifies each
# download against the manifest, and replaces it atomically. Then refreshes pending.txt via city_apply.py.
# Fail-open and quiet: always exits 0. At most one download pass per 30 minutes (--force skips that).
# Never overwrites a file that is not Agent City's, never touches applied.json / applied.log.
# Kill switch: touch ~/.grok/agent-city/off (no updates, no pending). Pin code: touch ~/.grok/agent-city/pin
# (feed, ideals, and prompts still update; skills, rule, hook, and scripts stay as they are).
# Bash 3.2 compatible (macOS). Wrapped in main so a truncated download never runs half a script.
main() {
  set -u
  RAW="${AGENT_CITY_RAW:-https://raw.githubusercontent.com/brandocalricia/agent-city/main}"
  G="${GROK_HOME:-$HOME/.grok}"
  D="$G/agent-city"
  mkdir -p "$D" 2>/dev/null || return 0
  if [ -e "$D/off" ]; then printf '0\nrepos: \n' > "$D/pending.txt" 2>/dev/null; return 0; fi

  # one updater at a time; a lock older than 2 minutes is stale (crashed or killed by the hook timeout)
  if ! mkdir "$D/.update.lock" 2>/dev/null; then
    if [ -n "$(find "$D/.update.lock" -maxdepth 0 -mmin +2 2>/dev/null)" ]; then
      rmdir "$D/.update.lock" 2>/dev/null; mkdir "$D/.update.lock" 2>/dev/null || return 0
    else
      return 0
    fi
  fi
  trap 'rmdir "$D/.update.lock" 2>/dev/null' EXIT

  now=$(date +%s); last=$(cat "$D/.last-update" 2>/dev/null || echo 0)
  case "$last" in ''|*[!0-9]*) last=0 ;; esac
  if [ "${1:-}" = "--force" ] || [ $((now - last)) -ge 1800 ] || [ "$last" -gt "$now" ]; then
    sync_files
    echo "$now" > "$D/.last-update"
  fi
  if command -v python3 >/dev/null 2>&1 && [ -f "$D/city_apply.py" ]; then
    python3 "$D/city_apply.py" status --write-pending >/dev/null 2>&1 || printf '0\nrepos: \n' > "$D/pending.txt"
  else
    printf '0\nrepos: \n' > "$D/pending.txt"
  fi
  return 0
}

sha() { # sha256 of a file, macOS or Linux
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

# repo path | destination | marker that proves the destination belongs to Agent City | code (pinnable)
targets() {
  cat <<T
grok-build/suggestions.md|$D/suggestions.md|Agent City|0
grok-build/prompts.md|$D/prompts.md|Agent City|0
IDEALS.md|$D/IDEALS.md|Agent City - Ideals|0
grok-build/skills/city-council/SKILL.md|$G/skills/city-council/SKILL.md|name: city-council|1
grok-build/skills/city-apply/SKILL.md|$G/skills/city-apply/SKILL.md|name: city-apply|1
grok-build/rules/40-agent-city.md|$G/rules/40-agent-city.md|Agent City|1
grok-build/hooks/agent-city.json|$G/hooks/agent-city.json|agent-city/update.sh|1
grok-build/city_apply.py|$D/city_apply.py|Agent City -> Grok Build: deterministic helper|1
grok-build/comms/bot-link/SKILL.md|$G/skills/bot-link/SKILL.md|name: bot-link|1
grok-build/comms/comms.py|$D/comms.py|Agent City <-> Grok Build message link|1
grok-build/update.sh|$D/update.sh|Agent City -> Grok Build updater|1
T
}

sync_files() {
  man="$D/.manifest.tmp.$$"
  curl -fsS --connect-timeout 3 --max-time 6 "$RAW/grok-build/manifest.txt" -o "$man" 2>/dev/null || { rm -f "$man"; return 0; }
  # a complete manifest ends with the line "end"; anything else is a partial or wrong download
  [ "$(tail -n 1 "$man" 2>/dev/null)" = "end" ] || { rm -f "$man"; return 0; }
  deadline=$(( $(date +%s) + 12 ))   # stay well inside the hook's 20 s timeout; the rest waits for next time
  targets | while IFS='|' read -r src dest marker code; do
    [ "$(date +%s)" -lt "$deadline" ] || break
    want=$(awk -v p="$src" '$2 == p && $1 ~ /^[0-9a-f]+$/ && length($1) == 64 { print $1 }' "$man")
    [ -n "$want" ] || continue
    [ "$code" = "1" ] && [ -e "$D/pin" ] && continue
    [ -f "$dest" ] && [ "$(sha "$dest")" = "$want" ] && continue
    if [ -e "$dest" ] && ! grep -qF "$marker" "$dest" 2>/dev/null; then continue; fi   # not ours: never clobber
    mkdir -p "$(dirname "$dest")" 2>/dev/null || continue
    tmp="$dest.tmp.$$"
    if curl -fsS --connect-timeout 3 --max-time 8 "$RAW/$src" -o "$tmp" 2>/dev/null \
       && [ "$(sha "$tmp")" = "$want" ] && grep -qF "$marker" "$tmp"; then
      case "$dest" in *.sh|*.py) chmod +x "$tmp" ;; esac
      old=""; [ -f "$dest" ] && old=$(sha "$dest")
      mv -f "$tmp" "$dest" && [ "$code" = "1" ] && echo "$(date +%Y-%m-%dT%H:%M:%S) $src ${old:-new} -> $want" >> "$D/updates.log"
    fi
    rm -f "$tmp"
  done
  rm -f "$man"
}

main "$@"
exit 0
