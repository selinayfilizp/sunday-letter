---
description: Subscribe to the Sunday Letter, schedule a weekly run at a day and time the user chooses (default Sunday 6pm). Only ships when something meaningful has changed.
---

# /subscribe-sunday-letter

Set up the Sunday Letter as a recurring weekly task. The **name stays "Sunday Letter"** for the brand; the **delivery slot is whatever day and time** the user wants.

## What to do

1. **Confirm intent.** Use `AskUserQuestion` (or an equivalent) so the user picks one of these paths:
   - **Weekly default:** Every Sunday at 6:00 PM (local to the scheduler unless they specify a timezone).
   - **Weekly, custom:** They choose **day of week** and **time** (24h or 12h with AM/PM). Optionally **IANA timezone** (e.g. `Europe/London`) if their scheduler supports `CRON_TZ` or per-task timezone. If not, explain that cron uses the **machine's local clock** and they should pick wall time accordingly.
   - **Just write one now:** Fall through to `/sunday-letter` and do **not** create a recurring task unless they ask for both.

2. **Capture the schedule in one place.** After they choose, restate it in plain language and, if they use a custom slot, offer to save a small JSON snippet (same shape as `skills/sunday-letter/references/schedule-config.example.json`) in their workspace so you can read it on later turns.

3. **Build the cron expression.** Standard five-field cron: `minute hour * * dayOfWeek` where **0 = Sunday** through **6 = Saturday** (same as typical `crontab` on macOS/Linux).

   | User picks | `dayOfWeek` |
   |------------|-------------|
   | Sunday | `0` |
   | Monday | `1` |
   | Tuesday | `2` |
   | Wednesday | `3` |
   | Thursday | `4` |
   | Friday | `5` |
   | Saturday | `6` |

   Examples:
   - Sunday 6:00 PM → `0 18 * * 0`
   - Monday 9:30 AM → `30 9 * * 1`
   - Wednesday 7:00 PM → `0 19 * * 3`

   If they want **sub-minute** precision, most schedulers do not support it; round to the nearest minute.

4. **Create or update the scheduled task.** If they picked weekly:
   - `name`: `sunday-letter` (keep this stable so triggers and docs match).
   - `cron`: the expression from step 3.
   - **If they already have** a `sunday-letter` task, **update** it (same tool family as create, if available) or delete and recreate so the new cron applies. Do not leave two tasks with the same purpose.
   - `prompt`: use a variant of the following, filling in their **actual weekday name and local time** so the trigger text matches their life rhythm:

     `"It's time for your weekly letter (${weekdayName} ${timeLabel}, your chosen slot). Invoke the sunday-letter skill and write this week's letter. Apply the delta gate: stay silent if nothing meaningful changed. Save the letter to the outputs folder and share a computer:// link."`

   - If the platform supports **timezone** on the task and they gave an IANA zone, set it. Otherwise add one line to the task description or their notes: `Wall clock: ${timezone or "scheduler local"}.`

5. **Walk through what they signed up for.** One short paragraph:
   - Default is silence; a letter only ships when something meaningful changed.
   - They can **change day or time** anytime by running this command again or asking you to reschedule.
   - Pause or cancel via `/schedules` or by asking.

6. **Offer a preview.** Ask if they want the first letter **now** so they can see the aesthetic. If yes, invoke the `sunday-letter` skill immediately.

## Arguments

None required. All configuration happens in the conversation (day, time, timezone, on-demand only).

## What to tell the user when done

Adapt the closing line to their schedule, for example:

> You're subscribed. I'll write you a letter every **Tuesday at 7:30 AM** (your time), but only when something's worth saying. If you want a different slot later, ask me to reschedule.

(Replace the bolded fragment with their actual choices.)

That's it. The letter is the product, not the subscription confirmation.
