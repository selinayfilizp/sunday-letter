---
description: Write this week's Sunday Letter, a reflective letter from the agent to the user about what it did, what it learned, what it retired, and one question worth sitting with.
---

# /sunday-letter

Write a Sunday Letter for the user right now.

## What to do

Invoke the `sunday-letter` skill. Follow its workflow end-to-end:

1. Look back over the last seven days of conversations with the user.
2. Extract structured signals (consequences, observations, retired beliefs, gap, becoming, question), see `skills/sunday-letter/references/schema.md`.
3. Apply the delta gate: if nothing meaningful changed this week, do not ship. Tell the user briefly that you're staying silent this Sunday, and stop.
4. Otherwise, render the letter to a single self-contained HTML file using `skills/sunday-letter/references/template.html` as the visual reference. Save it to the user's outputs folder.
5. Share a `computer://` link and a one-sentence summary. Nothing more.

## Arguments

This command takes no arguments. It always writes for the current user based on the last seven days.

If the user wants to preview the aesthetic without their own data, render `skills/sunday-letter/references/example-signals.json` instead and tell them it's the sample.

## Non-negotiables

- **Six rules of the contract.** Consequences first, epistemic honesty (no fake percentages), provenance on every observation, default silence, retire something at least monthly, one question (not two).
- **No exposed internal paths.** Refer to the letter as "your Sunday Letter", never as `/sessions/.../sample-letter.html`.
- **One question, not a survey.** Pick the single most generative thing the user is wrestling with. If you can't find one, the week wasn't interesting enough to ship.

Read `skills/sunday-letter/SKILL.md` and `skills/sunday-letter/references/design-principles.md` before writing the first letter.
