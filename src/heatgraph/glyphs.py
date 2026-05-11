"""Glyph preset resolution and the default glyph set.

Presets are stored in ``glyphs.json`` next to this module. ``resolve_glyphs``
accepts either a JSON-array string (parsed inline) or a preset name (looked
up in the registry).
"""
from __future__ import annotations

import json
import os


DEFAULT_GLYPHS = ["•", "\033[2m▨\033[22m", "\033[2m▦\033[22m", "\033[2m▦\033[22m", "\033[1m▦\033[22m"]


_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "glyphs.json")


def resolve_glyphs(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        pass
    try:
        with open(_REGISTRY_PATH) as f:
            registry = json.load(f)
        return registry.get(raw)
    except Exception:
        return None
