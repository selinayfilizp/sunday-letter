---
name: sunday-letter
description: Write a weekly Sunday Letter, a reflective note from the agent to the user that reports what it did that week, what it learned about them, what it stopped believing, and one question worth sitting with. Use when the user says "write my Sunday letter", "it's Sunday, reflect on the week", "what did you learn about me this week", "send me my weekly letter", "do a weekly reflection", or when a scheduled task named "sunday-letter" is firing. Produces a single rendered HTML note, Archive aesthetic: warm cream paper, Inter + JetBrains Mono, numbered sections, visible calibration badges (FIRM / SOFT / GUESS), three ×'s at the close.
---

# Sunday Letter

Write a weekly letter from the agent to the user. The letter is not a dashboard and not a notification, it is a piece of correspondence. Default is silence; a letter ships only when something meaningful changed.

## When to run this skill

- The user asks for a Sunday Letter (by name, paraphrase, or scheduled trigger).
- A scheduled task named `sunday-letter` or similar is invoking you.
- The user asks "what did you learn about me this week" or "what changed in how you think about me".

## The contract (non-negotiable)

Every letter obeys six rules. A letter that violates any of these should not ship.

1. **Consequences first.** Open with what you actually did for the user this week. Two to four concrete actions, drafts written, things filtered, decisions taken on their behalf. If you took no actions, say so and skip the section.
2. **Epistemic honesty.** Hedge every observation in natural language, never fake percentages. Use `firm` only with 5+ consistent signals; `soft` with 2–4; `guess` for new patterns.
3. **Provenance on everything.** Each observation needs a real paraphrased quote from an actual conversation this week, plus a date.
4. **Default silence.** If nothing meaningful changed vs. last week, do not ship. Return the skip payload (see below) and stop.
5. **Retire something.** Monthly or more often, cross out a belief you used to hold about the user and replace it with what you hold now. Be honest about having been wrong.
6. **One question, not two.** One generative, specific question tied to something the user is actually wrestling with. No philosophical abstractions.

Read `references/design-principles.md` for the reasoning behind these rules and the four critics (Elon, Karpathy, Ben, Amanda) they came from.

## Workflow

### Step 1, Gather the week's signal

Look back over the user's last 7 days of conversations with you. This must use real conversation history, not just the current thread, whenever the host makes history available.

Also read the ledger at `~/sunday-letter/ledger.json` if it exists. It carries the letter number, the running preference list, and previously retired beliefs from week to week. If there is no ledger yet, this is letter number 1.

**In Claude Code:** run the local collector before extracting signals:

```bash
python3 scripts/collect_claude_context.py --days 7 --out claude-weekly-context.md
```

Then read `claude-weekly-context.md` and treat it as the source transcript bundle for the week. The collector reads local session transcripts under `~/.claude/projects`; it does not call a network service.

**In Codex (CLI or Desktop):** run the local collector before extracting signals:

```bash
python3 scripts/collect_codex_context.py --days 7 --out codex-weekly-context.md
```

Then read `codex-weekly-context.md` and treat it as the source transcript bundle for the week. The collector reads the user's local Codex thread database and rollout JSONL files from `~/.codex`; it does not call a network service.

**In Cowork or any other host:** use the available conversation history or scheduled-task context tool. If the host does not expose a history API, say that clearly and do not pretend to have seven days of context.

You need enough material to answer:

- What did I do for them this week (drafts, filters, commits, builds, documents, declines, shortlists)?
- What did we decide this week?
- What tasks or open loops still need to be carried forward?
- What patterns repeated? What did they engage with at length? What did they dismiss quickly?
- Where did my predictions about their preferences turn out wrong?
- What's new this week that I didn't know last week?

If no conversation-history source is available, rely on what's in context and note the limitation honestly in the letter. Do not hallucinate transcript content.

### Step 2, Extract structured signals

Write a JSON object matching the schema in `references/schema.md`. The structure is:

```
name, letter_number, date, calibration_pct, total_prefs, hours_saved,
hero_lede, consequences[], decisions[], open_tasks[], observations[], retired[], gap,
becoming, question, preferences[], daily_shape[]
```

A complete working example is at `references/example-signals.json`. Mirror its shape exactly.

### Step 3, Apply the delta gate

