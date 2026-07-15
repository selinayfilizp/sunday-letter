#!/usr/bin/env bash
# Install the supported Codex-local Sunday Letter reference path.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$REPO_DIR/skills/sunday-letter"
PROMPTS_SRC="$REPO_DIR/commands"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SKILLS_DIR="$CODEX_HOME/skills"
PROMPTS_DIR="$CODEX_HOME/prompts"
TARGET="${1:-codex}"

if [[ "$TARGET" != "codex" ]]; then
  echo "usage: ./install.sh [codex]" >&2
  echo "Codex local usage is the only supported reference path in v0.3." >&2
  exit 1
fi

if [[ ! -d "$SKILL_SRC" ]]; then
  echo "error: cannot find $SKILL_SRC; install from a full repository clone" >&2
  exit 1
fi

mkdir -p "$SKILLS_DIR" "$PROMPTS_DIR"
rm -rf "$SKILLS_DIR/sunday-letter"
cp -R "$SKILL_SRC" "$SKILLS_DIR/sunday-letter"
find "$SKILLS_DIR/sunday-letter" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$SKILLS_DIR/sunday-letter" -type f -name '*.pyc' -delete
cp "$PROMPTS_SRC"/*.md "$PROMPTS_DIR/"

echo "Codex: installed skill to $SKILLS_DIR/sunday-letter"
echo "Codex: installed prompts to $PROMPTS_DIR"

cat <<'NEXT'

Next steps:
  1. Start a new Codex session so the skill is picked up.
  2. Run /sunday-letter for a local, one-time letter.
  3. Run /subscribe-sunday-letter to configure a weekly local schedule.

Privacy boundary:
  - Collection reads local Codex conversation state only.
  - The default scope is all dated Codex messages in the selected window.
  - Use collector --cwd or --thread-id filters to narrow the source set.
  - Common credentials are redacted before the transcript bundle is written.
NEXT
