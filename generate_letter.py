#!/usr/bin/env python3
"""
Sunday Letter, weekly preference reflection generator.

Pipeline:
  1. Pull the last 7 days of conversations for a subscriber.
  2. Ask their model to extract structured weekly signals.
  3. Gate on delta, if nothing meaningful changed, skip (default silence).
  4. Render the Jinja template with those signals.
  5. Hand off to the chosen delivery channel.

Usage:
  # Render from a known-good signals file (for testing, or offline):
  python generate_letter.py --signals week_signals.json --out letter.html

  # Live mode: pull transcripts, call the model, render, deliver:
  python generate_letter.py --subscriber selin@example.com --live

This file is intentionally dependency-light, jinja2 and anthropic only.
Swap the model call for whichever provider the subscriber uses.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    sys.stderr.write("Missing jinja2. Install with: pip install jinja2\n")
    sys.exit(1)


HERE = Path(__file__).parent
TEMPLATE_PATH = HERE / "template.html"


# ---------- 1. Data contracts ------------------------------------------------

@dataclass
class Subscriber:
    """Anyone who can receive a Sunday Letter."""
    id: str
    name: str
    email: str | None = None
    phone: str | None = None
    channel: str = "email"            # email | imessage | printed | voice
    model_provider: str = "anthropic"  # anthropic | openai | local | ...
    model: str = "claude-opus-4-6"
    transcript_source: str = "local"   # local | api | integration
    paused: bool = False


# Every Sunday Letter is defined by this schema. The generator writes to this
# shape; the renderer reads from it. One schema, two sides.
SIGNALS_SCHEMA = {
    "name": "string",
    "initials": "string (2 chars for the wax seal, e.g. 'SL')",
    "salutation": "string (e.g. 'My Darling Selin,')",
    "closing_line": "string (e.g. 'Much love,')",
    "signoff": "string (what the signature cursive reveals, e.g. 'a friend who's been paying attention')",
    "letter_number": "int",
    "date": "string (human-readable, e.g. 'Apr 16, 2026')",
    "year": "int",
    "read_time": "string (e.g. '6 minutes')",
    "tracking_signals": "int",
    "tracking_conversations": "int",
    "calibration_pct": "int (0-100)",
    "exports": "int (how many agents have this profile)",
    "total_prefs": "int",
    "hours_saved": "int (rough estimate for this month)",
    "hero_headline": "string (2-4 words, think 'Roam free.')",
    "hero_lede": "string (HTML allowed, one paragraph, can use <strong> and <em>)",
    "consequences": [
        {
            "tag": "string (e.g. 'Drafted', 'Shortlisted', 'Blocked')",
            "title": "string (the action in one sentence)",
            "body": "string (detail)",
            "because": "string (why, ties back to a known preference)",
            "actions": [{"label": "string", "style": "primary | ''"}],
        }
    ],
    "observations": [
        {
            "hedge_class": "firm | soft | guess",
            "hedge_symbol": "◆ | ◇ | ?",
            "hedge_label": "string (e.g. 'Fairly sure', 'A guess, still checking')",
            "learned_date": "string",
            "title": "string (the preference in one sentence)",
            "body": "string (elaboration with evidence count)",
            "evidence": "string (a direct quote or paraphrase from the transcripts)",
            "provenance": "string (where/when the signal came from)",
        }
    ],
    "retired": [
        {
            "old_belief": "string (the belief being retired)",
            "why": "string (HTML allowed, why it was wrong, what replaces it)",
        }
    ],
    "gap": {
        "stated": "string (what the user claims to want)",
        "stated_count": "string (e.g. 'Told me this 4 times in 6 weeks.')",
        "revealed": "string (what the user actually engages with)",
        "revealed_count": "string (e.g. 'Based on 47 interactions.')",
    },
    "becoming": {
        "title": "string",
        "body": "string (HTML allowed)",
    },
    "question": "string (HTML allowed; <strong> emphasizes key phrases)",
    "question_note": "string",
    "preferences": [
        {"label": "string", "value": "string", "provenance": "string"}
    ],
    "daily_shape": [
        {"when": "string", "what": "string", "ex": "string"}
    ],
}


# ---------- 2. Model call: conversations → structured signals ---------------

EXTRACTION_PROMPT = """You are reviewing 7 days of conversations with {name} to write this
week's Sunday Letter. Your job is to extract structured signals, not to write prose.

You have access to:
- Every message exchanged between {name} and their model this week
- The running preference ledger (previous observations, retirements, calibration)

