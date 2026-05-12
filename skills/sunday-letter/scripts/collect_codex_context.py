#!/usr/bin/env python3
"""
Collect recent Codex Desktop conversations for a Sunday Letter run.

This reads Codex's local thread database and rollout JSONL files. It does not
call a network service. The output is intentionally plain Markdown so the
scheduled Codex job can read it before extracting Sunday Letter signals.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HOME = Path.home()
DEFAULT_CODEX_HOME = HOME / ".codex"
DEFAULT_DB = DEFAULT_CODEX_HOME / "state_5.sqlite"


@dataclass
class ThreadRow:
    id: str
    title: str
    updated_at: int
    rollout_path: Path
    first_user_message: str


def _utc(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _read_text_parts(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("text") or item.get("input_text") or item.get("output_text")
        if text:
            parts.append(str(text))
    return "\n".join(parts).strip()


def _clean(text: str, limit: int) -> str:
    text = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n...[truncated]"


def query_threads(db_path: Path, days: int, limit: int) -> list[ThreadRow]:
    cutoff = int(time.time()) - days * 24 * 60 * 60
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            select id, title, updated_at, rollout_path, first_user_message
            from threads
            where updated_at >= ?
              and rollout_path != ''
            order by updated_at desc
            limit ?
            """,
            (cutoff, limit),
        ).fetchall()
    finally:
        conn.close()
    return [
        ThreadRow(
            id=row["id"],
            title=row["title"] or "Untitled",
            updated_at=int(row["updated_at"]),
            rollout_path=Path(row["rollout_path"]),
            first_user_message=row["first_user_message"] or "",
        )
        for row in rows
    ]


def parse_rollout(path: Path, per_message_limit: int) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    if not path.exists():
        return messages

    for line in path.read_text(errors="replace").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("type") != "response_item":
            continue
        payload = item.get("payload") or {}
        if payload.get("type") != "message":
            continue
        role = payload.get("role")
        if role not in {"user", "assistant"}:
            continue
        phase = payload.get("phase") or ""
        if role == "assistant" and phase != "final_answer":
            continue
        text = _read_text_parts(payload.get("content"))
        if not text:
            continue
        if role == "user" and text.lstrip().startswith("<environment_context>"):
            continue
        text = _clean(text, per_message_limit)
        key = (role, text)
        if key in seen:
            continue
        seen.add(key)
        messages.append({"role": role, "text": text})
    return messages


def render_markdown(threads: list[ThreadRow], messages_by_thread: dict[str, list[dict[str, str]]], days: int) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Codex Weekly Context",
        "",
        f"Generated: {generated}",
        f"Window: last {days} days",
        f"Threads found: {len(threads)}",
        "",
        "## Thread Index",
        "",
    ]
    for index, thread in enumerate(threads, start=1):
        count = len(messages_by_thread.get(thread.id, []))
        lines.append(f"{index}. {thread.title} - {_utc(thread.updated_at)} - {count} messages")
    lines.extend(["", "## Conversations", ""])

    for index, thread in enumerate(threads, start=1):
        messages = messages_by_thread.get(thread.id, [])
        if not messages:
            continue
        lines.extend(
            [
                f"### {index}. {thread.title}",
                "",
                f"- Thread ID: `{thread.id}`",
                f"- Updated: {_utc(thread.updated_at)}",
                f"- Source: `{thread.rollout_path}`",
                "",
            ]
        )
        for message in messages:
            role = "User" if message["role"] == "user" else "Assistant"
            lines.extend([f"**{role}:**", "", message["text"], ""])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--limit", type=int, default=80, help="Maximum threads to include.")
    parser.add_argument("--per-message-limit", type=int, default=5000)
    parser.add_argument("--db", type=Path, default=Path(os.environ.get("CODEX_STATE_DB", DEFAULT_DB)))
    parser.add_argument("--out", type=Path, default=Path("codex-weekly-context.md"))
    args = parser.parse_args()

    if not args.db.exists():
        raise SystemExit(f"Codex state database not found: {args.db}")

    threads = query_threads(args.db, args.days, args.limit)
    messages_by_thread = {
        thread.id: parse_rollout(thread.rollout_path, args.per_message_limit)
        for thread in threads
    }
    markdown = render_markdown(threads, messages_by_thread, args.days)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(markdown)
    included = sum(1 for value in messages_by_thread.values() if value)
    print(f"Wrote {args.out} with {included}/{len(threads)} threads containing readable messages.")


if __name__ == "__main__":
    main()
