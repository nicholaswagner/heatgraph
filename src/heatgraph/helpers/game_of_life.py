"""game_of_life: emit Conway's Game of Life as matrix-doc NDJSON on stdout.

Each generation is written as one JSON document per line, suitable for piping
into `heatgraph --follow`. The simulation halts on steady state, extinction, or
when --generations is reached. Ctrl-C exits cleanly.

The original Python implementation of Conway's Game of Life is sourced from
https://github.com/mwharrisjr/Game-of-Life/ by Maurice Harris.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time


def create_initial_grid(
    rows: int, cols: int, density: float, rng: random.Random
) -> list[list[int]]:
    return [
        [1 if rng.random() < density else 0 for _ in range(cols)] for _ in range(rows)
    ]


def live_neighbors(
    row: int, col: int, rows: int, cols: int, grid: list[list[int]]
) -> int:
    total = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            total += grid[(row + dr) % rows][(col + dc) % cols]
    return total


def step(
    rows: int,
    cols: int,
    grid: list[list[int]],
    next_grid: list[list[int]],
) -> None:
    for r in range(rows):
        for c in range(cols):
            n = live_neighbors(r, c, rows, cols, grid)
            cell = grid[r][c]
            if cell == 1 and (n == 2 or n == 3):
                next_grid[r][c] = 1
            elif cell == 0 and n == 3:
                next_grid[r][c] = 1
            else:
                next_grid[r][c] = 0


def alive_count(grid: list[list[int]]) -> int:
    return sum(sum(row) for row in grid)


def _frame_doc(grid: list[list[int]], gen: int) -> dict:
    return {
        "values": grid,
        "meta": {
            "message": f"Conway's Game of Life · gen {gen} · alive [COUNT]",
            "legend": "Alive [CELL:5]  -  Dead [CELL:0]",
            "vmin": 0,
            "vmax": 1,
        },
    }


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    p = argparse.ArgumentParser(
        prog="heatgraph-demos game-of-life",
        description=(
            "Emit Conway's Game of Life as matrix-doc NDJSON on stdout. "
            "Pipe into `heatgraph --follow` to render."
        ),
    )
    p.add_argument("--rows", type=int, default=22)
    p.add_argument("--cols", type=int, default=60)
    p.add_argument(
        "--density",
        type=float,
        default=0.125,
        help="Initial live-cell probability (default: 0.125)",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=0.15,
        help="Seconds between frames (default: 0.15)",
    )
    p.add_argument(
        "--generations",
        type=int,
        default=10000,
        help="Maximum generations before stopping (default: 10000)",
    )
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args(argv)

    rng = random.Random(args.seed)
    current = create_initial_grid(args.rows, args.cols, args.density, rng)
    next_grid = [[0] * args.cols for _ in range(args.rows)]

    try:
        for gen in range(1, args.generations + 1):
            sys.stdout.write(json.dumps(_frame_doc(current, gen)))
            sys.stdout.write("\n")
            sys.stdout.flush()

            if alive_count(current) == 0:
                break
            step(args.rows, args.cols, current, next_grid)
            if current == next_grid:
                break
            current, next_grid = next_grid, current
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
