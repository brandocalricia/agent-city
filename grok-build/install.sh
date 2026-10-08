#!/usr/bin/env bash
# Agent City for Grok Build: one-command installer (macOS and Linux, bash 3.2+).
#   curl -fsSL https://raw.githubusercontent.com/brandocalricia/agent-city/main/grok-build/install.sh | bash
# Installs into ~/.grok (or $GROK_HOME):
#   rules/40-agent-city.md, skills/city-council, skills/city-apply, skills/bot-link, hooks/agent-city.json (SessionStart),
#   agent-city/ (update.sh, city_apply.py, comms.py, suggestions.md, IDEALS.md, prompts.md, pending.txt, applied.json).
# Every file is verified against grok-build/manifest.txt (sha256) before it replaces anything.
# Idempotent. Files that would change are copied to ~/.grok/agent-city/backup/<time>/ first; a file at one of
# these paths that is not Agent City's is backed up and then replaced. config.toml and other rules, skills,
# and hooks are never touched. Uninstall: ... | bash -s -- --uninstall (keeps applied.json/log, backups, and the
# message-link state and webhook config).
# Everything runs inside main, so a truncated download executes nothing.
main() {
  set -eu
  RAW="${AGENT_CITY_RAW:-https://raw.githubusercontent.com/brandocalricia/agent-city/main}"
  G="${GROK_HOME:-$HOME/.grok}"
  D="$G/agent-city"
  BK="$D/backup/$(date +%Y%m%d-%H%M%S)"
  command -v curl >/dev/null || { echo "agent-city: curl is required" >&2; return 1; }
  FILES="rules/40-agent-city.md skills/city-council/SKILL.md skills/city-apply/SKILL.md skills/bot-link/SKILL.md hooks/agent-city.json agent-city/update.sh agent-city/city_apply.py agent-city/comms.py"

  if [ "${1:-}" = "--uninstall" ]; then
    for f in $FILES; do
      if [ -e "$G/$f" ]; then mkdir -p "$BK"; cp "$G/$f" "$BK/$(echo "$f" | sed 's|/|__|g')"; rm -f "$G/$f"; fi
    done
    rmdir "$G/skills/city-council" "$G/skills/city-apply" "$G/skills/bot-link" 2>/dev/null || true
    printf '0\nrepos: \n' > "$D/pending.txt" 2>/dev/null || true
    echo "agent-city: removed the rule, skills, hook, and scripts (state kept in $D). Restart Grok."
    return 0
  fi

  mkdir -p "$D"
  tmpd=$(mktemp -d "${TMPDIR:-/tmp}/agent-city.XXXXXX")
  trap 'rm -rf "$tmpd"' EXIT
  curl -fsS --connect-timeout 5 --max-time 20 "$RAW/grok-build/manifest.txt" -o "$tmpd/manifest.txt" \
    || { echo "agent-city: could not download the manifest (offline?). Nothing changed." >&2; return 1; }
  [ "$(tail -n 1 "$tmpd/manifest.txt")" = "end" ] || { echo "agent-city: incomplete manifest. Nothing changed." >&2; return 1; }

  # 1. download and verify everything first; touch nothing until all files check out
  for pair in "rules/40-agent-city.md|grok-build/rules/40-agent-city.md" "skills/city-council/SKILL.md|grok-build/skills/city-council/SKILL.md" \
              "skills/city-apply/SKILL.md|grok-build/skills/city-apply/SKILL.md" "skills/bot-link/SKILL.md|grok-build/comms/bot-link/SKILL.md" \
              "hooks/agent-city.json|grok-build/hooks/agent-city.json" "agent-city/update.sh|grok-build/update.sh" \
              "agent-city/city_apply.py|grok-build/city_apply.py" "agent-city/comms.py|grok-build/comms/comms.py"; do
    dst=${pair%%|*}; src=${pair#*|}
    want=$(awk -v p="$src" '$2 == p { print $1 }' "$tmpd/manifest.txt")
    out="$tmpd/$(echo "$dst" | sed 's|/|__|g')"
    curl -fsS --connect-timeout 5 --max-time 20 "$RAW/$src" -o "$out" || { echo "agent-city: download failed: $src. Nothing changed." >&2; return 1; }
    [ -n "$want" ] && [ "$(sha "$out")" = "$want" ] || { echo "agent-city: checksum mismatch: $src. Nothing changed." >&2; return 1; }
  done

  # 2. back up anything that would change, then replace atomically
  backed=0
  for f in $FILES; do
    new="$tmpd/$(echo "$f" | sed 's|/|__|g')"
    if [ -e "$G/$f" ] && ! cmp -s "$new" "$G/$f"; then
      mkdir -p "$BK"; cp "$G/$f" "$BK/$(echo "$f" | sed 's|/|__|g')"; backed=1
    fi
    mkdir -p "$(dirname "$G/$f")"
    cp "$new" "$G/$f.tmp.$$" && mv -f "$G/$f.tmp.$$" "$G/$f"
  done
  chmod +x "$D/update.sh" "$D/city_apply.py" "$D/comms.py"
  [ -f "$D/applied.json" ] || echo '{}' > "$D/applied.json"

  # 3. feed, ideals, prompts, and pending.txt through the normal updater
  AGENT_CITY_RAW="$RAW" GROK_HOME="$G" bash "$D/update.sh" --force

  for f in $FILES; do [ -s "$G/$f" ] || { echo "agent-city: missing $G/$f" >&2; return 1; }; done
  for f in suggestions.md IDEALS.md prompts.md pending.txt; do [ -s "$D/$f" ] || { echo "agent-city: missing $D/$f (feed download failed; it retries next session)" >&2; }; done
  echo "agent-city: installed into $G ($(head -n 1 "$D/pending.txt" 2>/dev/null || echo 0) suggestion(s) pending)."
  [ $backed = 1 ] && echo "agent-city: previous versions backed up in $BK"
  command -v python3 >/dev/null 2>&1 || echo "agent-city: python3 not found; city-apply and the message link need it."
  if ! command -v gh >/dev/null 2>&1; then
    echo "agent-city: message link: GitHub CLI not found. Install it (brew install gh), then run: gh auth login"
  elif ! gh auth token >/dev/null 2>&1; then
    echo "agent-city: message link: gh is not signed in. Run: gh auth login"
  fi
  [ -f "$D/bot-webhook.env" ] || echo "agent-city: message link: webhook not set up yet (optional): paste URL+key from the Bot panel into: python3 $D/comms.py setup"
  echo "agent-city: restart Grok, then run 'grok inspect' and look for 40-agent-city.md, city-council, city-apply, bot-link, and the agent-city hook."
  return 0
}

sha() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

main "$@"
