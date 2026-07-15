#!/usr/bin/env python3
"""Build the deterministic Codex plugin bundle and canonical sample letter."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "sunday-letter-codex.plugin"
DEFAULT_SAMPLE = ROOT / "docs" / "sample-letter.html"
INCLUDE = (
    Path("CHANGELOG.md"),
    Path("LICENSE"),
    Path("README.md"),
    Path("SECURITY.md"),
    Path("install.sh"),
    Path("generate_letter.py"),
    Path("manage_archive.py"),
    Path(".codex-plugin"),
    Path("commands"),
    Path("skills"),
)


# The Codex bundle ships the Codex reference path only. Claude Code users
# install from the repository (install.sh claude) or the plugin marketplace.
EXCLUDE_NAMES = frozenset({"collect_claude_context.py"})

SAMPLE_SOCIAL_METADATA = """<meta property="og:type" content="website">
<meta property="og:title" content="A sample Sunday Letter">
<meta property="og:description" content="A rendered example of the weekly letter: consequences, calibrated observations, one retired belief, one question.">
<meta property="og:url" content="https://selinayfilizp.github.io/sunday-letter/sample-letter.html">
<meta property="og:image" content="https://selinayfilizp.github.io/sunday-letter/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="A sample Sunday Letter">
<meta name="twitter:description" content="A rendered example of the weekly letter: consequences, calibrated observations, one retired belief, one question.">
<meta name="twitter:image" content="https://selinayfilizp.github.io/sunday-letter/og.png">"""


def _files() -> list[Path]:
    files: list[Path] = []
    for relative in INCLUDE:
        path = ROOT / relative
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(
                candidate
                for candidate in path.rglob("*")
                if candidate.is_file()
                and "__pycache__" not in candidate.parts
                and candidate.suffix != ".pyc"
                and candidate.name != ".DS_Store"
                and candidate.name not in EXCLUDE_NAMES
            )
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def build_bundle(out_path: Path) -> Path:
    out_path = out_path.expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(out_path, "w", ZIP_DEFLATED) as archive:
        for path in _files():
            relative = path.relative_to(ROOT).as_posix()
            info = ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
            info.external_attr = mode << 16
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    return out_path


def build_sample(out_path: Path) -> Path:
    out_path = out_path.expanduser().resolve()
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "generate_letter.py"),
            "--signals",
            str(ROOT / "skills/sunday-letter/references/example-signals.json"),
            "--preview",
            "--out",
            str(out_path),
        ],
        cwd=ROOT,
        check=True,
    )
    out_path.with_suffix(".signals.json").unlink(missing_ok=True)
    rendered = out_path.read_text(encoding="utf-8")
    description = '<meta name="description"'
    if description not in rendered:
        raise RuntimeError("sample renderer did not produce the expected description metadata")
    rendered = rendered.replace(description, f"{SAMPLE_SOCIAL_METADATA}\n{description}", 1)
    out_path.write_text(rendered, encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--sample", type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument("--skip-sample", action="store_true")
    args = parser.parse_args()
    if not args.skip_sample:
        print(f"Built sample: {build_sample(args.sample)}")
    print(f"Built bundle: {build_bundle(args.out)}")


if __name__ == "__main__":
    main()
