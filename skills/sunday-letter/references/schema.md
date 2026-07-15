# Sunday Letter signals contract

The machine-readable source of truth is [`signals.schema.json`](./signals.schema.json).
The Python runtime validates every payload against that file before it applies the
delta gate or writes HTML. Do not maintain a second schema in prompts or code.

## Two valid payloads

A silent week is explicit:

```json
{
  "schema_version": "1.0",
  "skip": true,
  "reason": "no meaningful delta"
}
```

A shipped letter follows [`example-signals.json`](./example-signals.json). The
runtime, not the model, owns the sequential `letter_number` during normal runs.
The example includes a number only so it can be rendered in preview mode.

## Trust boundaries

- Do not emit calibration percentages, hours saved, exports, or other unmeasured
  metrics. The validator rejects these legacy fields.
- Every consequence, decision, open task, observation, retirement, gap, and
  becoming claim carries provenance.
- Observation stance is one of `firm`, `soft`, or `guess`; the evidence text
  explains why.
- Rich text permits only `<strong>` and `<em>`. The renderer escapes every other
  tag and adds a restrictive Content Security Policy.
- A non-skip payload must contain a meaningful consequence, decision,
  observation, or retired belief. Otherwise return the skip payload.
- The renderer cannot render a skip payload. This is enforced in every CLI path.

## Measured source summary

`source_summary` is required for a shipped letter. Its scope, counts, and date
window must exactly match the collected Codex bundle:

```json
{
  "thread_count": 4,
  "message_count": 31,
  "window_start": "2026-07-07T00:00:00Z",
  "window_end": "2026-07-14T00:00:00Z",
  "scope": "selected local Codex threads"
}
```

These are counts, not confidence estimates.
