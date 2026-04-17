#!/usr/bin/env bash
# push-to-github.sh
# Run this from inside the sunday-letter-repo folder on your Mac.
# It will create a public GitHub repo named "sunday-letter" under your account
# and push the initial commit.
#
# Requirements: gh CLI (install with `brew install gh`), authenticated
# (`gh auth login`).

set -e

REPO_NAME="sunday-letter"
DESCRIPTION="A weekly note from your AI agent, about you. Six rules. Default is silence."
VISIBILITY="--public"   # change to --private if you want a private repo

cd "$(dirname "$0")"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found. Install it with: brew install gh"
  echo "Then run: gh auth login"
  echo ""
  echo "OR push manually:"
  echo "  1. Create the repo at https://github.com/new (name it: $REPO_NAME)"
  echo "  2. Run: git remote add origin git@github.com:YOUR_USERNAME/$REPO_NAME.git"
  echo "  3. Run: git branch -M main"
  echo "  4. Run: git push -u origin main"
  exit 1
fi

# Reset git config to whatever the user has on their Mac
git config --local --unset user.email 2>/dev/null || true
git config --local --unset user.name 2>/dev/null || true

# Create the repo and push
gh repo create "$REPO_NAME" $VISIBILITY \
  --description "$DESCRIPTION" \
  --source=. \
  --remote=origin \
  --push

echo ""
echo "Done. View your repo:"
gh repo view --web
