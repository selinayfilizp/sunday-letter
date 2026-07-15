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
    Path("LICENSE"),
    Path("README.md"),
    Path("install.sh"),
    Path("generate_letter.py"),
    Path("manage_archive.py"),
    Path(".codex-plugin"),
    Path("commands"),
    Path("skills"),
)


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
