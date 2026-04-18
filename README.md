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

### Cowork (Claude desktop)

Download `docs/sunday-letter.plugin` and drop it into Cowork.

### Claude Code

```bash
/plugin install sunday-letter
```

### Any other AI agent (ChatGPT, Cursor, Gemini, Claude API, etc.)

The Sunday Letter is a contract, not a runtime. To use it with any agent:

1. Drop `skills/sunday-letter/references/system-prompt.md` into your agent's instructions.
2. Hand the agent `skills/sunday-letter/references/schema.md` so it knows the JSON shape.
3. Render the JSON output through `template.html` with any Jinja-compatible engine.

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
├── commands/                      slash commands (/sunday-letter, /subscribe-sunday-letter)
├── skills/sunday-letter/
│   ├── SKILL.md                   the agent's instructions
│   ├── scripts/generate_letter.py the renderer
│   └── references/
│       ├── template.html          the Archive design template
│       ├── system-prompt.md       portable agent prompt for any LLM
│       ├── schema.md              JSON schema for weekly signals
│       ├── design-principles.md   the design contract
│       ├── example-signals.json   complete worked example (Teddy, cheesemonger)
│       └── schedule-config.example.json  weekly slot (day, time, tz, cron)
├── docs/                          static site (landing page, sample letter, install page)
├── generate_letter.py             top-level renderer for direct Python use
├── template.html                  top-level template
└── week_signals.example.json      example weekly signals
```

## License

MIT.