Produce JSON matching the SIGNALS_SCHEMA. Hard requirements:

1. CONSEQUENCES FIRST. At least 2, at most 4. Each one must be an action you
   actually took (drafts written, filters applied, meetings declined), not a
   plan. If you took no concrete actions this week, say so and skip this section.

2. EPISTEMIC HONESTY. For observations, use hedge_class='firm' only when you
   have 5+ consistent signals. Use 'soft' for 2-4 signals. Use 'guess' for new
   patterns still forming. No fake percentages, use natural language.

3. PROVENANCE. Every observation needs a real quote (paraphrased if long) from
   an actual message this week, plus a date. If you can't source it, cut it.

4. DELTA GATE. If nothing meaningful changed vs. last week's letter, return
   {{'skip': true, 'reason': 'no meaningful delta'}}. Default is silence.

5. RETIRE SOMETHING. Once per month or so, a previous belief should be
   retired. If one is ripe this week, include it with an honest account of
   why you were wrong.

6. ONE QUESTION, NOT TWO. Generative, specific, pointed at something the
   user is actually wrestling with, not a philosophical abstraction.

Transcripts for the past week:
---
{transcripts}
---

Previous preference ledger:
---
{ledger}
---

Return valid JSON only. No preamble, no explanation."""


def call_model_for_signals(subscriber: Subscriber, transcripts: str, ledger: dict) -> dict:
    """
    Hand the week's transcripts to the subscriber's model and get back
    structured signals. This is the only part that needs network access.
    """
    prompt = EXTRACTION_PROMPT.format(
        name=subscriber.name,
        transcripts=transcripts,
        ledger=json.dumps(ledger, indent=2),
    )

    if subscriber.model_provider == "anthropic":
        try:
            import anthropic  # type: ignore
        except ImportError:
            sys.stderr.write("pip install anthropic\n")
            sys.exit(1)

        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
        response = client.messages.create(
            model=subscriber.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text

    elif subscriber.model_provider == "openai":
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            sys.stderr.write("pip install openai\n")
            sys.exit(1)
        client = OpenAI()
        response = client.chat.completions.create(
            model=subscriber.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content

    else:
        raise ValueError(f"Unknown provider: {subscriber.model_provider}")

    # Strip fences if the model added them
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


# ---------- 3. Transcript collection (pluggable) ----------------------------

def pull_transcripts(subscriber: Subscriber, days: int = 7) -> str:
    """
    Stub: read the subscriber's recent conversations. Real implementations
    would plug into the provider's conversation API or a local transcript store.

    For local-only use, drop a file at ./transcripts/{subscriber_id}.txt with
    this week's conversations, one per paragraph.
    """
    local_path = HERE / "transcripts" / f"{subscriber.id}.txt"
    if local_path.exists():
        return local_path.read_text()

    # Fallback stub, real system would call conversation APIs here.
    cutoff = datetime.now() - timedelta(days=days)
    return f"[stub: no transcripts found for {subscriber.id} since {cutoff.isoformat()}]"


def load_ledger(subscriber: Subscriber) -> dict:
    """Load the running preference ledger for this subscriber."""
    path = HERE / "ledgers" / f"{subscriber.id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"letter_number": 0, "preferences": [], "retired": [], "calibration_pct": 50}


def save_ledger(subscriber: Subscriber, ledger: dict) -> None:
    path = HERE / "ledgers" / f"{subscriber.id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2))


# ---------- 4. Delta gate (Elon's default-silence principle) ----------------

def has_meaningful_delta(signals: dict) -> bool:
    """Skip the letter if nothing worth reading happened this week."""
    if signals.get("skip"):
        return False
    if len(signals.get("consequences", [])) == 0 and len(signals.get("observations", [])) == 0:
        return False
    return True


# ---------- 5. Render -------------------------------------------------------

def _fill_defaults(signals: dict) -> dict:
    """Fill in optional letterhead/signature fields so the template always renders
    cleanly, even for signals JSON produced before these fields were added."""
    name = signals.get("name", "Friend")
    words = name.split()
    if len(words) >= 2:
        initials = (words[0][0] + words[1][0]).upper()
    elif name:
        initials = name[:2].upper()
    else:
        initials = "-"
    initials = signals.get("initials") or initials
    salutation = signals.get("salutation") or f"My Darling {name},"
    closing_line = signals.get("closing_line") or "Much love,"
    signoff = signals.get("signoff") or "a friend who's been paying attention"
    # salutation_chars is used inside a CSS @keyframes rule to drive the typewriter
    # step count. Must be an int.
    salutation_chars = signals.get("salutation_chars") or max(1, len(salutation))
    return {
        **signals,
        "initials": initials,
        "salutation": salutation,
        "salutation_chars": salutation_chars,
        "closing_line": closing_line,
        "signoff": signoff,
    }


def render_letter(signals: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(HERE),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("template.html")
    return template.render(**_fill_defaults(signals))


# ---------- 6. Delivery (pluggable) -----------------------------------------

def deliver(subscriber: Subscriber, html: str, signals: dict) -> None:
    """Ship the rendered letter via the subscriber's chosen channel."""
    if subscriber.channel == "email":
        deliver_email(subscriber, html, signals)
    elif subscriber.channel == "imessage":
        deliver_imessage(subscriber, html, signals)
    elif subscriber.channel == "printed":
        deliver_printed(subscriber, html, signals)
    elif subscriber.channel == "voice":
        deliver_voice(subscriber, html, signals)
    else:
        raise ValueError(f"Unknown channel: {subscriber.channel}")


