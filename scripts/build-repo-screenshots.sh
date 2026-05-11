#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
REPO_ROOT=$(dirname "$SCRIPT_DIR")
IMAGES_DIR="${REPO_ROOT}/images"
GLYPHS=$(jq -r 'keys | join(" ")' "${REPO_ROOT}/src/heatgraph/glyphs.json")

cd "$REPO_ROOT"
mkdir -p "${IMAGES_DIR}"

PAGE_THEME="nord"

# termshot -f "${IMAGES_DIR}/first_example.png" -- bash -c "
#   echo 'echo {values:[[1,2,3],[4,5,6],[7,8,9]]} | uvx heatgraph'
#   echo
#   paste <(echo '{\"values\":[[1,2,3],[4,5,6],[7,8,9]]}' | uvx heatgraph)
# "
  # echo 'echo {values:[[1,2,3],[4,5,6],[7,8,9]]} | uvx heatgraph'
  # echo 'echo '{\"values\":[[1,2,3],[4,5,6],[7,8,9]]},\"cols\": [\"A\",\"B\",\"C\"], \"rows\": [\"1\",\"2\",\"3\"], \"meta\": {\"from\": \"2025-05-12\", \"to\": \"2026-05-12\"} | uvx heatgraph'
# ,\"cols\": [], \"rows\": []


# Simple Example with side by side
# termshot -f "${IMAGES_DIR}/first_example.png" --columns 80 -- bash -c "
#   echo
#   paste <(heatgraph-helpers mock-data --cols 16 --rows 4 | heatgraph) \
#   <(heatgraph-helpers mock-data --cols 16 --rows 4 | heatgraph --theme nord)
# "

# Single Line Example
 termshot -f "${IMAGES_DIR}/quick-start.png" -s -- bash -c "echo '{\"values\": [[1, 2, 3, 4, 5]], \"cols\": [\"a\",\"b\",\"c\",\"d\",\"e\"]}' | heatgraph"

# Render one heatgraph per glyph preset, two panels per row, into a single PNG.
# Each glyph renders to a temp file; pairs are pasted side-by-side.
# $GLYPHS expands at the outer shell (single space-separated line);
# \$glyph and friends are escaped so they expand inside bash -c.
# termshot -f "${IMAGES_DIR}/glyphs.png" -m 20 --columns 80 -- bash -c "
#   echo
#   echo -e \"\e[3m--glyphs OPTIONS\e[0m\"
#   echo
#   echo
#   left=
#   for glyph in $GLYPHS; do
#     out=\$(mktemp)
#     heatgraph-helpers mock-data --cols 16 --rows 4 --seed 1 \
#       | heatgraph --max-columns 35 --glyphs \"\$glyph\" --theme nord  --message \"\$glyph\" > \"\$out\"
#     if [ -z \"\$left\" ]; then
#       left=\"\$out\"
#     else
#       # paste glues bytes, but visual alignment needs visible-width parity.
#       # Heatgraph's grid lines have ANSI escapes (non-visible bytes); its
#       # chrome lines (message, header, blank) are pure ASCII. Pad only the
#       # ASCII lines, to the widest ASCII line in the file. That happens to
#       # be the column-header row, which already matches grid visible width.
#       W=\$(awk '!/\033\[/ { if (length(\$0) > w) w = length(\$0) } END { print w+0 }' \"\$left\")
#       padded=\$(mktemp)
#       awk -v W=\"\$W\" '/\033\[/ { print; next } { printf \"%-*s\n\", W, \$0 }' \"\$left\" > \"\$padded\"
#       paste -d '  ' \"\$padded\" \"\$out\"
#       echo
#       rm -f \"\$left\" \"\$out\" \"\$padded\"
#       left=
#     fi
#   done
#   if [ -n \"\$left\" ]; then
#     cat \"\$left\"
#     rm -f \"\$left\"
#   fi
# "


# <hr/>
# termshot -f "${IMAGES_DIR}/hr1.png" --no-decoration --no-shadow -s --columns 120 -- bash -c "
#   uv run heatgraph-helpers mock-data --cols 80 --rows 1 | heatgraph --vmin 1 --normalize quantile --theme $PAGE_THEME --glyphs modern --message '' --legend '' --no-row-labels --no-col-labels
#   echo
# "

            # "message": "[COUNT] / [CELLS] days",
            # "legend": "logged activity  [CELL:-1]",

# Hero
  # uv run heatgraph-helpers mock-data --cols 80 --rows 7 --seed 42 | heatgraph  --theme github-dark --message 'heatgraph interest [COUNT]/[CELLS]' --legend 'less  [GRADIENT]  more' --no-row-labels --no-col-labels
  # uv run heatgraph-helpers mock-data --cols 80 --rows 7 --seed 42 | heatgraph --message 'heatgraph interest [COUNT] / [CELLS]' --legend 'less  [GRADIENT]  more' --no-row-labels --no-col-labels --normalize quantile --glyphs squarespace --theme rose-pine --no-invert-headers
termshot -f "${IMAGES_DIR}/hero.png" --columns 80 -- bash -c "
  uv run heatgraph-helpers mock-data --cols 80 --rows 7 --seed 12 --sparsity 0.5 --vmax 5 | heatgraph --message '[COUNT] / [CELLS]' --legend 'less  [GRADIENT]  more' --no-row-labels --no-col-labels --normalize quantile --glyphs squarespace --no-invert-headers --theme rose-pine
"

#github contribution graph image
# termshot -f "${IMAGES_DIR}/gh-contributions.png" --columns 80 -- bash -c "
#   echo
#   uv run heatgraph-helpers gh-contributions mrdoob
#   echo
# "

# Workout Habit Tracker Example
termshot --columns 80 -f "${IMAGES_DIR}/helpers-habit-tracker.png" -- uv run heatgraph-helpers habit-tracker examples/workout-log.md --simple


# Sleep quality tracker
termshot --columns 80 -f "${IMAGES_DIR}/helpers-sleep-tracker.png" -- uv run heatgraph-helpers habit-tracker examples/sleep.log --theme nord --glyphs terminal --normalize quantile --message '[COUNT] nights logged' --legend 'poor  [GRADIENT]  excellent'

