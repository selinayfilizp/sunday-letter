# The Sunday Letter

A weekly note from your AI agent, about you. What it did for you. What it learned. What it stopped believing. One question worth sitting with. Kept as a running archive, not a letter you throw away.

## What this is

The Sunday Letter is a portable contract for AI agents. Once a week, at a **day and time you configure** (Sunday evening is the default story, not a hard requirement), the agent files a short, structured letter. Default is silence: if nothing meaningful changed, no letter ships.

After install, run `/subscribe-sunday-letter` to pick **weekday, wall-clock time, and optional IANA timezone**; see `commands/subscribe-sunday-letter.md` and `skills/sunday-letter/references/schedule-config.example.json`.

Every letter obeys six rules:

1. Consequences first, what the agent actually did for you.
2. Epistemic honesty, observations are labeled `firm`, `soft`, or `guess`. No fake percentages.
3. Provenance on every claim, dated paraphrased quotes from real conversations.
4. Default is silence, no delta, no letter.
5. Retire something, visible strikethrough of beliefs the agent used to hold.
6. One question, not a survey.

## Install

### Claude Code (plugin, recommended)

Inside Claude Code:

```
/plugin marketplace add selinayfilizp/sunday-letter
/plugin install sunday-letter@sunday-letter
```

Then run `/sunday-letter` for a letter now, or `/subscribe-sunday-letter` to pick your weekly slot.

### Claude Code or Codex CLI (one script)

```bash
git clone https://github.com/selinayfilizp/sunday-letter.git
cd sunday-letter
./install.sh          # installs for every agent it finds
./install.sh claude   # or just Claude Code
./install.sh codex    # or just Codex
```

The script copies the skill into `~/.claude/skills/` and/or `~/.codex/skills/`, and the slash commands into `~/.claude/commands/` and/or `~/.codex/prompts/`. Everything stays local.

### Codex (manual)

Codex reads Agent Skills from `~/.codex/skills/` (personal) or `.codex/skills/` (project). The SKILL.md format is portable, so copying is the whole install:

```bash
mkdir -p ~/.codex/skills
cp -R skills/sunday-letter ~/.codex/skills/
```

The skill's Codex path uses `scripts/collect_codex_context.py`, a local seven-day history collector. It reads Codex state under `~/.codex` and writes a Markdown transcript bundle; it does not upload transcripts anywhere. Run it directly if you want to see what the letter sees:

```bash
python3 skills/sunday-letter/scripts/collect_codex_context.py --days 7 --out codex-weekly-context.md
```

Claude Code has the same thing in `scripts/collect_claude_context.py`, reading `~/.claude/projects`.

### Cowork (Claude desktop)

Download `docs/sunday-letter.plugin` and drop it into Cowork. Codex Desktop users can try `docs/sunday-letter-codex.plugin` the same way.

### Any other AI agent (ChatGPT, Cursor, Gemini, Claude API, etc.)

The Sunday Letter is a contract, not a runtime. To use it with any agent:

1. Drop `skills/sunday-letter/references/system-prompt.md` into your agent's instructions.
2. Hand the agent `skills/sunday-letter/references/schema.md` so it knows the JSON shape.
3. Render the JSON output through `template.html` with any Jinja-compatible engine.

## Make it a weekly routine

Two ways, pick one:

**Inside the agent.** Run `/subscribe-sunday-letter` and pick a day, time, and optional timezone. On hosts with a native scheduler the command creates the recurring task for you.

**Plain cron (works anywhere).** Add one line with `crontab -e` (Sunday 6 PM shown, adjust the last two fields for your slot):

```cron
# Claude Code
0 18 * * 0 claude -p "/sunday-letter" >> ~/sunday-letter/cron.log 2>&1

# Codex CLI
0 18 * * 0 codex exec "Use the sunday-letter skill and write this week's letter. Stay silent if nothing meaningful changed." >> ~/sunday-letter/cron.log 2>&1
```

Either way, letters land in `~/sunday-letter/letters/` and the running ledger (letter number, preferences, retired beliefs) lives at `~/sunday-letter/ledger.json`. Silent weeks are recorded in the ledger but ship nothing.

## Run from Python

```bash
python3 generate_letter.py --signals week_signals.example.json --out my-letter.html
```

Open `my-letter.html` in a browser. That's it.

## Live demo

[Landing page and sample letter](docs/index.html) (also published via GitHub Pages from `/docs`).

## Repo layout

```
.
├── .claude-plugin/plugin.json     plugin manifest
├── .claude-plugin/marketplace.json  marketplace registry (enables /plugin marketplace add)
├── .codex-plugin/plugin.json      Codex plugin manifest
├── install.sh                     one-command install for Claude Code and Codex CLI
├── commands/                      slash commands (/sunday-letter, /subscribe-sunday-letter)
├── skills/sunday-letter/
│   ├── SKILL.md                   the agent's instructions
│   ├── scripts/generate_letter.py the renderer
│   ├── scripts/collect_claude_context.py Claude Code seven-day history collector
│   ├── scripts/collect_codex_context.py Codex seven-day history collector
│   └── references/
│       ├── template.html          the Archive design template
│       ├── system-prompt.md       portable agent prompt for any LLM
│       ├── schema.md              JSON schema for weekly signals
│       ├── design-principles.md   the design contract
│       ├── example-signals.json   complete worked example (Teddy, cheesemonger)
│       └── schedule-config.example.json  weekly slot (day, time, tz, cron)
├── docs/                          static site (landing page, sample letter, install/Codex pages)
├── generate_letter.py             top-level renderer for direct Python use
├── template.html                  top-level template
└── week_signals.example.json      example weekly signals
```

## License

MIT.
