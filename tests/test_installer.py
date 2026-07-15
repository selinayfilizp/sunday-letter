from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def test_codex_target_installs_codex_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            env = {**os.environ, "HOME": str(home)}
            subprocess.run([str(ROOT / "install.sh"), "codex"], cwd=ROOT, env=env, check=True)

            self.assertTrue((home / ".codex" / "skills" / "sunday-letter" / "SKILL.md").exists())
            self.assertTrue((home / ".codex" / "prompts" / "sunday-letter.md").exists())
            self.assertFalse((home / ".claude").exists())
            self.assertFalse(
                any((home / ".codex" / "skills" / "sunday-letter").rglob("__pycache__"))
            )

    def test_claude_target_installs_claude_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            env = {**os.environ, "HOME": str(home)}
            subprocess.run([str(ROOT / "install.sh"), "claude"], cwd=ROOT, env=env, check=True)

            self.assertTrue((home / ".claude" / "skills" / "sunday-letter" / "SKILL.md").exists())
            self.assertTrue(
                (
                    home
                    / ".claude"
                    / "skills"
                    / "sunday-letter"
                    / "scripts"
                    / "collect_claude_context.py"
                ).exists()
            )
            self.assertTrue((home / ".claude" / "commands" / "sunday-letter.md").exists())
            self.assertFalse((home / ".codex").exists())
            self.assertFalse(
                any((home / ".claude" / "skills" / "sunday-letter").rglob("__pycache__"))
            )

    def test_default_installs_every_agent_home_found(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home / ".codex").mkdir()
            (home / ".claude").mkdir()
            env = {**os.environ, "HOME": str(home)}
            subprocess.run([str(ROOT / "install.sh")], cwd=ROOT, env=env, check=True)

            self.assertTrue((home / ".codex" / "skills" / "sunday-letter" / "SKILL.md").exists())
            self.assertTrue((home / ".claude" / "skills" / "sunday-letter" / "SKILL.md").exists())

    def test_default_fails_when_no_agent_home_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            result = subprocess.run(
                [str(ROOT / "install.sh")],
                cwd=ROOT,
                env={**os.environ, "HOME": str(home)},
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Neither", result.stderr)

    def test_rejects_unknown_install_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            result = subprocess.run(
                [str(ROOT / "install.sh"), "chatgpt"],
                cwd=ROOT,
                env={**os.environ, "HOME": str(home)},
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("usage", result.stderr)
            self.assertFalse((home / ".codex").exists())
            self.assertFalse((home / ".claude").exists())


if __name__ == "__main__":
    unittest.main()
