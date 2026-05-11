"""cal_to_matrix: stdin (calendar doc) -> stdout (matrix doc)."""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from typing import Any, Dict, List, Tuple

SCHEMA_HINT = "See docs/SCHEMA.md for the calendar doc format."

MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


class SchemaError(ValueError):
    """Raised when stdin input does not conform to the calendar doc schema."""


def validate_calendar_doc(doc: Any) -> None:
    if not isinstance(doc, dict):
        raise SchemaError(
            f"Expected a JSON object, got {type(doc).__name__}. {SCHEMA_HINT}"
        )

    if "data" not in doc:
        hint = (
            " Unexpected document shape.  Was expecting a 'data' key and did not find one.  Is it a matrix doc?  If so, you can pipe that directly into heatgraph."
            if "values" in doc
            else ""
        )
        raise SchemaError(f"Missing required field 'data'.{hint} {SCHEMA_HINT}")

    data = doc["data"]
    if not isinstance(data, dict):
        raise SchemaError(
            f"'data' must be an object mapping YYYY-MM-DD -> number, got {type(data).__name__}. {SCHEMA_HINT}"
        )

    for k, v in data.items():
        if not isinstance(k, str):
            raise SchemaError(
                f"date keys must be strings, got {type(k).__name__}. {SCHEMA_HINT}"
            )
        try:
            datetime.date.fromisoformat(k)
        except ValueError as e:
            raise SchemaError(
                f"date key {k!r} is not a valid YYYY-MM-DD: {e}. {SCHEMA_HINT}"
            ) from None
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise SchemaError(
                f"value for {k!r} must be a number, got {type(v).__name__}. {SCHEMA_HINT}"
            )

    if "meta" in doc and doc["meta"] is not None and not isinstance(doc["meta"], dict):
        raise SchemaError(f"'meta' must be an object if present. {SCHEMA_HINT}")


def cal_to_matrix(
    doc: dict,
    *,
    week_starts_on: int = 6,
    show_months: bool = True,
    show_days: bool = True,
) -> dict[str, Any]:
    raw_values = doc["data"]
    values = {datetime.date.fromisoformat(k): float(v) for k, v in raw_values.items()}

    if not values:
        return {"values": []}

    start = min(values.keys())
    end = max(values.keys())

    rows, column_dates = _build_grid(values, start, end, week_starts_on)

    out: dict[str, Any] = {"values": rows}
    if show_months:
        out["cols"] = _month_labels(column_dates, start)
    if show_days:
        out["rows"] = _dow_labels(week_starts_on)

    input_meta = doc.get("meta") or {}
    out["meta"] = {
        "from": start.isoformat(),
        "to": end.isoformat(),
        **input_meta,
    }
    return out


def _build_grid(
    values: Dict[datetime.date, float],
    start: datetime.date,
    end: datetime.date,
    week_starts_on: int,
) -> Tuple[List[List[float]], List[datetime.date]]:
    days_back = (start.weekday() - week_starts_on) % 7
    grid_start = start - datetime.timedelta(days=days_back)

    days_forward = (week_starts_on - 1 - end.weekday()) % 7
    grid_end = end + datetime.timedelta(days=days_forward)

    n_days = (grid_end - grid_start).days + 1
    n_cols = n_days // 7

    rows = [[0.0] * n_cols for _ in range(7)]
    column_dates = []

    for c in range(n_cols):
        col_anchor = grid_start + datetime.timedelta(days=c * 7)
        column_dates.append(col_anchor)

        for r in range(7):
            d = col_anchor + datetime.timedelta(days=r)
            if start <= d <= end and d in values:
                rows[r][c] = float(values[d])

    return rows, column_dates


def _month_labels(column_dates: List[datetime.date], start: datetime.date) -> List[str]:
    labels = [""] * len(column_dates)
    last_month = None

    for i, d in enumerate(column_dates):
        if d < start:
            continue

        m = (d + datetime.timedelta(days=3)).month
        if m != last_month:
            labels[i] = MONTHS[m - 1]
            last_month = m

    return labels


def _dow_labels(week_starts_on: int) -> List[str]:
    base = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    rotated = base[week_starts_on:] + base[:week_starts_on]
    return [d if d in ("Mon", "Wed", "Fri") else "" for d in rotated]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cal_to_matrix",
        description="Transform a calendar doc on stdin into a matrix doc on stdout.",
    )
    p.add_argument(
        "--week-starts-on",
        dest="week_starts_on",
        type=int,
        choices=range(7),
        default=6,
        metavar="{0..6}",
        help="0=Mon ... 6=Sun (default: 6)",
    )
    p.add_argument("--no-months", dest="show_months", action="store_false")
    p.add_argument("--no-days", dest="show_days", action="store_false")
    p.add_argument(
        "--follow",
        action="store_true",
        help="Read NDJSON calendar docs and emit NDJSON matrix docs, one per line. See docs/SCHEMA.md.",
    )
    return p


def _transform_doc(args: argparse.Namespace, doc: dict[str, Any]) -> dict[str, Any]:
    validate_calendar_doc(doc)
    return cal_to_matrix(
        doc,
        week_starts_on=args.week_starts_on,
        show_months=args.show_months,
        show_days=args.show_days,
    )


def _run_oneshot(args: argparse.Namespace) -> int:
    try:
        doc = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(
            f"cal_to_matrix: invalid JSON on stdin: {e.msg} (line {e.lineno}, column {e.colno})",
            file=sys.stderr,
        )
        return 2

    try:
        out = _transform_doc(args, doc)
    except SchemaError as e:
        print(f"cal_to_matrix: {e}", file=sys.stderr)
        return 2

    print(json.dumps(out))
    return 0


def _run_follow(args: argparse.Namespace) -> int:
    for lineno, raw in enumerate(sys.stdin, start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            doc = json.loads(line)
            out = _transform_doc(args, doc)
        except json.JSONDecodeError as e:
            print(
                f"cal_to_matrix: line {lineno}: invalid JSON: {e.msg}",
                file=sys.stderr,
            )
            continue
        except SchemaError as e:
            print(f"cal_to_matrix: line {lineno}: {e}", file=sys.stderr)
            continue

        sys.stdout.write(json.dumps(out, separators=(",", ":")))
        sys.stdout.write("\n")
        sys.stdout.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.follow:
        return _run_follow(args)
    return _run_oneshot(args)


if __name__ == "__main__":
    raise SystemExit(main())
