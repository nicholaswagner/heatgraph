"""Generate a random matrix doc for development and testing."""
from __future__ import annotations

import argparse
import json
import random


def _col_label(i: int) -> str:
    """Spreadsheet-style column label: a, b, ..., z, aa, ab, ..."""
    s = ""
    n = i + 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(ord("a") + r) + s
    return s


def build_matrix_fixture(
    rows: int = 8,
    cols: int = 8,
    vmin: float = 0.0,
    vmax: float = 10.0,
    sparsity: float = 0.0,
    seed: int | None = None,
) -> dict:
    rng = random.Random(seed)
    values = [
        [
            0.0 if sparsity > 0 and rng.random() < sparsity
            else rng.uniform(vmin, vmax)
            for _ in range(cols)
        ]
        for _ in range(rows)
    ]
    return {
        "values": values,
        "cols": [_col_label(c) for c in range(cols)],
        "rows": [str(r + 1) for r in range(rows)],
    }


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python scripts/fixtures/matrix.py",
        description="Emit a random matrix doc to stdout.",
    )
    p.add_argument("--rows", type=int, default=8)
    p.add_argument("--cols", type=int, default=8)
    p.add_argument("--vmin", type=float, default=0.0)
    p.add_argument("--vmax", type=float, default=10.0)
    p.add_argument(
        "--sparsity",
        type=float,
        default=0.0,
        help="Probability that a given cell is exactly zero (0.0–1.0). Useful for making [COUNT] meaningful.",
    )
    p.add_argument("--seed", type=int, default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.vmin > args.vmax:
        raise SystemExit("vmin must be <= vmax")
    if not 0.0 <= args.sparsity <= 1.0:
        raise SystemExit("sparsity must be between 0.0 and 1.0")
    print(json.dumps(build_matrix_fixture(
        rows=args.rows,
        cols=args.cols,
        vmin=args.vmin,
        vmax=args.vmax,
        sparsity=args.sparsity,
        seed=args.seed,
    )))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
