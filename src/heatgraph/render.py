"""Terminal renderer: matrix values + presentation config -> ANSI string.

The renderer is intentionally pure: no IO, no argument parsing, no schema
awareness. It consumes a 2D list of floats plus optional axis labels and a
``RenderConfig``, and returns the rendered string.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from heatgraph.bucket import bucket, compute_quantile_thresholds, quantile_bucket
from heatgraph.colors import resolve_color, RESET
from heatgraph.glyphs import DEFAULT_GLYPHS
from heatgraph.themes import DEFAULT_COLORS

Matrix = List[List[float]]

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _visible_len(s: str) -> int:
    return len(_ANSI_RE.sub("", s))


@dataclass
class RenderConfig:
    colors: Optional[List[str]] = None
    glyphs: Optional[List[str]] = None

    spacer: str = " "

    message: Optional[str] = None
    legend: Optional[str] = None

    max_columns: Optional[int] = None
    direction: str = "ltr"
    pad_to_width: bool = False

    vmin: Optional[float] = None
    vmax: Optional[float] = None
    gamma: float = 1.0

    # "linear" (default) bins values evenly across [vmin, vmax] with optional
    # gamma. "quantile" reserves bucket 0 for v<=0 and bins positive values by
    # quantile across the dataset (GitHub-contributions style). gamma is
    # ignored when normalize == "quantile".
    normalize: str = "linear"

    simple: bool = False
    invert_headers: bool = True
    header_orientation: str = "auto"
    show_rows: bool = True
    show_cols: bool = True

    highlights: Dict[Tuple[int, int], str] = field(default_factory=dict)

    # Template-only inputs sourced from meta. They feed [FROM] / [TO]
    # placeholders without coupling render() to the matrix-doc shape.
    from_date: Optional[str] = None
    to_date: Optional[str] = None


_TEMPLATE_RE = re.compile(r"\[([A-Z]+)(?::(-?\d+))?\]")


def _format_number(v: Optional[float]) -> str:
    if v is None:
        return "?"
    f = float(v)
    if f.is_integer():
        return str(int(f))
    return f"{f:g}"


def _build_cell(colors: List[str], glyphs: List[str], i: int) -> str:
    if not colors:
        return "?"
    if i < 0 or i >= len(colors):
        i = len(colors) - 1
    color = colors[i]
    glyph = glyphs[i] if i < len(glyphs) else (glyphs[-1] if glyphs else "?")
    return f"{color}{glyph}{RESET}"


def _build_gradient(colors: List[str], glyphs: List[str], spacer: str) -> str:
    return spacer.join(_build_cell(colors, glyphs, i) for i in range(len(colors)))


def _expand_template(
    s: Optional[str],
    *,
    colors: List[str],
    glyphs: List[str],
    spacer: str,
    vmin: Optional[float],
    vmax: Optional[float],
    total: float,
    count: int,
    mean: Optional[float],
    cells: int,
    from_date: Optional[str],
    to_date: Optional[str],
) -> Optional[str]:
    if not s:
        return s

    def repl(m: re.Match) -> str:
        name = m.group(1)
        idx = m.group(2)
        if name == "GRADIENT":
            return _build_gradient(colors, glyphs, spacer)
        if name == "CELL" and idx is not None:
            return _build_cell(colors, glyphs, int(idx))
        if name == "MIN":
            return _format_number(vmin)
        if name == "MAX":
            return _format_number(vmax)
        if name == "TOTAL":
            return _format_number(total)
        if name == "COUNT":
            return str(count)
        if name == "MEAN":
            return _format_number(mean)
        if name == "CELLS":
            return str(cells)
        if name == "FROM":
            return from_date or "?"
        if name == "TO":
            return to_date or "?"
        return m.group(0)

    return _TEMPLATE_RE.sub(repl, s)


def render(
    values: Matrix,
    *,
    cols: Optional[List[str]] = None,
    rows: Optional[List[str]] = None,
    config: Optional[RenderConfig] = None,
) -> str:
    config = config or RenderConfig()

    if not config.show_cols:
        cols = None
    if not config.show_rows:
        rows = None

    if not values:
        return ""

    colors = [resolve_color(c) for c in (config.colors or DEFAULT_COLORS)]
    glyphs = config.glyphs or DEFAULT_GLYPHS

    n_cols = max((len(r) for r in values), default=0)
    if n_cols == 0:
        return ""

    flat = [v for row in values for v in row if v is not None]
    if not flat:
        return ""

    vmin = config.vmin if config.vmin is not None else min(flat)
    vmax = config.vmax if config.vmax is not None else max(flat)

    if config.normalize == "quantile":
        thresholds: Optional[List[float]] = compute_quantile_thresholds(
            flat, len(colors)
        )
    else:
        thresholds = None

    total = sum(flat)
    nonzero = sum(1 for v in flat if v != 0)
    mean = total / len(flat) if flat else None

    cw = _cell_width(glyphs, config.spacer)
    prefix_width = _prefix_width(rows)

    rendered_cells = sum(len(row) for row in values)

    data, cols_out = _fit_columns(
        values,
        cols,
        config.max_columns,
        prefix_width,
        cw,
        direction=config.direction,
        pad_to_width=config.pad_to_width,
    )
    template_ctx = dict(
        colors=colors,
        glyphs=glyphs,
        spacer=config.spacer,
        vmin=vmin,
        vmax=vmax,
        total=total,
        count=nonzero,
        mean=mean,
        cells=rendered_cells,
        from_date=config.from_date,
        to_date=config.to_date,
    )
    message = _expand_template(config.message, **template_ctx)
    legend = _expand_template(config.legend, **template_ctx)

    header_lines = _render_header(
        cols_out,
        prefix_width,
        cw,
        orientation=config.header_orientation,
        align_bottom=not config.invert_headers,
    )

    body_lines: List[str] = []
    for r, row in enumerate(data):
        body_lines.append(
            _render_row(
                row=row,
                r=r,
                n_cols=len(data[0]) if data else 0,
                colors=colors,
                glyphs=glyphs,
                spacer=config.spacer,
                rows=rows,
                prefix_width=prefix_width,
                vmin=vmin,
                vmax=vmax,
                gamma=config.gamma,
                thresholds=thresholds,
                simple=config.simple,
                highlights=config.highlights,
            )
        )

    footer_lines = _render_footer(
        message=message,
        legend=legend,
        prefix_width=prefix_width,
        total_width=prefix_width + len(data[0]) * cw if data else 0,
        spacer=config.spacer,
    )

    lines: List[str] = []
    if config.invert_headers:
        if footer_lines:
            lines.extend(footer_lines)
            lines.append("")
        lines.extend(body_lines)
        lines.extend(header_lines)
    else:
        lines.extend(header_lines)
        lines.extend(body_lines)
        if footer_lines:
            lines.append("")
            lines.extend(footer_lines)

    return "\n".join(lines)


def _cell_width(glyphs: List[str], spacer: str) -> int:
    sample = glyphs[0] if glyphs else " "
    return _visible_len(sample) + _visible_len(spacer)


def _prefix_width(rows: Optional[List[str]]) -> int:
    if not rows:
        return 0
    width = max((_visible_len(l) for l in rows), default=0)
    return width + 2 if width > 0 else 0


def _fit_columns(
    data,
    cols,
    max_columns,
    prefix_width,
    cw,
    *,
    direction: str = "rtl",
    pad_to_width: bool = False,
):
    if max_columns is None or cw == 0:
        return data, cols

    if max_columns - prefix_width < cw:
        return data, None

    usable = max_columns - prefix_width
    max_cols_fit = usable // cw
    cur = len(data[0])

    if max_cols_fit == cur:
        return data, cols

    if max_cols_fit < cur:
        trim = cur - max_cols_fit
        if direction == "ltr":
            new_data = [row[:max_cols_fit] for row in data]
            new_labels = cols[:max_cols_fit] if cols else None
        else:
            new_data = [row[trim:] for row in data]
            new_labels = cols[trim:] if cols else None
        return new_data, new_labels

    if not pad_to_width:
        return data, cols

    pad = max_cols_fit - cur
    filler = [0.0] * pad
    label_filler = [""] * pad
    if direction == "ltr":
        new_data = [list(row) + filler for row in data]
        new_labels = (list(cols) + label_filler) if cols else None
    else:
        new_data = [filler + list(row) for row in data]
        new_labels = (label_filler + list(cols)) if cols else None
    return new_data, new_labels


def _labels_collide(labels: List[str], cw: int) -> bool:
    # Touching counts as a collision: two non-empty labels with no whitespace
    # between them are visually unreadable (e.g., "aa"+"ab" = "aaab"). Months
    # don't trip this because intervening columns are blank.
    last_end = -1
    for i, label in enumerate(labels):
        if not label:
            continue
        start = i * cw
        if start <= last_end:
            return True
        last_end = start + _visible_len(label)
    return False


def _render_header(
    cols: Optional[List[str]],
    prefix_width: int,
    cw: int,
    orientation: str = "auto",
    align_bottom: bool = True,
) -> List[str]:
    if not cols:
        return []
    if orientation == "auto":
        orientation = "vertical" if _labels_collide(cols, cw) else "horizontal"
    if orientation == "vertical":
        return _render_header_vertical(cols, prefix_width, cw, align_bottom)
    return _render_header_horizontal(cols, prefix_width, cw)


def _render_header_horizontal(cols, prefix_width, cw) -> List[str]:
    n_cols = len(cols)
    row_width = prefix_width + n_cols * cw
    line = [" "] * row_width

    for i, label in enumerate(cols):
        if not label:
            continue
        pos = prefix_width + i * cw
        for k, ch in enumerate(label):
            if pos + k < row_width:
                line[pos + k] = ch

    rendered = "".join(line).rstrip()
    return [rendered] if rendered else []


def _render_header_vertical(
    cols: List[str], prefix_width: int, cw: int, align_bottom: bool
) -> List[str]:
    max_len = max((_visible_len(l) for l in cols), default=0)
    if max_len == 0:
        return []

    padded = [
        ((" " * (max_len - _visible_len(l))) + l) if align_bottom
        else (l + " " * (max_len - _visible_len(l)))
        for l in cols
    ]
    row_width = prefix_width + len(cols) * cw
    lines: List[str] = []
    for depth in range(max_len):
        line = [" "] * row_width
        for i, label in enumerate(padded):
            ch = label[depth] if depth < len(label) else " "
            if ch == " ":
                continue
            pos = prefix_width + i * cw
            if pos < row_width:
                line[pos] = ch
        lines.append("".join(line).rstrip())

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _render_row(
    row,
    r,
    n_cols,
    colors,
    glyphs,
    spacer,
    rows,
    prefix_width,
    vmin,
    vmax,
    gamma,
    thresholds,
    simple,
    highlights,
):
    prefix = ""

    if rows and prefix_width:
        label = rows[r] if r < len(rows) else ""
        pad = prefix_width - 2
        prefix = f" {label:<{pad}} "

    cells = []

    for c in range(n_cols):
        v = row[c] if c < len(row) and row[c] is not None else vmin
        if thresholds is not None:
            b = quantile_bucket(v, thresholds, len(colors))
        else:
            b = bucket(v, vmin, vmax, len(colors), gamma)

        if simple:
            color = colors[-1] if b > 0 else colors[0]
        else:
            override = (
                resolve_color(highlights[(r, c)]) if (r, c) in highlights else None
            )
            color = override or colors[b]

        glyph = glyphs[b] if b < len(glyphs) else glyphs[-1]

        cell = f"{color}{glyph}{RESET}"
        if spacer:
            cell += spacer

        cells.append(cell)

    return prefix + "".join(cells)


def _render_footer(message, legend, prefix_width, total_width, spacer):
    if not message and not legend:
        return None

    indent = " " * prefix_width
    lines = []

    if legend:
        # Visible widths only — message/legend may contain ANSI escapes from
        # template expansion ([GRADIENT], [CELL:i]).
        msg_len = _visible_len(message or "")
        leg_len = _visible_len(legend)
        # Right edge of the visible grid is one trailing-spacer inside total_width.
        target = total_width - _visible_len(spacer)
        available = target - prefix_width - msg_len - leg_len
        padding = " " * max(1 if message else 0, available)

        lines.append(f"{indent}{message or ''}{padding}{legend}")
    else:
        lines.append(f"{indent}{message or ''}")

    return lines
