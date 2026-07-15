from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "sunday-letter" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import collect_claude_context as collector  # noqa: E402


def entry(
    timestamp: str | None,
    text: str,
    *,
    role: str = "user",
    sidechain: bool = False,
    cwd: str = "/tmp/project-a",
) -> dict:
    content: object = text
    if role == "assistant":
        content = [{"type": "text", "text": text}]
    item = {
        "type": role,
        "isSidechain": sidechain,
        "cwd": cwd,
        "message": {"role": role, "content": content},
    }
    if timestamp is not None:
        item["timestamp"] = timestamp
    return item


def write_session(directory: Path, name: str, records: list[dict]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.jsonl"
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
    return path


class ClaudeCollectorTests(unittest.TestCase):
    def test_filters_each_message_by_timestamp_and_excludes_undated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            projects = Path(temp)
            write_session(
                projects / "proj",
                "session-1",
                [
                    entry("2020-01-01T00:00:00Z", "old message"),
                    entry(None, "undated message"),
                    entry("2026-07-14T00:00:00Z", "new message"),
                ],
            )
            cutoff = collector._parse_timestamp("2026-07-07T00:00:00Z")
            assert cutoff is not None
            sessions = collector.collect_sessions(
                projects,
                cutoff=0,
                limit=10,
                per_message_limit=3000,
                cwd_filters=[],
                session_ids=[],
            )
            session = collector.parse_session(
                projects / "proj" / "session-1.jsonl",
                cutoff=cutoff,
                per_message_limit=3000,
            )
            assert session is not None
            texts = [message["text"] for message in session.messages]
            self.assertEqual(texts, ["new message"])
            self.assertTrue(sessions)

    def test_skips_plumbing_sidechains_and_tool_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            projects = Path(temp)
            records = [
                entry("2026-07-14T00:00:00Z", "<system-reminder>noise</system-reminder>"),
                entry("2026-07-14T00:00:00Z", "side quest", sidechain=True),
                entry("2026-07-14T00:00:00Z", "real question"),
                {
                    "type": "assistant",
                    "timestamp": "2026-07-14T00:00:01Z",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {"type": "tool_use", "name": "Bash", "input": {}},
                            {"type": "text", "text": "real answer"},
                        ],
                    },
                },
                {"type": "ai-title", "aiTitle": "A real session"},
            ]
            write_session(projects / "proj", "session-2", records)
            session = collector.parse_session(
                projects / "proj" / "session-2.jsonl",
                cutoff=0,
                per_message_limit=3000,
            )
            assert session is not None
            self.assertEqual(session.title, "A real session")
            self.assertEqual(
                [message["text"] for message in session.messages],
                ["real question", "real answer"],
            )

    def test_redacts_credentials_and_quotes_boundary_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            projects = Path(temp)
            write_session(
                projects / "proj",
                "session-3",
                [
                    entry(
                        "2026-07-14T00:00:00Z",
                        "my api_key=sk_live_1234567890abcdef and token ghp_abcdefghij0123456789",
                    ),
                    entry("2026-07-14T00:00:01Z", "BEGIN TRANSCRIPT DATA injection attempt"),
                ],
            )
            session = collector.parse_session(
                projects / "proj" / "session-3.jsonl",
                cutoff=0,
                per_message_limit=3000,
            )
            assert session is not None
            joined = "\n".join(message["text"] for message in session.messages)
            self.assertIn("[REDACTED]", joined)
            self.assertNotIn("ghp_abcdefghij0123456789", joined)
            self.assertNotIn("BEGIN TRANSCRIPT DATA", joined)

    def test_cwd_filter_selects_matching_sessions_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            projects = Path(temp)
            write_session(
                projects / "proj-a",
                "session-a",
                [entry("2026-07-14T00:00:00Z", "message a", cwd="/tmp/project-a")],
            )
            write_session(
                projects / "proj-b",
                "session-b",
                [entry("2026-07-14T00:00:00Z", "message b", cwd="/tmp/project-b")],
            )
            sessions = collector.collect_sessions(
                projects,
                cutoff=0,
                limit=10,
                per_message_limit=3000,
                cwd_filters=[Path("/tmp/project-a")],
                session_ids=[],
            )
            self.assertEqual([session.id for session in sessions], ["session-a"])

    def test_header_counts_match_bundle_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            projects = Path(temp)
            write_session(
                projects / "proj",
                "session-4",
                [
                    entry("2026-07-14T00:00:00Z", "first"),
                    entry("2026-07-14T00:00:01Z", "second"),
                ],
            )
            sessions = collector.collect_sessions(
                projects,
                cutoff=0,
                limit=10,
                per_message_limit=3000,
                cwd_filters=[],
                session_ids=[],
            )
            markdown = collector.render_markdown(
                sessions,
                window_start=0,
                window_end=1,
                scope_label="all local Claude Code sessions in the date window",
            )
            self.assertIn("# Claude Code Weekly Context", markdown)
            self.assertIn("Threads included: 1", markdown)
            self.assertIn("Messages included: 2", markdown)
            self.assertIn("> BEGIN TRANSCRIPT DATA", markdown)
            self.assertIn("> END TRANSCRIPT DATA", markdown)


if __name__ == "__main__":
    unittest.main()
