"""heatgraph CLI: stdin -> validate -> render -> stdout."""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from heatgraph.colors import resolve_color
from heatgraph.glyphs import resolve_glyphs
from heatgraph.render import RenderConfig, render
from heatgraph.schema import SchemaError, validate_matrix_doc
from heatgraph.themes import load_theme

# Cursor home + erase-from-cursor-to-end. Used between frames in --follow mode
# so the terminal redraws in place instead of accumulating scrollback.
CLEAR_HOME = "\x1b[H\x1b[J"


def _terminal_width() -> int | None:
    try:
        return os.get_terminal_size().columns - 1
    except OSError:
        return None


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="heatgraph",
        description="Render a matrix doc from stdin as a terminal heatgraph.",
    )
    p.add_argument(
        "--theme",
        default=None,
        help="Named theme (see docs/CUSTOMIZING.md#built-in-themes) or path to a theme JSON file.",
    )
    p.add_argument(
        "--colors",
        default=None,
        help="JSON list of color specs: #RRGGBB hex, 256:N, or raw ANSI escapes. Overrides the theme's colors.",
    )
    p.add_argument(
        "--glyphs",
        default=None,
        help="Glyph preset name (see docs/CUSTOMIZING.md#glyph-presets) or a JSON list of glyph strings.",
    )
    p.add_argument(
        "--gamma",
        type=float,
        default=None,
        help="Gamma correction applied to the colormap. Ignored when --normalize quantile.",
    )
    p.add_argument(
        "--normalize",
        choices=["linear", "quantile"],
        default=None,
        help=(
            "Bucketing strategy (default: linear). 'quantile' = GitHub-style: "
            "zero is its own bucket, nonzero values are quantile-binned. "
            "With 'quantile', --gamma is ignored."
        ),
    )
    p.add_argument(
        "--vmin",
        type=float,
        default=None,
        help="Lower bound for the colormap. Default: computed from values (or meta).",
    )
    p.add_argument(
        "--vmax",
        type=float,
        default=None,
        help="Upper bound for the colormap. Default: computed from values (or meta).",
    )
    p.add_argument(
        "--spacer",
        default=" ",
        help='Character placed between cells. Default: a single space. Set to "" for tight grids.',
    )
    p.add_argument(
        "--message",
        default=None,
        help="Footer text. Accepts template placeholders (see docs/SCHEMA.md#templates).",
    )
    p.add_argument(
        "--legend",
        default=None,
        help="Right-aligned legend next to the message. Also accepts templates.",
    )
    p.add_argument(
        "--max-columns",
        dest="max_columns",
        type=int,
        default=None,
        help="Cap on output width. Auto-detected from terminal width when omitted.",
    )
    p.add_argument(
        "--direction",
        choices=["rtl", "ltr"],
        default=None,
        help=(
            "Which edge data anchors to (default: ltr). 'ltr' anchors data on "
            "the left; trimming and padding both happen on the right. 'rtl' is "
            "the mirror image (GitHub-contributions style)."
        ),
    )
    p.add_argument(
        "--pad-to-width",
        dest="pad_to_width",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "If the data is narrower than the terminal, fill remaining cells "
            "with zero-valued cells (no column labels) so the grid spans the "
            "full width. Padding lands on the side opposite --direction."
        ),
    )
    p.add_argument(
        "--simple",
        action="store_true",
        help='Collapse the colormap to two colors (zero vs nonzero). For when "subtle gradients" isn\'t the brief.',
    )
    p.add_argument(
        "--invert-headers",
        dest="invert_headers",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Place the column-label header at the bottom and the "
            "message/legend footer at the top (default: enabled). Use "
            "--no-invert-headers to restore the original layout."
        ),
    )
    p.add_argument(
        "--header-orientation",
        dest="header_orientation",
        choices=["horizontal", "vertical", "auto"],
        default=None,
        help=(
            "How to lay out column-label header (default: auto). 'vertical' "
            "stacks each label's chars one per row, useful when every column "
            "has a label too long for cell width. 'auto' chooses vertical only "
            "when adjacent labels would collide."
        ),
    )
    p.add_argument(
        "--row-labels",
        dest="show_rows",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Show row labels in the left prefix (default: enabled). Use --no-row-labels to hide.",
    )
    p.add_argument(
        "--col-labels",
        dest="show_cols",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Show column labels in the header (default: enabled). Use --no-col-labels to hide.",
    )
    p.add_argument(
        "--follow",
        action="store_true",
        help="Read NDJSON: one matrix doc per line, render each frame in place. See docs/SCHEMA.md.",
    )
    return p


