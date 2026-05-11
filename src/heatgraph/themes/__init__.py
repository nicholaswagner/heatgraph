"""Theme loading and the default ANSI color palette.

Theme files (``<name>.json``) live alongside this module. ``load_theme(name)``
first looks for a packaged theme by that name, then falls back to treating the
argument as a filesystem path. All keys in a theme JSON are optional.
"""
from __future__ import annotations

import json
import os
from typing import Any


# Standard 16 terminal palette colors (foreground)
C0  = "\033[38;5;0m"   # black
C1  = "\033[38;5;1m"   # red
C2  = "\033[38;5;2m"   # green
C3  = "\033[38;5;3m"   # yellow
C4  = "\033[38;5;4m"   # blue
C5  = "\033[38;5;5m"   # magenta
C6  = "\033[38;5;6m"   # cyan
C7  = "\033[38;5;7m"   # white
C8  = "\033[38;5;8m"   # bright black
C9  = "\033[38;5;9m"   # bright red
C10 = "\033[38;5;10m"  # bright green
C11 = "\033[38;5;11m"  # bright yellow
C12 = "\033[38;5;12m"  # bright blue
C13 = "\033[38;5;13m"  # bright magenta
C14 = "\033[38;5;14m"  # bright cyan
C15 = "\033[38;5;15m"  # bright white


DEFAULT_COLORS_DARK = [C8, C8, C5, C4, C12]
DEFAULT_COLORS_LIGHT = [C15, C10, C2, C4, C4]
DEFAULT_COLORS = DEFAULT_COLORS_DARK


_PACKAGE_DIR = os.path.dirname(__file__)


def load_theme(name: str | None) -> dict[str, Any]:
    if not name:
        return {}
    candidates = [
        os.path.join(_PACKAGE_DIR, f"{name}.json"),
        name,
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception:
                pass
    return {}
