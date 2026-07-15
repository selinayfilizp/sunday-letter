from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_build_module():
    path = ROOT / "scripts" / "build_release.py"
    spec = importlib.util.spec_from_file_location("build_release", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ReleaseTests(unittest.TestCase):
    def test_bundle_contains_only_the_supported_codex_path(self) -> None:
        module = load_build_module()
        with tempfile.TemporaryDirectory() as temp:
            bundle = module.build_bundle(Path(temp) / "sunday-letter-codex.plugin")
            with zipfile.ZipFile(bundle) as archive:
                names = set(archive.namelist())
        self.assertIn(".codex-plugin/plugin.json", names)
        self.assertIn("skills/sunday-letter/references/signals.schema.json", names)
        self.assertIn("skills/sunday-letter/scripts/manage_archive.py", names)
        self.assertFalse(any("claude" in name.lower() for name in names))

    def test_bundle_is_deterministic(self) -> None:
        module = load_build_module()
        with tempfile.TemporaryDirectory() as temp:
            first = module.build_bundle(Path(temp) / "first.plugin")
            second = module.build_bundle(Path(temp) / "second.plugin")
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_sample_build_preserves_social_metadata(self) -> None:
        module = load_build_module()
        with tempfile.TemporaryDirectory() as temp:
            sample = module.build_sample(Path(temp) / "sample-letter.html")
            html = sample.read_text()

        self.assertIn('<meta name="twitter:card" content="summary_large_image">', html)
        self.assertIn('<meta property="og:image"', html)
        self.assertIn("Local agent sources only", html)
        self.assertNotIn("recent Codex conversations", html)

    def test_manifest_and_public_version_match(self) -> None:
        manifests = [
            ROOT / ".codex-plugin" / "plugin.json",
            ROOT / ".claude-plugin" / "plugin.json",
            ROOT / ".claude-plugin" / "marketplace.json",
        ]
        for path in manifests:
            manifest = json.loads(path.read_text())
            version = manifest.get("version") or manifest["metadata"]["version"]
            self.assertEqual(version, "0.4.0", path)
        self.assertIn("v0.4.0", (ROOT / "docs" / "index.html").read_text())

    def test_landing_intro_is_fast_and_decorative(self) -> None:
        html = (ROOT / "docs" / "index.html").read_text()
        self.assertIn('class="vortex-stage" aria-hidden="true"', html)
        self.assertIn("window.setTimeout(openLetter, 1500)", html)
        self.assertNotIn("window.setTimeout(openLetter, 4300)", html)

    def test_subscription_commands_cover_both_host_skill_paths(self) -> None:
        commands = (ROOT / "commands" / "subscribe-sunday-letter.md").read_text()
        self.assertIn('${CODEX_HOME:-$HOME/.codex}/skills/sunday-letter', commands)
        self.assertIn('${CLAUDE_HOME:-$HOME/.claude}/skills/sunday-letter', commands)


if __name__ == "__main__":
    unittest.main()
