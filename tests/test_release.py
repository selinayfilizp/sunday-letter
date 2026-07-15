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

    def test_manifest_and_public_version_match(self) -> None:
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())
        self.assertEqual(manifest["version"], "0.4.0")
        self.assertIn("v0.4.0", (ROOT / "docs" / "index.html").read_text())


if __name__ == "__main__":
    unittest.main()
