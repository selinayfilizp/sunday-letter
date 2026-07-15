# The Sunday Letter

A private local weekly note grounded in recent Codex conversations: what the
agent actually completed, what changed in its model of you, what it stopped
believing, and one question worth sitting with.

The default is silence. If the selected sources contain no meaningful delta,
the runtime records a skipped week and writes no letter.

## Supported reference path

Version 0.3 supports one path end to end: **local Codex state → dated and
redacted context bundle → canonical signals → validated HTML → atomic ledger →
private local archive**.

Claude, Cowork, ChatGPT, email delivery, messaging delivery, and cross-agent
profile export are not supported runtime paths yet. The editorial contract may
eventually be portable; this release deliberately makes fewer promises.

## Install

Clone the repository and install the skill and prompts into Codex:

```bash
git clone https://github.com/selinayfilizp/sunday-letter.git
cd sunday-letter
./install.sh
```

Alternatively, download `docs/sunday-letter-codex.plugin` from the published
site and import the local Codex bundle.

Everything uses the Python standard library. No package installation, model API
key, analytics service, or delivery provider is required.

## Run

Start a new Codex session after installation, then run:

```text
/sunday-letter
```

The skill performs this exact pipeline:

1. Checks `~/sunday-letter/ledger.json` and stops if paused.
2. Collects dated local Codex messages from the last seven days.
3. Applies optional `--cwd` or `--thread-id` source filters.
4. Redacts common credential shapes and writes an owner-readable transcript
   bundle.
5. Extracts JSON matching
   `skills/sunday-letter/references/signals.schema.json`.
6. Verifies the source scope, counts, and window against the collector bundle.
7. Applies the delta gate before rendering.
8. Sanitizes rich text to `<strong>` and `<em>`, then adds a restrictive
   Content Security Policy.
9. Writes the HTML letter and validated signals record atomically.
10. Updates the ledger atomically and rebuilds `~/sunday-letter/index.html`.

The runtime owns the letter number. It rejects unmeasured legacy fields such as
confidence percentages, hours saved, and exports.

## Inspect the source bundle

Run the collector directly to see exactly what a letter may use:

```bash
python3 skills/sunday-letter/scripts/collect_codex_context.py \
  --days 7 \
  --limit 80 \
  --per-message-limit 3000 \
  --out codex-weekly-context.md
```

Narrow collection to one project with:

```bash
--cwd /absolute/path/to/project
```

The seven-day boundary is applied to every message, not merely to the thread's
last-updated time. Undated messages are excluded by default.

## Preview the renderer

Preview mode validates and renders without changing your ledger:

```bash
python3 generate_letter.py \
  --signals skills/sunday-letter/references/example-signals.json \
  --preview \
  --out preview.html
```

Skip payloads are never rendered, including in preview mode.

## Private archive actions

Letters, validated signal records, the ledger, and the generated archive stay
under `~/sunday-letter/` by default. Archive and per-letter export links work as
local files. Pause, Resume, Delete, and full-archive Export are available through
the loopback-only archive server:

```bash
python3 manage_archive.py --root ~/sunday-letter serve
```

Open `http://127.0.0.1:8765/`. The server binds to loopback by default and does
not expose the archive to the network.

CLI equivalents are also available:

```bash
python3 manage_archive.py --root ~/sunday-letter status
python3 manage_archive.py --root ~/sunday-letter pause
python3 manage_archive.py --root ~/sunday-letter resume
python3 manage_archive.py --root ~/sunday-letter export --out sunday-letter-export.zip
python3 manage_archive.py --root ~/sunday-letter delete letters/2026-07-12-letter-01.html
```

Deleting this archive removes Sunday Letter artifacts only. It does **not**
delete Codex's underlying conversation history or any other Codex memory.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The suite covers schema validation, delta enforcement, numbering, ledger
updates, HTML safety, per-message date filtering, redaction, source selection,
archive actions, path traversal, exports, and isolated installation.

## Repository layout

```text
.
├── .codex-plugin/plugin.json
├── commands/
│   ├── sunday-letter.md
│   └── subscribe-sunday-letter.md
├── skills/sunday-letter/
│   ├── SKILL.md
│   ├── references/
│   │   ├── signals.schema.json
│   │   ├── schema.md
│   │   ├── example-signals.json
│   │   └── letter.css
│   └── scripts/
│       ├── core.py
│       ├── collect_codex_context.py
│       ├── generate_letter.py
│       └── manage_archive.py
├── tests/
├── generate_letter.py
├── manage_archive.py
└── install.sh
```

## License

MIT.
