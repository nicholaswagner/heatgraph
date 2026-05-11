"""Regenerate the CLI flag table in docs/CONFIGURATION.md from argparse.

The doc has a marker block:

    <!-- BEGIN GENERATED:cli-flags -->
    ...
    <!-- END GENERATED:cli-flags -->

Everything between the markers is replaced with a freshly rendered usage line
and table built by introspecting heatgraph.cli._build_parser(). Run after
editing CLI flags to keep the docs honest.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from heatgraph.cli import _build_parser  # noqa: E402

DOC_PATH = ROOT / "docs" / "CONFIGURATION.md"
BEGIN = "<!-- BEGIN GENERATED:cli-flags -->"
END = "<!-- END GENERATED:cli-flags -->"


def _flag_label(action: argparse.Action) -> str:
    opts = [o for o in action.option_strings if o.startswith("--")]
    if isinstance(action, argparse.BooleanOptionalAction) and len(opts) == 1:
        return f"`{opts[0]}` / `--no-{opts[0][2:]}`"
    if len(opts) > 1:
        return " / ".join(f"`{o}`" for o in opts)
    return f"`{opts[0]}`"


def _usage_token(action: argparse.Action) -> str:
    primary = next((o for o in action.option_strings if o.startswith("--")), None)
    if primary is None:
        return ""
    if isinstance(action, argparse.BooleanOptionalAction):
        return f"[{primary}/--no-{primary[2:]}]"
    if action.nargs == 0 or isinstance(action, argparse._StoreTrueAction):
        return f"[{primary}]"
    if action.choices:
        return f"[{primary} {'|'.join(action.choices)}]"
    if action.type is float:
        return f"[{primary} F]"
    if action.type is int:
        return f"[{primary} N]"
    return f"[{primary} S]"


def render() -> str:
    parser = _build_parser()
    flags = [a for a in parser._actions if a.option_strings and not isinstance(a, argparse._HelpAction)]

    tokens = [_usage_token(a) for a in flags if _usage_token(a)]
    usage_lines: list[str] = []
    current = "heatgraph"
    indent = " " * len(current)
    for tok in tokens:
        candidate = f"{current} {tok}" if current.strip() else f"{indent} {tok}"
        if len(candidate) > 88 and current.strip() != "heatgraph":
            usage_lines.append(current)
            current = f"{indent} {tok}"
        else:
            current = candidate
    usage_lines.append(current)
    usage_block = "```text\n" + "\n".join(usage_lines) + "\n```"

    rows = ["| Flag | Description |", "|------|-------------|"]
    for a in flags:
        label = _flag_label(a)
        help_text = " ".join((a.help or "").split())
        rows.append(f"| {label} | {help_text} |")
    table = "\n".join(rows)

    return f"{usage_block}\n\n{table}"


def main() -> int:
    body = render()
    doc = DOC_PATH.read_text()
    pattern = re.compile(
        re.escape(BEGIN) + r".*?" + re.escape(END),
        re.DOTALL,
    )
    if not pattern.search(doc):
        print(
            f"error: {DOC_PATH.relative_to(ROOT)} has no "
            f"{BEGIN!r} / {END!r} markers",
            file=sys.stderr,
        )
        return 1
    replacement = f"{BEGIN}\n{body}\n{END}"
    new_doc = pattern.sub(replacement, doc)
    if new_doc == doc:
        print(f"{DOC_PATH.relative_to(ROOT)} already up to date")
        return 0
    DOC_PATH.write_text(new_doc)
    print(f"wrote {DOC_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
