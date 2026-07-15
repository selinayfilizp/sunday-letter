#!/usr/bin/env python3
"""Top-level wrapper for the agent-local Sunday Letter archive manager."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


SCRIPT = Path(__file__).parent / "skills" / "sunday-letter" / "scripts" / "manage_archive.py"

if __name__ == "__main__":
    sys.path.insert(0, str(SCRIPT.parent))
    runpy.run_path(str(SCRIPT), run_name="__main__")
