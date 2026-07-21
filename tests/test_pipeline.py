from __future__ import annotations

import json
import multiprocessing
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "sunday-letter" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import core  # noqa: E402
import generate_letter  # noqa: E402


def _concurrent_ship(
    root: str,
    signals: dict,
    start: object,
    results: object,
) -> None:
    start.wait(10)
    try:
        result = generate_letter.process_signals(
            signals,
            out_path=None,
            ledger_path=Path(root) / "ledger.json",
            allow_duplicate_week=True,
        )
    except Exception as error:  # pragma: no cover - reported to the parent process
        results.put(("error", repr(error)))
    else:
        results.put(("ok", result.letter_number))


def valid_signals() -> dict:
    return {
        "schema_version": "1.0",
        "name": "Selin",
        "date": "Jul 14, 2026",
        "hero_headline": "A useful shift.",
        "hero_lede": "I finished <strong>two concrete things</strong> this week.",
        "source_summary": {
            "thread_count": 2,
            "message_count": 8,
            "window_start": "2026-07-07T00:00:00Z",
            "window_end": "2026-07-14T00:00:00Z",
            "scope": "selected local agent conversations",
        },
        "consequences": [
            {
                "tag": "Built",
                "title": "Made the renderer safer.",
                "body": "Removed executable markup.",
                "because": "The archive is meant to be trustworthy.",
                "provenance": "Jul 14 · Sunday Letter project",
            },
            {
                "tag": "Fixed",
                "title": "Made silence enforceable.",
                "body": "Skip payloads no longer render.",
                "because": "No delta means no letter.",
                "provenance": "Jul 14 · Sunday Letter project",
            },
        ],
        "decisions": [],
        "open_tasks": [],
        "observations": [
            {
                "hedge_class": "soft",
                "hedge_label": "Still checking",
                "learned_date": "Jul 14",
                "title": "You prefer product truth over polish.",
                "body": "The implementation should earn the promise.",
                "evidence": "Start the improvements with the trust boundary.",
                "provenance": "Jul 14 · project review follow-up",
            }
        ],
        "retired": [],
        "gap": None,
        "becoming": None,
        "question": "Which promise should become measurable next?",
        "question_note": "One answer is enough.",
        "closing_line": "Until next week,",
        "signoff": "your attentive agent",
    }


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.ledger = self.root / "ledger.json"
        self.letters = self.root / "letters"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_skip_updates_ledger_without_rendering(self) -> None:
        out = self.letters / "should-not-exist.html"
        result = generate_letter.process_signals(
            {"schema_version": "1.0", "skip": True, "reason": "no meaningful delta"},
            out_path=out,
            ledger_path=self.ledger,
        )

        self.assertEqual(result.status, "skipped")
        self.assertFalse(out.exists())
        ledger = json.loads(self.ledger.read_text())
        self.assertEqual(ledger["letter_number"], 0)
        self.assertEqual(ledger["last_status"], "skipped")
        self.assertEqual(ledger["events"][-1]["status"], "skipped")

    def test_ship_sanitizes_html_and_updates_ledger(self) -> None:
        signals = valid_signals()
        signals["hero_lede"] = '<script id="probe">alert(1)</script><strong>kept</strong>'
        signals["observations"][0]["evidence"] = '<img src=x onerror=alert(1)> evidence'
        out = self.letters / "letter.html"

        result = generate_letter.process_signals(signals, out_path=out, ledger_path=self.ledger)

        self.assertEqual(result.status, "shipped")
        rendered = out.read_text()
        self.assertTrue(out.with_suffix(".signals.json").exists())
        self.assertNotIn('<script id="probe">', rendered)
        self.assertNotIn("<img", rendered)
        self.assertIn("&lt;script", rendered)
        self.assertIn("<strong>kept</strong>", rendered)
        self.assertIn("selected local agent conversations", rendered)
        self.assertNotIn("recent Codex conversations", rendered)
        ledger = json.loads(self.ledger.read_text())
        self.assertEqual(ledger["letter_number"], 1)
        self.assertEqual(ledger["last_status"], "shipped")
        self.assertEqual(ledger["letters"][0]["file"], "letters/letter.html")

    def test_runtime_owns_sequential_letter_number(self) -> None:
        first = valid_signals()
        first["letter_number"] = 99
        result1 = generate_letter.process_signals(
            first,
            out_path=self.letters / "one.html",
            ledger_path=self.ledger,
        )
        result2 = generate_letter.process_signals(
            valid_signals(),
            out_path=self.letters / "two.html",
            ledger_path=self.ledger,
            allow_duplicate_week=True,
        )

        self.assertEqual(result1.letter_number, 1)
        self.assertEqual(result2.letter_number, 2)
        self.assertIn("Letter №1", (self.letters / "one.html").read_text())
        self.assertIn("Letter №2", (self.letters / "two.html").read_text())

    def test_concurrent_hosts_receive_unique_letter_numbers(self) -> None:
        context = multiprocessing.get_context("fork")
        start = context.Event()
        results = context.Queue()
        workers = [
            context.Process(
                target=_concurrent_ship,
                args=(str(self.root), valid_signals(), start, results),
            )
            for _ in range(4)
        ]
        for worker in workers:
            worker.start()
        start.set()
        for worker in workers:
            worker.join(20)
            self.assertFalse(worker.is_alive(), "concurrent letter generation deadlocked")
            self.assertEqual(worker.exitcode, 0)

        outcomes = [results.get(timeout=2) for _ in workers]
        self.assertFalse([value for status, value in outcomes if status == "error"])
        numbers = sorted(value for status, value in outcomes if status == "ok")
        self.assertEqual(numbers, [1, 2, 3, 4])

        ledger = json.loads(self.ledger.read_text())
        self.assertEqual(ledger["letter_number"], 4)
        self.assertEqual(len(ledger["letters"]), 4)
        for record in ledger["letters"]:
            self.assertTrue((self.root / record["file"]).exists())

    def test_duplicate_week_guard_blocks_second_ship(self) -> None:
        generate_letter.process_signals(
            valid_signals(), out_path=self.letters / "one.html", ledger_path=self.ledger
        )
        with self.assertRaises(generate_letter.DuplicateWeekError):
            generate_letter.process_signals(
                valid_signals(), out_path=self.letters / "two.html", ledger_path=self.ledger
            )
        skipped = generate_letter.process_signals(
            {"schema_version": "1.0", "skip": True, "reason": "no meaningful delta"},
            out_path=None,
            ledger_path=self.ledger,
        )
        self.assertEqual(skipped.status, "skipped")

    def test_duplicate_week_guard_allows_after_window(self) -> None:
        generate_letter.process_signals(
            valid_signals(), out_path=self.letters / "one.html", ledger_path=self.ledger
        )
        ledger = json.loads(self.ledger.read_text())
        ledger["last_shipped"] = "2020-01-01"
        self.ledger.write_text(json.dumps(ledger))
        result = generate_letter.process_signals(
            valid_signals(), out_path=self.letters / "two.html", ledger_path=self.ledger
        )
        self.assertEqual(result.status, "shipped")

    def test_letter_and_ledger_carry_verified_source_scope(self) -> None:
        out = self.letters / "letter.html"
        generate_letter.process_signals(valid_signals(), out_path=out, ledger_path=self.ledger)
        self.assertIn("selected local agent conversations", out.read_text())
        self.assertNotIn("Local agent sources only", out.read_text())
        ledger = json.loads(self.ledger.read_text())
        self.assertEqual(ledger["letters"][0]["source"], "selected local agent conversations")

    def test_validation_rejects_unmeasured_metrics(self) -> None:
        signals = valid_signals()
        signals["calibration_pct"] = 81
        with self.assertRaises(core.ValidationError):
            core.validate_signals(signals)

    def test_validation_requires_observation_provenance(self) -> None:
        signals = valid_signals()
        del signals["observations"][0]["provenance"]
        with self.assertRaises(core.ValidationError):
            core.validate_signals(signals)

    def test_validation_rejects_invalid_source_window(self) -> None:
        signals = valid_signals()
        signals["source_summary"]["window_start"] = "not-a-date"
        with self.assertRaises(core.ValidationError):
            core.validate_signals(signals)

    def test_source_summary_must_match_collector_metadata(self) -> None:
        signals = valid_signals()
        expected = dict(signals["source_summary"])
        expected["message_count"] += 1
        with self.assertRaises(core.ValidationError):
            generate_letter.process_signals(
                signals,
                out_path=self.letters / "mismatch.html",
                ledger_path=self.ledger,
                expected_source_summary=expected,
            )
        self.assertFalse((self.letters / "mismatch.html").exists())

    def test_preview_ignores_paused_ledger_and_writes_no_sidecar(self) -> None:
        core.save_ledger(self.ledger, {**core.default_ledger(), "paused": True})
        out = self.root / "preview.html"

        result = generate_letter.process_signals(
            valid_signals(),
            out_path=out,
            ledger_path=self.ledger,
            update_ledger=False,
        )

        self.assertEqual(result.status, "shipped")
        self.assertTrue(out.exists())
        self.assertFalse(out.with_suffix(".signals.json").exists())
        self.assertNotIn(">Archive</a>", out.read_text())

    def test_paused_ledger_blocks_shipping(self) -> None:
        core.save_ledger(self.ledger, {**core.default_ledger(), "paused": True})
        with self.assertRaises(generate_letter.PausedError):
            generate_letter.process_signals(
                valid_signals(),
                out_path=self.letters / "paused.html",
                ledger_path=self.ledger,
            )

    def test_ledger_drops_unknown_legacy_metrics(self) -> None:
        legacy = {
            **core.default_ledger(),
            "tracking_conversations": 200,
            "hours_saved": 14,
        }
        self.ledger.write_text(json.dumps(legacy))

        loaded = core.load_ledger(self.ledger)
        core.save_ledger(self.ledger, loaded)

        persisted = json.loads(self.ledger.read_text())
        self.assertNotIn("tracking_conversations", persisted)
        self.assertNotIn("hours_saved", persisted)

    def test_cli_verifies_context_then_ships_to_archive(self) -> None:
        signals = valid_signals()
        signals_path = self.root / "signals.json"
        signals_path.write_text(json.dumps(signals))
        summary = signals["source_summary"]
        context = self.root / "context.md"
        context.write_text(
            "\n".join(
                [
                    "# Codex Weekly Context",
                    f"Window start: {summary['window_start']}",
                    f"Window end: {summary['window_end']}",
                    f"Source scope: {summary['scope']}",
                    f"Threads included: {summary['thread_count']}",
                    f"Messages included: {summary['message_count']}",
                    "",
                    "> BEGIN TRANSCRIPT DATA",
                    "> END TRANSCRIPT DATA",
                ]
            )
        )

        subprocess.run(
            [
                sys.executable,
                str(ROOT / "generate_letter.py"),
                "--signals",
                str(signals_path),
                "--context",
                str(context),
                "--root",
                str(self.root / "archive"),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        archive = self.root / "archive"
        self.assertTrue((archive / "ledger.json").exists())
        self.assertEqual(len(list((archive / "letters").glob("*.html"))), 1)
        self.assertEqual((archive.stat().st_mode & 0o777), 0o700)


if __name__ == "__main__":
    unittest.main()