def _build_config(args: argparse.Namespace, doc: dict[str, Any]) -> RenderConfig:
    theme = load_theme(args.theme)
    meta = doc.get("meta") or {}

    if args.colors:
        colors = [resolve_color(c) for c in json.loads(args.colors)]
    elif theme.get("colors"):
        colors = [resolve_color(c) for c in theme["colors"]]
    else:
        colors = None

    theme_glyphs = theme.get("glyphs")
    glyphs = resolve_glyphs(args.glyphs) or (
        theme_glyphs if isinstance(theme_glyphs, list) else resolve_glyphs(theme_glyphs)
    )

    # Precedence: CLI arg > doc meta > theme value > default.
    gamma = _first_not_none(
        args.gamma, meta.get("gamma"), theme.get("gamma"), 1.0
    )
    normalize = _first_not_none(
        args.normalize, meta.get("normalize"), theme.get("normalize"), "linear"
    )
    invert_headers = _first_not_none(
        args.invert_headers,
        meta.get("invert_headers"),
        theme.get("invert_headers"),
        True,
    )
    header_orientation = _first_not_none(
        args.header_orientation,
        meta.get("header_orientation"),
        theme.get("header_orientation"),
        "auto",
    )
    show_rows = _first_not_none(
        args.show_rows,
        meta.get("row_labels"),
        theme.get("row_labels"),
        True,
    )
    show_cols = _first_not_none(
        args.show_cols,
        meta.get("col_labels"),
        theme.get("col_labels"),
        True,
    )
    vmin = _first_not_none(args.vmin, meta.get("vmin"))
    vmax = _first_not_none(args.vmax, meta.get("vmax"))
    message = _first_not_none(args.message, meta.get("message"))
    legend = _first_not_none(args.legend, meta.get("legend"))
    max_columns = (
        args.max_columns if args.max_columns is not None else _terminal_width()
    )
    direction = _first_not_none(
        args.direction, meta.get("direction"), theme.get("direction"), "ltr"
    )
    pad_to_width = _first_not_none(
        args.pad_to_width, meta.get("pad_to_width"), theme.get("pad_to_width"), False
    )

    return RenderConfig(
        colors=colors,
        glyphs=glyphs,
        gamma=float(gamma),
        normalize=str(normalize),
        vmin=None if vmin is None else float(vmin),
        vmax=None if vmax is None else float(vmax),
        spacer=args.spacer,
        message=message,
        legend=legend,
        max_columns=max_columns,
        simple=args.simple,
        invert_headers=bool(invert_headers),
        header_orientation=str(header_orientation),
        show_rows=bool(show_rows),
        show_cols=bool(show_cols),
        from_date=meta.get("from"),
        to_date=meta.get("to"),
        direction=str(direction),
        pad_to_width=bool(pad_to_width),
    )


def _first_not_none(*values):
    for v in values:
        if v is not None:
            return v
    return None


def _render_doc(args: argparse.Namespace, doc: dict[str, Any]) -> str:
    validate_matrix_doc(doc)
    config = _build_config(args, doc)
    return render(
        doc["values"],
        cols=doc.get("cols"),
        rows=doc.get("rows"),
        config=config,
    )


def _run_oneshot(args: argparse.Namespace) -> int:
    try:
        doc = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"heatgraph: invalid JSON on stdin: {e.msg} (line {e.lineno}, column {e.colno})", file=sys.stderr)
        return 2

    try:
        output = _render_doc(args, doc)
    except SchemaError as e:
        print(f"heatgraph: {e}", file=sys.stderr)
        return 2

    print(output)
    return 0


def _run_follow(args: argparse.Namespace) -> int:
    for lineno, raw in enumerate(sys.stdin, start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            doc = json.loads(line)
            output = _render_doc(args, doc)
        except json.JSONDecodeError as e:
            print(f"heatgraph: line {lineno}: invalid JSON: {e.msg}", file=sys.stderr)
            continue
        except SchemaError as e:
            print(f"heatgraph: line {lineno}: {e}", file=sys.stderr)
            continue

        sys.stdout.write(CLEAR_HOME)
        sys.stdout.write(output)
        sys.stdout.write("\n")
        sys.stdout.flush()
    return 0


def main() -> int:
    args = _build_parser().parse_args()
    try:
        if args.follow:
            return _run_follow(args)
        return _run_oneshot(args)
    except KeyboardInterrupt:
        return 130
    except BrokenPipeError:
        return 0
