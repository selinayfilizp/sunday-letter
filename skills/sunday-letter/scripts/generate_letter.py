#!/usr/bin/env python3
"""Validate, gate, render, and record one agent-local Sunday Letter run."""

from __future__ import annotations

import argparse
import json
import os
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core import (
    ValidationError,
    atomic_write_text,
    default_ledger,
    ensure_private_directory,
    ledger_lock,
    load_ledger,
    sanitize_rich_text,
    save_ledger,
    text,
    today_iso,
    validate_signals,
)


HERE = Path(__file__).resolve().parent
STYLE_PATH = HERE.parent / "references" / "letter.css"
DEFAULT_ROOT = Path.home() / "sunday-letter"


class PausedError(RuntimeError):
    """The local subscription is paused in the ledger."""


@dataclass(frozen=True)
class RunResult:
    status: str
    out_path: Path | None
    letter_number: int | None
    reason: str | None = None


def _style_block() -> str:
    return f"<style>\n{STYLE_PATH.read_text()}\n</style>"


def _rich(value: Any) -> str:
    return sanitize_rich_text(value)


def _section(number: int, title: str, body: str) -> str:
    return f"""
    <section class="section">
      <div class="section-head">
        <span class="section-num">{number:02d}</span>
        <h2 class="section-title">{text(title)}</h2>
      </div>
      {body.strip()}
    </section>"""


def _render_consequences(items: list[dict[str, Any]]) -> str:
    rows = "".join(
        f"""
        <li class="csq">
          <div>
            <span class="csq-tag">{text(item['tag'])}</span>
            <h3 class="csq-title">{text(item['title'])}</h3>
            <p class="csq-body">{_rich(item['body'])}</p>
            <div class="csq-because">{_rich(item['because'])}</div>
            <div class="obs-prov">{text(item['provenance'])}</div>
          </div>
        </li>"""
        for item in items
    )
    return f'<ol class="csq-list">{rows}</ol>'


def _render_decisions_and_tasks(
    decisions: list[dict[str, Any]], tasks: list[dict[str, Any]]
) -> str:
    decision_rows = "".join(
        f"""
        <li class="csq">
          <div>
            <span class="csq-tag">Decision</span>
            <h3 class="csq-title">{text(item['title'])}</h3>
            <p class="csq-body">{_rich(item['body'])}</p>
            <div class="obs-prov">{text(item['provenance'])}</div>
          </div>
        </li>"""
        for item in decisions
    )
    task_rows = "".join(
        f"""
        <li class="csq">
          <div>
            <span class="csq-tag">Open loop</span>
            <h3 class="csq-title">{text(item['title'])}</h3>
            <p class="csq-body">{_rich(item['body'])}</p>
            <div class="csq-because">Owner: {text(item['owner'])}</div>
            <div class="obs-prov">{text(item['provenance'])}</div>
          </div>
        </li>"""
        for item in tasks
    )
    return f'<ol class="csq-list">{decision_rows}{task_rows}</ol>'


def _render_observations(items: list[dict[str, Any]]) -> str:
    return "".join(
        f"""
      <div class="obs">
        <div class="obs-head">
          <span class="badge {text(item['hedge_class'])}">{text(item['hedge_label'])}</span>
          <span class="obs-when">· {text(item['learned_date'])}</span>
        </div>
        <h3 class="obs-title">{text(item['title'])}</h3>
        <p class="obs-body">{_rich(item['body'])}</p>
        <div class="obs-evidence">{_rich(item['evidence'])}</div>
        <div class="obs-prov">{text(item['provenance'])}</div>
      </div>"""
        for item in items
    )


def _render_retired(items: list[dict[str, Any]]) -> str:
    return "".join(
        f"""
      <div class="retired-card">
        <p class="retired-old">{text(item['old_belief'])}</p>
        <div class="retired-arrow">→ Replaced because</div>
        <p class="retired-why">{_rich(item['why'])}</p>
        <div class="obs-prov">{text(item['provenance'])}</div>
      </div>"""
        for item in items
    )


def _render_gap(item: dict[str, Any]) -> str:
    return f"""
      <div class="gap-grid">
        <div class="gap-cell">
          <div class="gap-label">You said</div>
          <p class="gap-value">{text(item['stated'])}</p>
          <div class="gap-count">{text(item['stated_count'])}</div>
        </div>
        <div class="gap-cell">
          <div class="gap-label">You did</div>
          <p class="gap-value">{text(item['revealed'])}</p>
          <div class="gap-count">{text(item['revealed_count'])}</div>
        </div>
      </div>
      <div class="obs-prov">{text(item['provenance'])}</div>"""


def _render_becoming(item: dict[str, Any]) -> str:
    return f"""
      <div class="becoming-card">
        <h3 class="becoming-title">{text(item['title'])}</h3>
        <p class="becoming-body">{_rich(item['body'])}</p>
        <div class="obs-prov">{text(item['provenance'])}</div>
      </div>"""


