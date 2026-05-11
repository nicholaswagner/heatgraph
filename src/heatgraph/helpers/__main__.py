import argparse

from heatgraph.helpers import game_of_life, gh_contributions, habit_tracker, cal2matrix
from heatgraph.fixtures import matrix

HELPERS = {
    "cal2matrix": cal2matrix.main,
    "game-of-life": game_of_life.main,
    "gh-contributions": gh_contributions.main,
    "habit-tracker": habit_tracker.main,
    "mock-data": matrix.main,
}


def main():
    parser = argparse.ArgumentParser(prog="heatgraph-helpers")
    parser.add_argument("command", choices=sorted(HELPERS))
    args, rest = parser.parse_known_args()
    return HELPERS[args.command](rest)
