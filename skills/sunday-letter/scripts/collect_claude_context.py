#!/usr/bin/env python3
"""
Collect recent Claude Code conversations for a Sunday Letter run.

This reads Claude Code's local session transcripts (JSONL files under
~/.claude/projects). It does not call a network service. The output is plain
Markdown so the weekly Sunday Letter run can read it before extracting signals.

The Codex equivalent is collect_codex_context.py in this same folder.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HOME = Path.home()
DEFAULT_PROJECTS_DIR = HOME / ".claude" / "projects"

# User messages that are host plumbing, not conversation.
SKIP_PREFIXES = (
    "<system-reminder>",
    "<command-name>",
    "<command-message>",
    "<local-command-stdout>",
    "<task-notification>",
    "Caveat: the messages below",
)


@dataclass
class Session:
    id: str
    title: str
    project: str
    updated_at: float
    messages: list[dict[str, str]] = field(default_factory=list)


def _utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _parse_timestamp(value: Any) -> float | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _read_text_parts(content: Any) -> str:
    """Pull human-readable text out of a message content field.

    Content is either a plain string or a list of blocks. Only text blocks
    count; tool_use, tool_result, and thinking blocks are internal machinery.
    """
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "text" and item.get("text"):
            parts.append(str(item["text"]))
    return "\n".join(parts).strip()


def _clean(text: str, limit: int) -> str:
    text = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n...[truncated]"


def parse_session(path: Path, cutoff: float, per_message_limit: int) -> Session | None:
    session = Session(
        id=path.stem,
        title="",
        project=path.parent.name,
        updated_at=path.stat().st_mtime,
    )
    seen: set[tuple[str, str]] = set()

    for line in path.read_text(errors="replace").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue

        kind = item.get("type")
        if kind == "ai-title":
            session.title = item.get("aiTitle") or session.title
            continue
        if kind not in {"user", "assistant"}:
            continue
        if item.get("isSidechain") or item.get("isMeta"):
            continue

        ts = _parse_timestamp(item.get("timestamp"))
        if ts is not None and ts < cutoff:
            continue

        message = item.get("message") or {}
        role = message.get("role")
        if role not in {"user", "assistant"}:
            continue

        text = _read_text_parts(message.get("content"))
        if not text:
            continue
        if role == "user" and text.lstrip().startswith(SKIP_PREFIXES):
            continue

        text = _clean(text, per_message_limit)
        key = (role, text)
        if key in seen:
            continue
        seen.add(key)
        session.messages.append({"role": role, "text": text})

    if not session.messages:
        return None
    if not session.title:
        first_user = next((m for m in session.messages if m["role"] == "user"), None)
        session.title = (first_user["text"].splitlines()[0][:80] if first_user else "Untitled")
    return session


def collect_sessions(projects_dir: Path, days: int, limit: int, per_message_limit: int) -> list[Session]:
    cutoff = time.time() - days * 24 * 60 * 60
    candidates = sorted(
        (p for p in projects_dir.glob("*/*.jsonl") if p.stat().st_mtime >= cutoff),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    sessions: list[Session] = []
    for path in candidates:
        if len(sessions) >= limit:
            break
        session = parse_session(path, cutoff, per_message_limit)
        if session:
            sessions.append(session)
    return sessions


def render_markdown(sessions: list[Session], days: int) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Claude Code Weekly Context",
        "",
        f"Generated: {generated}",
        f"Window: last {days} days",
        f"Sessions found: {len(sessions)}",
        "",
        "## Session Index",
        "",
    ]
    for index, session in enumerate(sessions, start=1):
        lines.append(
            f"{index}. {session.title} - {_utc(session.updated_at)} - {len(session.messages)} messages"
        )
    lines.extend(["", "## Conversations", ""])

    for index, session in enumerate(sessions, start=1):
        lines.extend(
            [
                f"### {index}. {session.title}",
                "",
                f"- Session ID: `{session.id}`",
                f"- Project: `{session.project}`",
                f"- Updated: {_utc(session.updated_at)}",
                "",
            ]
        )
        for message in session.messages:
            role = "User" if message["role"] == "user" else "Assistant"
            lines.extend([f"**{role}:**", "", message["text"], ""])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--limit", type=int, default=80, help="Maximum sessions to include.")
    parser.add_argument("--per-message-limit", type=int, default=5000)
    parser.add_argument(
        "--projects-dir",
        type=Path,
        default=Path(os.environ.get("CLAUDE_PROJECTS_DIR", DEFAULT_PROJECTS_DIR)),
    )
    parser.add_argument("--out", type=Path, default=Path("claude-weekly-context.md"))
    args = parser.parse_args()

    if not args.projects_dir.exists():
        raise SystemExit(f"Claude Code projects directory not found: {args.projects_dir}")

    sessions = collect_sessions(args.projects_dir, args.days, args.limit, args.per_message_limit)
    markdown = render_markdown(sessions, args.days)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(markdown)
    print(f"Wrote {args.out} with {len(sessions)} sessions from the last {args.days} days.")


if __name__ == "__main__":
    main()