If `consequences` is empty AND `observations` is empty AND nothing would retire this week, do not ship. Return:

```json
{"skip": true, "reason": "no meaningful delta this week"}
```

Tell the user briefly: "I stayed silent this week, nothing meaningful changed." Then stop. Do not render a letter.

### Step 4, Render the letter

You have two paths:

**Path A (recommended in Cowork):** Write the HTML directly, using `references/template.html` as a visual reference for the aesthetic. Substitute the signal values into the template's structure. Save the output to the working directory and then copy to the user's outputs folder so they can view it.

**Path B (if Python is available):** Run `scripts/generate_letter.py --signals <your_signals.json> --out letter.html` to render via Jinja. This requires `jinja2` to be installed.

The renderer has a dependency-free fallback in Codex, so `jinja2` is optional for offline preview and scheduled local runs. Either path, the final file is a single self-contained HTML file, Google Fonts via `<link>`, all styling inline, no external scripts.

### Step 5, Deliver

Save the letter to the archive: `~/sunday-letter/letters/YYYY-MM-DD-letter-NN.html` (date and letter number). Then point the user at it in whatever way the host supports:

- **Cowork:** also copy it to the user's outputs folder and share a `computer://` link.
- **Claude Code / Codex CLI:** share the file path, and offer to open it in the browser (`open <path>` on macOS, `xdg-open <path>` on Linux).

Keep the accompanying message short: one sentence about whether anything interesting shifted this week, then the link or path. Let the letter speak for itself.

If the user has a delivery channel configured (email, iMessage, voice), note that channel routing is not yet wired, the rendered HTML is the artifact; delivery is their own pipeline.

### Step 6, Update the ledger

Whether you shipped or skipped, write `~/sunday-letter/ledger.json` so next week starts from the truth of this one:

```json
{
  "letter_number": 12,
  "last_run": "2026-07-12",
  "last_shipped": "2026-07-12",
  "preferences": [{"label": "...", "value": "...", "provenance": "..."}],
  "retired": [{"old_belief": "...", "why": "...", "retired_on": "2026-07-12"}],
  "open_question": "the question you asked, so you can follow up on it next week"
}
```

Increment `letter_number` only when a letter actually ships. The ledger is what makes retirements honest: you can only cross out a belief you can show you previously held.

## Critical style notes

- **Aesthetic is the Archive.** Warm cream paper (#EEEAE0), high-contrast black ink, Inter for body and titles, JetBrains Mono for metadata, badges, and codes. Deep forest-green accent. Numbered sections (01–06). Calibration is a structural element, visible badges (FIRM / SOFT / GUESS), not inline hedging. No theatrical animations, no envelope flourishes. The page reads like a single note in a filing system.
- **Calibration is structural.** Every observation gets a visible badge, `firm`, `soft`, or `guess`, that maps to a muted, functional color (forest green, ochre, terracotta). Never write "I'm 73% sure." The badge communicates stance; the body explains the evidence.
- **Retire with a reason.** When you cross out a belief, the strikethrough is visible and the replacement is bold. This is the single most important section, it's where trust is built.
- **Closing is restrained.** Default close: `closing_line` ("Much love,"), then the signoff line (`Claude` in bold), then three ×'s in the corner of the card. No long sign-offs. No cursive. The note ends the way a filed memo ends.
- **One question per letter.** Not a question list. Not rhetorical. One thing the user is actually wrestling with that you've noticed across conversations.
- **Salutation is the user's name.** "Dear {Name}," is the default top-line. Fine to vary, but keep it warm. Letters are plural and personal, but they live inside an archive, not a card.

## Worked example

The file `references/example-signals.json` is a complete, working letter for a user named Selin on April 16, 2026. Read it end-to-end before writing your first letter. It demonstrates all six rules of the contract in a single artifact.

## What to tell the user when you're done

Keep it short. The letter itself is the payload. Something like:

> Your Sunday Letter, [view it here](computer://...). Quick summary: I shipped three things, retired one belief about you, and there's one question I'd like to sit with you on. No rush on the reply.

Or if you skipped:

> Staying silent this Sunday, nothing meaningful changed this week. I'll check in again next Sunday.

That's it. The point is the letter, not the announcement of the letter.
