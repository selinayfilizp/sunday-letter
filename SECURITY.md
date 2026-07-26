# Security and local-data boundary

The Sunday Letter is a local tool. It does not include analytics, remote sync,
an API client, or a delivery integration.

## What it reads

- Codex collection reads the local state database at
  `${CODEX_HOME:-~/.codex}/state_5.sqlite`.
- Claude Code collection reads local JSONL transcripts under
  `${CLAUDE_HOME:-~/.claude}/projects`.
- Date, working-directory, thread, and session filters can narrow that source
  set. Undated messages are excluded by default.

Collectors include user and assistant text needed for the selected window.
Claude Code tool-use, tool-result, and thinking blocks are excluded. Collection
does not grant the project access to Cowork, ChatGPT, Gemini, email, or messaging
history.

## What it writes

By default, the runtime creates an owner-readable archive under
`~/sunday-letter/` containing:

- rendered HTML letters;
- validated signal records;
- `ledger.json`; and
- the generated local archive index.

Temporary context and signal inputs live under `~/sunday-letter/.working/` and
the skill instructs the host to remove them after a successful or skipped run.
The archive server binds to `127.0.0.1` by default. Every request must carry
a loopback Host header, so DNS rebinding pages cannot read the archive, and
state-changing actions additionally reject cross-origin and cross-site
requests.

## Redaction and rendering

Collectors redact common credential shapes before writing a context bundle.
This is defense in depth, not a guarantee that every secret format will be
recognized. Use source filters when a project may contain sensitive material.

Rendered rich text allows only `<strong>` and `<em>`. Other markup is escaped,
and generated pages include a restrictive Content Security Policy.

## Deletion

Archive Delete removes Sunday Letter HTML and signal records and updates its
ledger. It does not delete underlying Codex or Claude Code conversation history
or unrelated agent memory. Those remain controlled by the host application.

## Reporting a vulnerability

Please use GitHub's private security-advisory flow for this repository. Include
the affected version, a minimal reproduction, and the local platform. Do not
attach real conversation transcripts or credentials.
