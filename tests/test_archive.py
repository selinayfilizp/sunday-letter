from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "sunday-letter" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import core  # noqa: E402
import manage_archive  # noqa: E402


class ArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "letters").mkdir()
        (self.root / "letters" / "letter-1.html").write_text("<html>one</html>")
        ledger = core.default_ledger()
        ledger.update(
            {
                "letter_number": 1,
                "letters": [
                    {
                        "number": 1,
                        "date": "Jul 14, 2026",
                        "headline": "One <script>bad</script>",
                        "file": "letters/letter-1.html",
                        "status": "shipped",
                    }
                ],
                "events": [
                    {
                        "date": "Jul 7, 2026",
                        "status": "skipped",
                        "reason": "no meaningful delta",
                    }
                ],
            }
        )
        core.save_ledger(self.root / "ledger.json", ledger)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_build_archive_has_real_navigation_and_actions(self) -> None:
        index = manage_archive.build_archive(self.root)
        html = index.read_text()
        self.assertIn("letters/letter-1.html", html)
        self.assertIn("/action/pause", html)
        self.assertIn("/action/delete", html)
        self.assertIn("/export.zip", html)
        self.assertNotIn("<script>bad</script>", html)

    def test_pause_resume_export_and_delete(self) -> None:
        manage_archive.set_paused(self.root, True)
        self.assertTrue(json.loads((self.root / "ledger.json").read_text())["paused"])
        manage_archive.set_paused(self.root, False)
        self.assertFalse(json.loads((self.root / "ledger.json").read_text())["paused"])

        exported = manage_archive.export_archive(self.root, self.root / "export.zip")
        with zipfile.ZipFile(exported) as archive:
            self.assertIn("ledger.json", archive.namelist())
            self.assertIn("letters/letter-1.html", archive.namelist())

        manage_archive.delete_letter(self.root, "letters/letter-1.html")
        self.assertFalse((self.root / "letters" / "letter-1.html").exists())
        self.assertEqual(json.loads((self.root / "ledger.json").read_text())["letters"], [])

    def test_delete_rejects_path_traversal(self) -> None:
        with self.assertRaises(ValueError):
            manage_archive.delete_letter(self.root, "../outside.html")

    def test_archive_omits_unsafe_ledger_links(self) -> None:
        ledger = core.load_ledger(self.root / "ledger.json")
        ledger["letters"].append(
            {
                "number": 2,
                "date": "Jul 14, 2026",
                "headline": "Unsafe",
                "file": "javascript:alert(1)",
                "status": "shipped",
            }
        )
        core.save_ledger(self.root / "ledger.json", ledger)

        html = manage_archive.build_archive(self.root).read_text()

        self.assertNotIn("javascript:", html)

    def test_server_rejects_non_loopback_binding(self) -> None:
        with self.assertRaises(ValueError):
            manage_archive.serve_archive(self.root, "0.0.0.0", 8765)


if __name__ == "__main__":
    unittest.main()
