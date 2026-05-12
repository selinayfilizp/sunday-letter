#!/usr/bin/env python3
"""Top-level wrapper for the Sunday Letter renderer."""

from __future__ import annotations

import runpy
from pathlib import Path


SCRIPT = Path(__file__).parent / "skills" / "sunday-letter" / "scripts" / "generate_letter.py"

if __name__ == "__main__":
    runpy.run_path(str(SCRIPT), run_name="__main__")