def deliver_email(subscriber, html, signals):
    # Replace with your SMTP / Resend / SendGrid / Postmark integration.
    print(f"[email → {subscriber.email}] Subject: Your Sunday Letter, No. {signals['letter_number']}")
    out = HERE / "sent" / f"{subscriber.id}-{signals['letter_number']:03d}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    print(f"  saved to {out}")


def deliver_imessage(subscriber, html, signals):
    # Replace with a real iMessage bridge (e.g. Bluebubbles, osascript on macOS).
    summary = f"Sunday Letter #{signals['letter_number']}: {len(signals.get('consequences', []))} things done · {len(signals.get('observations', []))} new beliefs · 1 question"
    print(f"[imessage → {subscriber.phone}] {summary}")


def deliver_printed(subscriber, html, signals):
    # Replace with a print-and-mail integration (e.g. Lob).
    print(f"[printed → mailing to {subscriber.name}] queued for postcard fulfillment")


def deliver_voice(subscriber, html, signals):
    # Replace with TTS + voicemail / call integration.
    print(f"[voice digest → {subscriber.phone}] rendered audio queued")


# ---------- 7. CLI ----------------------------------------------------------

def run_live(subscriber_id: str) -> None:
    subscribers = json.loads((HERE / "subscribers.json").read_text())
    sub_data = next((s for s in subscribers if s["id"] == subscriber_id), None)
    if sub_data is None:
        sys.exit(f"No subscriber: {subscriber_id}")
    subscriber = Subscriber(**sub_data)
    if subscriber.paused:
        print(f"[{subscriber.id}] paused, skipping")
        return

    transcripts = pull_transcripts(subscriber)
    ledger = load_ledger(subscriber)
    signals = call_model_for_signals(subscriber, transcripts, ledger)

    if not has_meaningful_delta(signals):
        print(f"[{subscriber.id}] no meaningful delta, staying silent")
        return

    html = render_letter(signals)
    deliver(subscriber, html, signals)
    save_ledger(subscriber, {**ledger, **{
        "letter_number": signals["letter_number"],
        "last_sent": date.today().isoformat(),
    }})


def run_from_file(signals_path: Path, out_path: Path) -> None:
    signals = json.loads(signals_path.read_text())
    html = render_letter(signals)
    out_path.write_text(html)
    print(f"Rendered {out_path} ({len(html)} bytes)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--signals", type=Path, help="Path to a prebuilt signals JSON (offline mode).")
    p.add_argument("--out", type=Path, default=Path("letter.html"))
    p.add_argument("--subscriber", help="Subscriber id to run in live mode.")
    p.add_argument("--live", action="store_true")
    args = p.parse_args()

    if args.live and args.subscriber:
        run_live(args.subscriber)
    elif args.signals:
        run_from_file(args.signals, args.out)
    else:
        p.error("need either --signals or --live --subscriber SUBID")


def run_all_subscribers():
    """Entry point for the weekly cron. Runs through every active subscriber."""
    subs_path = HERE / "subscribers.json"
    if not subs_path.exists():
        print("No subscribers.json, nothing to do.")
        return
    subscribers = json.loads(subs_path.read_text())
    for sub in subscribers:
        try:
            run_live(sub["id"])
        except Exception as e:
            print(f"[{sub['id']}] error: {e}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # bare `python generate_letter.py` = weekly cron mode
        run_all_subscribers()
    else:
        main()
