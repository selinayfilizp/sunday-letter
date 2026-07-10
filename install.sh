#!/usr/bin/env bash
# Install the Sunday Letter skill into Claude Code, Codex CLI, or both.
#
# Usage:
#   ./install.sh            # install for every agent it can find
#   ./install.sh claude     # Claude Code only
#   ./install.sh codex      # Codex CLI only
#
# What it does:
#   Claude Code: copies the skill to ~/.claude/skills/sunday-letter
#                and the slash commands to ~/.claude/commands/
#   Codex CLI:   copies the skill to ~/.codex/skills/sunday-letter
#                and the commands to ~/.codex/prompts/ (invoked as /sunday-letter)
#
# Everything is local. Nothing is uploaded anywhere.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$REPO_DIR/skills/sunday-letter"
COMMANDS_SRC="$REPO_DIR/commands"
TARGET="${1:-all}"

if [[ ! -d "$SKILL_SRC" ]]; then
  echo "error: cannot find $SKILL_SRC, run this from a full clone of the repo" >&2
  exit 1
fi

install_claude() {
  local skills_dir="$HOME/.claude/skills"
  local commands_dir="$HOME/.claude/commands"
  mkdir -p "$skills_dir" "$commands_dir"
  rm -rf "$skills_dir/sunday-letter"
  cp -R "$SKILL_SRC" "$skills_dir/sunday-letter"
  cp "$COMMANDS_SRC"/*.md "$commands_dir/"
  echo "Claude Code: installed skill to $skills_dir/sunday-letter"
  echo "Claude Code: installed /sunday-letter and /subscribe-sunday-letter commands"
}

install_codex() {
  local skills_dir="$HOME/.codex/skills"
  local prompts_dir="$HOME/.codex/prompts"
  mkdir -p "$skills_dir" "$prompts_dir"
  rm -rf "$skills_dir/sunday-letter"
  cp -R "$SKILL_SRC" "$skills_dir/sunday-letter"
  cp "$COMMANDS_SRC"/*.md "$prompts_dir/"
  echo "Codex CLI: installed skill to $skills_dir/sunday-letter"
  echo "Codex CLI: installed sunday-letter prompts to $prompts_dir"
}

case "$TARGET" in
  claude)
    install_claude
    ;;
  codex)
    install_codex
    ;;
  all)
    installed=0
    if [[ -d "$HOME/.claude" ]]; then
      install_claude
      installed=1
    fi
    if [[ -d "$HOME/.codex" ]]; then
      install_codex
      installed=1
    fi
    if [[ "$installed" -eq 0 ]]; then
      echo "Neither ~/.claude nor ~/.codex exists." >&2
      echo "Run './install.sh claude' or './install.sh codex' to force one." >&2
      exit 1
    fi
    ;;
  *)
    echo "usage: ./install.sh [claude|codex|all]" >&2
    exit 1
    ;;
esac

cat <<'NEXT'

Next steps:
  1. Start a new agent session so the skill is picked up.
  2. Run /sunday-letter for a letter right now, or
     /subscribe-sunday-letter to pick your weekly day and time.
  3. No native scheduler? Add a cron line (Sunday 6 PM shown):
       Claude Code: 0 18 * * 0 claude -p "/sunday-letter"
       Codex CLI:   0 18 * * 0 codex exec "Use the sunday-letter skill and write this week's letter. Stay silent if nothing meaningful changed."

Default is silence: a letter only ships when something meaningful changed.
NEXT
