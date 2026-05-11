"""habit_tracker: render a heatgraph of a simple habit log.

Reads a log file with one entry per line::

    YYYY-MM-DD              # counted as 1
    YYYY-MM-DD  COUNT       # explicit count
    # comment lines and blanks are ignored

Multiple entries for the same date are summed. The parsed dates flow through
`heatgraph.helpers.cal_to_matrix` and into the heatgraph renderer.
"""

from __future__ import annotations

import argparse
import datetime
import sys
from typing import IO

from heatgraph import cli as heatgraph_cli
from heatgraph.helpers.cal2matrix import cal_to_matrix


def parse_log(fh: IO[str]) -> dict[str, float]:
    counts: dict[str, float] = {}
    for raw in fh:
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        try:
            datetime.date.fromisoformat(parts[0])
        except (ValueError, IndexError):
            continue
        date = parts[0]
        if len(parts) > 1:
            try:
                count: float = float(parts[1])
            except ValueError:
                continue
        else:
            count = 1.0
        counts[date] = counts.get(date, 0.0) + count
    return counts


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    render_args, demo_argv = heatgraph_cli._build_parser().parse_known_args(argv)
    # if render_args.theme is None:
    #     render_args.theme = "github-dark"

    if render_args.invert_headers is None:
        render_args.invert_headers = False

    if render_args.pad_to_width is None:
        render_args.pad_to_width = True

    if render_args.glyphs is None:
        render_args.glyphs = "square-x"

    if render_args.theme is None:
        render_args.theme = "monokai"

    p = argparse.ArgumentParser(
        prog="heatgraph-demos habit-tracker",
        description=(
            "Render a heatgraph of a simple habit log. "
            "Any heatgraph flag (see `heatgraph --help`) is also accepted "
            "and forwarded to the renderer; --theme defaults to github-dark."
        ),
    )
    p.add_argument(
        "file",
        nargs="?",
        default=None,
        help="Path to habit log (or omit to read from stdin).",
    )
    args = p.parse_args(demo_argv)

    try:
        if args.file:
            with open(args.file) as fh:
                data = parse_log(fh)
        else:
            data = parse_log(sys.stdin)
    except FileNotFoundError:
        sys.stderr.write(f"habit-tracker: file not found: {args.file}\n")
        return 1

    if not data:
        sys.stderr.write("habit-tracker: no dated entries found in log\n")
        return 1

    calendar_doc = {
        "data": data,
        "meta": {
            "message": "[COUNT] / [CELLS] days",
            "legend": "logged activity  [CELL:-1]",
        },
    }
    matrix_doc = cal_to_matrix(calendar_doc)

    output = heatgraph_cli._render_doc(render_args, matrix_doc)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
