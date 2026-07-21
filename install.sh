#!/usr/bin/env bash
# Install the Sunday Letter reference path for Codex, Claude Code, or both.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$REPO_DIR/skills/sunday-letter"
PROMPTS_SRC="$REPO_DIR/commands"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
TARGET="${1:-all}"

if [[ ! -d "$SKILL_SRC" ]]; then
  echo "error: cannot find $SKILL_SRC; install from a full repository clone" >&2
  exit 1
fi

copy_skill() {
  local skills_dir="$1"
  mkdir -p "$skills_dir"
  rm -rf "$skills_dir/sunday-letter"
  cp -R "$SKILL_SRC" "$skills_dir/sunday-letter"
  find "$skills_dir/sunday-letter" -type d -name __pycache__ -prune -exec rm -rf {} +
  find "$skills_dir/sunday-letter" -type f -name '*.pyc' -delete
}

install_codex() {
  copy_skill "$CODEX_HOME/skills"
  mkdir -p "$CODEX_HOME/prompts"
  cp "$PROMPTS_SRC"/*.md "$CODEX_HOME/prompts/"
  echo "Codex: installed skill to $CODEX_HOME/skills/sunday-letter"
  echo "Codex: installed prompts to $CODEX_HOME/prompts"
}

install_claude() {
  copy_skill "$CLAUDE_HOME/skills"
  mkdir -p "$CLAUDE_HOME/commands"
  cp "$PROMPTS_SRC"/*.md "$CLAUDE_HOME/commands/"
  echo "Claude Code: installed skill to $CLAUDE_HOME/skills/sunday-letter"
  echo "Claude Code: installed commands to $CLAUDE_HOME/commands"
  if [[ -d "$CLAUDE_HOME/plugins/cache/sunday-letter" ]]; then
    echo "Claude Code: note, the sunday-letter plugin is also installed via /plugin." >&2
    echo "Claude Code: pick one install method or /sunday-letter may appear twice." >&2
  fi
}

case "$TARGET" in
  codex)
    install_codex
    ;;
  claude)
    install_claude
    ;;
  all)
    installed=0
    if [[ -d "$CODEX_HOME" ]]; then
      install_codex
      installed=1
    fi
    if [[ -d "$CLAUDE_HOME" ]]; then
      install_claude
      installed=1
    fi
    if [[ "$installed" -eq 0 ]]; then
      echo "Neither $CODEX_HOME nor $CLAUDE_HOME exists." >&2
      echo "Run './install.sh codex' or './install.sh claude' to force one." >&2
      exit 1
    fi
    ;;
  *)
    echo "usage: ./install.sh [codex|claude|all]" >&2
    echo "Codex local and Claude Code local are the supported reference paths." >&2
    exit 1
    ;;
esac

cat <<'NEXT'

Next steps:
  1. Start a new agent session so the skill is picked up.
  2. Run /sunday-letter for a local, one-time letter.
  3. Run /subscribe-sunday-letter to configure a weekly local schedule.

Privacy boundary:
  - Collection reads local agent conversation state only (Codex or Claude Code).
  - The default scope is all dated messages in the selected window.
  - Use collector --cwd, --thread-id (Codex), or --session-id (Claude Code)
    filters to narrow the source set.
  - Common credentials are redacted before the transcript bundle is written.
NEXT
