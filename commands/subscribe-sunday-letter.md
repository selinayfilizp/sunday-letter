---
description: Configure or update a weekly local Sunday Letter schedule (Codex or Claude Code).
---

# /subscribe-sunday-letter

Configure one recurring task named `sunday-letter` in the host agent. Ask for weekday,
wall-clock time, and optional IANA timezone only when the user has not already
provided them. Sunday at 6:00 PM in the scheduler's local timezone is the
default.

The scheduled prompt must say:

> Invoke the installed sunday-letter skill. Use dated local sources,
> apply its delta gate, and update the private local archive. Stay silent when
> there is no meaningful delta.

If a task named `sunday-letter` already exists, update it; do not create a
duplicate. Use the host's native scheduling capability when available.

For CLI installations without native scheduling, show the proposed cron line
and obtain confirmation before changing the user's crontab:

```cron
# Codex CLI
0 18 * * 0 codex exec "Use the installed sunday-letter skill and run the supported local workflow."
# Claude Code
0 18 * * 0 claude -p "/sunday-letter"
```

Explain that cron uses the machine's local clock unless the environment sets a
timezone and that the machine must be awake. Do not claim the plugin watches in
the background; each scheduled invocation performs a bounded local collection.

Pause and resume the content pipeline independently of the schedule with:

```bash
# Codex
python3 "${CODEX_HOME:-$HOME/.codex}/skills/sunday-letter/scripts/manage_archive.py" --root "$HOME/sunday-letter" pause
python3 "${CODEX_HOME:-$HOME/.codex}/skills/sunday-letter/scripts/manage_archive.py" --root "$HOME/sunday-letter" resume

# Claude Code
python3 "${CLAUDE_HOME:-$HOME/.claude}/skills/sunday-letter/scripts/manage_archive.py" --root "$HOME/sunday-letter" pause
python3 "${CLAUDE_HOME:-$HOME/.claude}/skills/sunday-letter/scripts/manage_archive.py" --root "$HOME/sunday-letter" resume
```

When finished, restate the exact schedule, source scope, and local archive path.
