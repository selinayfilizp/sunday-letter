---
description: Subscribe to the Sunday Letter, schedule a weekly run so the agent writes a letter every Sunday at 6pm (only ships when something meaningful has changed).
---

# /subscribe-sunday-letter

Set up the Sunday Letter as a recurring weekly task.

## What to do

1. **Confirm intent.** Use `AskUserQuestion` to confirm the user wants a weekly scheduled letter. Offer three options:
   - "Every Sunday at 6pm" (the default)
   - "Every Sunday at a time I choose" (follow up with a time picker)
   - "Actually, just write one now" (fall through to `/sunday-letter`)

2. **Create the scheduled task.** If they picked weekly, call the `scheduled-tasks` MCP (tool: `mcp__scheduled-tasks__create_scheduled_task`) with:
   - `name`: `sunday-letter`
   - `cron`: `0 18 * * 0` (Sundays at 6pm local, adjust the hour if they chose a different time)
   - `prompt`: `"It's Sunday. Invoke the sunday-letter skill and write this week's letter. Apply the delta gate, stay silent if nothing meaningful changed. Save the letter to the outputs folder and share a computer:// link."`

3. **Walk through what they just signed up for.** Keep it short, one paragraph. Remind them:
   - Default is silence. A letter only ships when something's changed.
   - They can pause or cancel the schedule with `/schedules` or by asking.
   - This Sunday will be the first letter, they don't need to do anything.

4. **Offer to write a preview now.** Ask if they'd like the first letter written today so they can see the aesthetic. If yes, invoke the `sunday-letter` skill immediately.

## Arguments

None required. All configuration happens through the clarifying question in step 1.

## What to tell the user when done

Something like:

> You're subscribed. I'll write you a letter next Sunday at 6pm, and every Sunday after, but only when something's worth saying. [View your first letter →](computer://...) _(if they asked for a preview)_

That's it. The letter is the product, not the subscription confirmation.