def render_letter(
    signals: dict[str, Any],
    *,
    archive_href: str | None = "../index.html",
    export_href: str | None = None,
) -> str:
    """Render validated signals through the single dependency-free HTML path."""
    validated = validate_signals(signals)
    if validated.get("skip"):
        raise ValidationError("skip payloads cannot be rendered")

    sections: list[str] = []
    number = 1
    if validated["consequences"]:
        sections.append(
            _section(number, "What I did this week", _render_consequences(validated["consequences"]))
        )
        number += 1
    if validated["decisions"] or validated["open_tasks"]:
        sections.append(
            _section(
                number,
                "Decisions and open loops",
                _render_decisions_and_tasks(validated["decisions"], validated["open_tasks"]),
            )
        )
        number += 1
    if validated["observations"]:
        sections.append(
            _section(number, "What I learned about you", _render_observations(validated["observations"]))
        )
        number += 1
    if validated["retired"]:
        sections.append(_section(number, "What I retired", _render_retired(validated["retired"])))
        number += 1
    if validated.get("gap"):
        sections.append(_section(number, "The gap (stated vs. revealed)", _render_gap(validated["gap"])))
        number += 1
    if validated.get("becoming"):
        sections.append(_section(number, "What you're becoming", _render_becoming(validated["becoming"])))
        number += 1

    source = validated.get("source_summary") or {}
    source_line = ""
    if source:
        source_line = (
            f"{text(source['thread_count'])} threads · {text(source['message_count'])} messages · "
            f"{text(source['window_start'])} → {text(source['window_end'])}"
        )
    export_link = ""
    if export_href:
        export_link = f'<a href="{text(export_href)}" download>Export HTML</a>'
    archive_link = (
        f'<a href="{text(archive_href)}">Archive</a>' if archive_href else ""
    )
    wordmark = (
        f'<a class="wordmark" href="{text(archive_href)}"><span class="dot"></span>The Sunday Letter</a>'
        if archive_href
        else '<span class="wordmark"><span class="dot"></span>The Sunday Letter</span>'
    )

    letter_number = int(validated["letter_number"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Letter №{letter_number} · {text(validated['date'])} · The Sunday Letter</title>
<meta name="description" content="A local weekly note grounded in recent agent conversations.">
{_style_block()}
</head>
<body>
<header class="topbar">
  {wordmark}
  <div class="meta-right"><span>Letter №{letter_number}</span><span>{text(validated['date'])}</span></div>
</header>
<main class="container">
  <article class="note">
    <div class="note-meta">
      <div class="note-meta-left"><span class="num">№{letter_number}</span> · {text(validated['date'])} · for {text(validated['name'])}</div>
      <div class="note-meta-right">{source_line}</div>
    </div>
    <h1 class="note-title">{text(validated['hero_headline'])}</h1>
    <p class="note-lede">{_rich(validated['hero_lede'])}</p>
    {''.join(sections)}
    <section class="question-block">
      <div class="question-label">{number:02d} · One question</div>
      <p class="question">{_rich(validated['question'])}</p>
      {f'<p class="question-note">{text(validated.get("question_note"))}</p>' if validated.get('question_note') else ''}
    </section>
    <div class="note-close">
      <div class="signoff">
        <div class="signoff-line">{text(validated.get('closing_line'), 'Until next week,')}</div>
        <div class="sig-name">{text(validated.get('signoff'), 'your attentive agent')}</div>
      </div>
      <div class="close-mark">× × ×</div>
    </div>
    <div class="note-foot">
      <div class="note-foot-left">Local agent sources only</div>
      <div class="note-foot-right">{export_link}{archive_link}</div>
    </div>
  </article>
</main>
</body>
</html>
"""


def _relative_archive_href(out_path: Path, ledger_path: Path) -> str:
    target = ledger_path.expanduser().resolve().parent / "index.html"
    return Path(os.path.relpath(target, out_path.expanduser().resolve().parent)).as_posix()


def _ledger_file_value(out_path: Path, ledger_path: Path) -> str:
    try:
        return out_path.expanduser().resolve().relative_to(
            ledger_path.expanduser().resolve().parent
        ).as_posix()
    except ValueError:
        return out_path.name


def _rebuild_archive(ledger_path: Path) -> None:
    from manage_archive import build_archive

    build_archive(ledger_path.expanduser().resolve().parent)


def read_context_source_summary(context_path: Path) -> dict[str, Any]:
    """Read measured source metadata from the collector-owned header."""
    header = context_path.expanduser().read_text().split("> BEGIN TRANSCRIPT DATA", 1)[0]
    labels = {
        "Window start": "window_start",
        "Window end": "window_end",
        "Source scope": "scope",
        "Threads included": "thread_count",
        "Messages included": "message_count",
    }
    found: dict[str, Any] = {}
    for line in header.splitlines():
        for label, key in labels.items():
            prefix = f"{label}: "
            if line.startswith(prefix):
                value: Any = line[len(prefix) :].strip()
                if key in {"thread_count", "message_count"}:
                    try:
                        value = int(value)
                    except ValueError as error:
                        raise ValidationError(
                            f"context header {label!r} must be an integer"
                        ) from error
                found[key] = value
    missing = sorted(set(labels.values()) - set(found))
    if missing:
        raise ValidationError(
            f"context header is missing measured source fields: {', '.join(missing)}"
        )
    return found


def _verify_source_summary(
    signals: dict[str, Any], expected_source_summary: dict[str, Any] | None
) -> None:
    if signals.get("skip") or expected_source_summary is None:
        return
    actual = signals["source_summary"]
    mismatches = [
        key
        for key in ("thread_count", "message_count", "window_start", "window_end", "scope")
        if actual.get(key) != expected_source_summary.get(key)
    ]
    if mismatches:
        raise ValidationError(
            "signals.source_summary does not match the collector bundle: "
            + ", ".join(mismatches)
        )


def process_signals(
    signals: dict[str, Any],
    *,
    out_path: Path | None,
    ledger_path: Path,
    update_ledger: bool = True,
    expected_source_summary: dict[str, Any] | None = None,
) -> RunResult:
    """Run the validated pipeline. The delta gate always precedes rendering."""
    validated = validate_signals(signals)
    _verify_source_summary(validated, expected_source_summary)
    ledger_path = Path(ledger_path).expanduser()
    lock = ledger_lock(ledger_path) if update_ledger else nullcontext()
    with lock:
        ledger = load_ledger(ledger_path) if update_ledger else default_ledger()
        if update_ledger and ledger.get("paused"):
            raise PausedError(f"Sunday Letter is paused in {ledger_path}")

        run_date = today_iso()
        if validated.get("skip"):
            if update_ledger:
                ledger["last_run"] = run_date
                ledger["last_status"] = "skipped"
                ledger["last_skip_reason"] = validated["reason"]
                ledger["events"].append(
                    {"date": run_date, "status": "skipped", "reason": validated["reason"]}
                )
                save_ledger(ledger_path, ledger)
                _rebuild_archive(ledger_path)
            return RunResult("skipped", None, None, validated["reason"])

        letter_number = ledger["letter_number"] + 1 if update_ledger else int(
            validated.get("letter_number", 1)
        )
        prepared = deepcopy(validated)
        prepared["letter_number"] = letter_number
        if out_path is None:
            out_path = (
                ledger_path.parent / "letters" / f"{run_date}-letter-{letter_number:02d}.html"
                if update_ledger
                else Path("preview.html")
            )
        out_path = Path(out_path).expanduser()

        if update_ledger:
            archive_root = ensure_private_directory(ledger_path.parent)
            try:
                out_path.resolve().relative_to(archive_root.resolve())
            except ValueError:
                pass
            else:
                ensure_private_directory(out_path.parent)

        rendered = render_letter(
            prepared,
            archive_href=_relative_archive_href(out_path, ledger_path) if update_ledger else None,
            export_href=out_path.name,
        )
        atomic_write_text(out_path, rendered)
        signals_out = out_path.with_suffix(".signals.json")
        if update_ledger:
            atomic_write_text(
                signals_out,
                json.dumps(prepared, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            )

        if update_ledger:
            ledger["letter_number"] = letter_number
            ledger["last_run"] = run_date
            ledger["last_shipped"] = run_date
            ledger["last_status"] = "shipped"
            ledger["last_skip_reason"] = None
            ledger["open_question"] = prepared["question"]
            for retired in prepared["retired"]:
                ledger["retired"].append({**retired, "retired_on": run_date})
            record = {
                "number": letter_number,
                "date": prepared["date"],
                "headline": prepared["hero_headline"],
                "file": _ledger_file_value(out_path, ledger_path),
                "signals_file": _ledger_file_value(signals_out, ledger_path),
                "status": "shipped",
            }
            ledger["letters"].append(record)
            ledger["events"].append({"date": run_date, **record})
            save_ledger(ledger_path, ledger)
            _rebuild_archive(ledger_path)

        return RunResult("shipped", out_path, letter_number)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate, gate, render, and record an agent-local Sunday Letter."
    )
    parser.add_argument("--signals", type=Path, required=True, help="Canonical signals JSON.")
    parser.add_argument(
        "--context",
        type=Path,
        help="Collector bundle used to verify measured source metadata. Required outside preview.",
    )
    parser.add_argument("--out", type=Path, help="Output HTML. Defaults to the local archive.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--ledger", type=Path, help="Defaults to <root>/ledger.json.")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Validate and render without updating the ledger.",
    )
    args = parser.parse_args()

    if not args.preview and args.context is None:
        parser.error("--context is required outside preview mode")

    signals = json.loads(args.signals.read_text())
    expected_source_summary = (
        read_context_source_summary(args.context) if args.context is not None else None
    )
    ledger_path = args.ledger or args.root.expanduser() / "ledger.json"
    result = process_signals(
        signals,
        out_path=args.out,
        ledger_path=ledger_path,
        update_ledger=not args.preview,
        expected_source_summary=expected_source_summary,
    )
    if result.status == "skipped":
        print(f"Skipped: {result.reason}")
    else:
        print(f"Rendered {result.out_path} as letter {result.letter_number}.")


if __name__ == "__main__":
    main()
