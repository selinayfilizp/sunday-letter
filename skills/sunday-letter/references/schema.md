# Sunday Letter Signals Schema

One JSON object per letter. This is the contract between the model (which extracts signals from a week of conversations) and the template (which renders them as a letter).

See [`week_signals.example.json`](./week_signals.example.json) for a complete, working example.

## Top-level fields

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | ✅ | The subscriber's first name. |
| `initials` | string | ⚠️ auto | 2-letter wax seal. Defaults to first two letters of `name`. |
| `salutation` | string | ⚠️ auto | Opening line. Defaults to `My Darling {name},` |
| `closing_line` | string | ⚠️ auto | Line above signature. Defaults to `Much love,` |
| `signoff` | string | ⚠️ auto | Cursive signature text. Defaults to `a friend who's been paying attention`. |
| `letter_number` | int | ✅ | Sequential letter count for this subscriber. |
| `date` | string | ✅ | Human-readable date, e.g. `Apr 16, 2026`. |
| `year` | int | ✅ | |
| `read_time` | string | ✅ | e.g. `6 minutes`. |
| `tracking_signals` | int | ✅ | Count for the letterhead line. |
| `tracking_conversations` | int | ✅ | |
| `calibration_pct` | int | ✅ | 0–100. How often the model correctly predicted user preferences this week. |
| `exports` | int | ✅ | How many agents have this profile. |
| `total_prefs` | int | ✅ | Total preferences in the ledger. |
| `hours_saved` | int | ✅ | Rough month-level estimate. |
| `hero_headline` | string | ✅ | 2–4 words. |
| `hero_lede` | string (HTML) | ✅ | One paragraph. Can use `<strong>`, `<em>`, `<span class="pen-underline">…</span>`. |

## Sections (arrays)

### `consequences`, what the agent did for the user this week

At least 2, at most 4. Each must be an action actually taken, not a plan.

```json
{
  "tag": "Drafted",
  "title": "3 recruiter replies, ready for your review.",
  "body": "Two AI-lab roles (product-growth), one declined politely.",
  "because": "Because I know your wedge is AI labs, product × growth × ops.",
  "actions": [{"label": "Review 3 drafts", "style": "primary"}]
}
```

### `observations`, what the agent learned about the user

```json
{
  "hedge_class": "firm",              // firm | soft | guess
  "hedge_symbol": "◆",                 // ◆ | ◇ | ?
  "hedge_label": "Fairly sure",
  "learned_date": "learned Apr 16",
  "title": "You're drawn to answers that push back.",
  "body": "…evidence, with count…",
  "evidence": "stress-test this as Elon, Karpathy…",
  "provenance": "Apr 16 · 8:24 PM · strongest signal this week"
}
```

Use `firm` only with 5+ consistent signals. `soft` for 2–4. `guess` for new patterns.

### `decisions`, what got decided this week

Concrete decisions the user and agent converged on. State these as outcomes, not vague themes.

```json
{
  "title": "Launch navigation should use Feed / Shelf / Activity / Profile.",
  "body": "Folio was renamed to Feed, Index became Activity, and Profile replaced Me.",
  "provenance": "May 9 · Selo launch UX thread"
}
```

### `open_tasks`, tasks or open loops still worth carrying forward

Only include tasks that remain useful next week. Avoid dumping every small todo.

```json
{
  "title": "Submit latest TestFlight build to external testers.",
  "body": "External testers could only see an older build until Apple approved the newer build.",
  "owner": "Selinay / Codex",
  "provenance": "May 9 · TestFlight review thread"
}
```

### `retired`, beliefs the agent stopped holding

```json
{
  "old_belief": "Selin prefers structured frameworks over narrative thinking.",
  "why": "I held this for 4 weeks. It was wrong… replacing with <strong>narrative generator, framework translator</strong>."
}
```

### `gap`, stated vs revealed preferences

```json
{
  "stated": "Keep it concise.",
  "stated_count": "Told me this 4 times in 6 weeks.",
  "revealed": "Engaged 3.2× longer with responses over 600 words.",
  "revealed_count": "Based on 47 interactions."
}
```

### `becoming`, preferences in motion

```json
{
  "title": "From thinking partner to autonomous collaborator",
  "body": "Six weeks ago you defended… This week you asked about… (HTML allowed)"
}
```

### `question`, the one thing worth sitting with this week

```json
"question": "You keep returning to DecisionOS. Is it a <strong>product you want to build</strong>, or a <strong>workflow you want for yourself</strong>?",
"question_note": "No need to reply now. Voice-memo a stray thought and I'll hold it."
```

One question, specific and generative. HTML allowed for emphasis.

### `preferences`, portable profile

```json
{
  "label": "Response shape",
  "value": "TL;DR top, depth below",
  "provenance": "learned Apr 16 · 6 of 7 engagements"
}
```

### `daily_shape`, how agent/user stay in touch through the week

```json
{
  "when": "Mon–Fri · 7:12am",
  "what": "One-line morning card",
  "ex": "\"Handling 3 recruiter replies in your voice. Flag if you want to eyeball one.\""
}
```

## Delta gate, skipping silently

If nothing meaningful happened this week, the model should return:

```json
{"skip": true, "reason": "no meaningful delta"}
```

`has_meaningful_delta()` in the generator returns `False` for this payload and the letter is suppressed. Default silence is a feature.

## Versioning

This schema is v1. Breaking changes will bump the version and include a migration note here.
