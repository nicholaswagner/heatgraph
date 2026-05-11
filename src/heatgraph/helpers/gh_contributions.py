"""gh_contributions: render a heatgraph of GitHub contributions.

Fetches contribution counts via the `gh` CLI, converts the calendar doc to a
matrix doc with `heatgraph.helpers.cal_to_matrix`, and renders to stdout using
the same machinery as the `heatgraph` CLI.

Requires the `gh` CLI to be installed and authenticated. The default range is
the last 365 days; pass --from / --to to override.
"""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys

from heatgraph import cli as heatgraph_cli
from heatgraph.helpers.cal2matrix import cal_to_matrix


def fetch(username: str | None, frm: datetime.date, to: datetime.date) -> dict:
    iso_from = f"{frm.isoformat()}T00:00:00Z"
    iso_to = f"{to.isoformat()}T23:59:59Z"
    args = f'(from: "{iso_from}", to: "{iso_to}")'
    days = "date contributionCount"

    if username:
        query = (
            f'{{ user(login: "{username}") {{ contributionsCollection{args} '
            f"{{ contributionCalendar {{ weeks {{ contributionDays {{ {days} }} }} }} }} }} }}"
        )
        node_key = "user"
    else:
        query = (
            f"{{ viewer {{ contributionsCollection{args} "
            f"{{ contributionCalendar {{ weeks {{ contributionDays {{ {days} }} }} }} }} }} }}"
        )
        node_key = "viewer"

    res = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(res.stdout)
    return payload["data"][node_key]["contributionsCollection"]["contributionCalendar"]


def to_calendar_doc(calendar: dict) -> dict:
    data: dict[str, int] = {}
    for week in calendar.get("weeks", []):
        for day in week.get("contributionDays", []):
            data[day["date"]] = int(day.get("contributionCount", 0))
    return {
        "data": data,
        "meta": {
            "message": "[TOTAL] contributions, [FROM] → [TO]",
            "legend": "less  [GRADIENT]  more",
        },
    }


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # Stage 1: let the heatgraph parser absorb its own flags first. Doing this
    # before the demo parser is what prevents the demo's positional `username`
    # from greedily swallowing a value that actually belongs to e.g. --glyphs.
    render_args, demo_argv = heatgraph_cli._build_parser().parse_known_args(argv)
    if render_args.theme is None:
        render_args.theme = "github-dark"

    if render_args.normalize is None:
        render_args.normalize = "quantile"

    # Stage 2: parse the demo's own args from what's left.
    p = argparse.ArgumentParser(
        prog="heatgraph-demos gh-contributions",
        description=(
            "Render a heatgraph of GitHub contributions for a user. "
            "Any heatgraph flag (see `heatgraph --help`) is also accepted "
            "and forwarded to the renderer; --theme defaults to github-dark."
        ),
    )
    p.add_argument(
        "username",
        nargs="?",
        default=None,
        help="GitHub login (default: authenticated viewer)",
    )
    p.add_argument("--from", dest="frm", default=None, metavar="YYYY-MM-DD")
    p.add_argument("--to", dest="to", default=None, metavar="YYYY-MM-DD")
    args = p.parse_args(demo_argv)

    today = datetime.date.today()
    to = datetime.date.fromisoformat(args.to) if args.to else today
    frm = (
        datetime.date.fromisoformat(args.frm)
        if args.frm
        else (to - datetime.timedelta(days=365))
    )

    try:
        calendar = fetch(args.username, frm, to)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"gh-contributions: gh CLI failed: {e.stderr.strip()}\n")
        return 1
    except (KeyError, json.JSONDecodeError) as e:
        sys.stderr.write(f"gh-contributions: unexpected GraphQL response: {e}\n")
        return 1

    calendar_doc = to_calendar_doc(calendar)
    matrix_doc = cal_to_matrix(calendar_doc)

    output = heatgraph_cli._render_doc(render_args, matrix_doc)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
