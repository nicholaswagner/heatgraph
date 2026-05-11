"""
Generates a random [calendar doc](scripts/calendar-doc-spec.md) for development and testing.
{ "data": [{
            "2026-01-01": 1, "2026-01-02": 1, "2026-01-04": 1,
            "2026-01-05": 1, "2026-01-06": 1}] },
"""

from __future__ import annotations

import argparse
import datetime
import json


def build_calendar_fixture(
    start: datetime.date | None = None,
    end: datetime.date | None = None,
) -> dict:
    end = end or datetime.date.today()
    start = start or (end - datetime.timedelta(days=365))
    data = {
        (start + datetime.timedelta(days=i)).isoformat(): float(i % 5)
        for i in range((end - start).days + 1)
    }
    return {"data": data}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python scripts/fixtures/calendar.py",
        description="Emit a random calendar doc to stdout.",
    )
    p.add_argument("--start", default=None, metavar="YYYY-MM-DD")
    p.add_argument("--end", default=None, metavar="YYYY-MM-DD")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    start = datetime.date.fromisoformat(args.start) if args.start else None
    end = datetime.date.fromisoformat(args.end) if args.end else None
    print(json.dumps(build_calendar_fixture(start=start, end=end)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
