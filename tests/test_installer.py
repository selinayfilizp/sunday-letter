from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def test_installs_only_the_codex_reference_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            env = {**os.environ, "HOME": str(home)}
            subprocess.run([str(ROOT / "install.sh")], cwd=ROOT, env=env, check=True)

            self.assertTrue((home / ".codex" / "skills" / "sunday-letter" / "SKILL.md").exists())
            self.assertTrue((home / ".codex" / "prompts" / "sunday-letter.md").exists())
            self.assertFalse((home / ".claude").exists())
            self.assertFalse(
                any((home / ".codex" / "skills" / "sunday-letter").rglob("__pycache__"))
            )

    def test_rejects_unsupported_install_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            result = subprocess.run(
                [str(ROOT / "install.sh"), "claude"],
                cwd=ROOT,
                env={**os.environ, "HOME": str(home)},
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("only supported reference path", result.stderr)
            self.assertFalse((home / ".codex").exists())


if __name__ == "__main__":
    unittest.main()
