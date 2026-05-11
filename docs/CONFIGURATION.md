# Configuring `heatgraph`

Settings come from four places. The leftmost source wins:

```
┌──────────────┐
│  CLI flag    │  highest
├──────────────┤
│  doc meta    │
├──────────────┤
│  theme JSON  │
├──────────────┤
│  default     │  lowest
└──────────────┘
```

No magic merge, no surprise overrides. If something looks wrong, walk the
chain from the top.

## CLI flags

> The block below is auto-generated from `argparse` by
> [`scripts/gen-cli-table.py`](../scripts/gen-cli-table.py). Edit the help text
> in [`src/heatgraph/cli.py`](../src/heatgraph/cli.py), then rerun the script.

<!-- BEGIN GENERATED:cli-flags -->
```text
heatgraph [--theme S] [--colors S] [--glyphs S] [--gamma F]
          [--normalize linear|quantile] [--vmin F] [--vmax F] [--spacer S] [--message S]
          [--legend S] [--max-columns N] [--direction rtl|ltr]
          [--pad-to-width/--no-pad-to-width] [--simple]
          [--invert-headers/--no-invert-headers]
          [--header-orientation horizontal|vertical|auto] [--row-labels/--no-row-labels]
          [--col-labels/--no-col-labels] [--follow]
```

| Flag | Description |
|------|-------------|
| `--theme` | Named theme (see docs/CUSTOMIZING.md#built-in-themes) or path to a theme JSON file. |
| `--colors` | JSON list of color specs: #RRGGBB hex, 256:N, or raw ANSI escapes. Overrides the theme's colors. |
| `--glyphs` | Glyph preset name (see docs/CUSTOMIZING.md#glyph-presets) or a JSON list of glyph strings. |
| `--gamma` | Gamma correction applied to the colormap. Ignored when --normalize quantile. |
| `--normalize` | Bucketing strategy (default: linear). 'quantile' = GitHub-style: zero is its own bucket, nonzero values are quantile-binned. With 'quantile', --gamma is ignored. |
| `--vmin` | Lower bound for the colormap. Default: computed from values (or meta). |
| `--vmax` | Upper bound for the colormap. Default: computed from values (or meta). |
| `--spacer` | Character placed between cells. Default: a single space. Set to "" for tight grids. |
| `--message` | Footer text. Accepts template placeholders (see docs/SCHEMA.md#templates). |
| `--legend` | Right-aligned legend next to the message. Also accepts templates. |
| `--max-columns` | Cap on output width. Auto-detected from terminal width when omitted. |
| `--direction` | Which edge data anchors to (default: ltr). 'ltr' anchors data on the left; trimming and padding both happen on the right. 'rtl' is the mirror image (GitHub-contributions style). |
| `--pad-to-width` / `--no-pad-to-width` | If the data is narrower than the terminal, fill remaining cells with zero-valued cells (no column labels) so the grid spans the full width. Padding lands on the side opposite --direction. |
| `--simple` | Collapse the colormap to two colors (zero vs nonzero). For when "subtle gradients" isn't the brief. |
| `--invert-headers` / `--no-invert-headers` | Place the column-label header at the bottom and the message/legend footer at the top (default: enabled). Use --no-invert-headers to restore the original layout. |
| `--header-orientation` | How to lay out column-label header (default: auto). 'vertical' stacks each label's chars one per row, useful when every column has a label too long for cell width. 'auto' chooses vertical only when adjacent labels would collide. |
| `--row-labels` / `--no-row-labels` | Show row labels in the left prefix (default: enabled). Use --no-row-labels to hide. |
| `--col-labels` / `--no-col-labels` | Show column labels in the header (default: enabled). Use --no-col-labels to hide. |
| `--follow` | Read NDJSON: one matrix doc per line, render each frame in place. See docs/SCHEMA.md. |
<!-- END GENERATED:cli-flags -->

## Doc `meta`

If you control the producer and want the rendering hints to travel *with* the
data, put them in `meta`. A CLI flag for the same setting will still win —
meta is a *default*, not a mandate.

See [SCHEMA.md#meta-keys](SCHEMA.md#meta-keys) for the full key list and types.

```json
{
  "values": [[…]],
  "meta": {
    "vmin": 0,
    "vmax": 10,
    "normalize": "quantile",
    "direction": "ltr",
    "message": "[COUNT] events · mean [MEAN]",
    "legend": "low  [GRADIENT]  high"
  }
}
```

## Theme JSON

Themes are the bottom of the precedence chain — they supply defaults that
anything above can override. See
[CUSTOMIZING.md#custom-themes](CUSTOMIZING.md#custom-themes) for the JSON shape
and the built-in list.

## Examples

```bash
# CLI overrides everything
echo '{"values":[[1,2,3]],"meta":{"vmax":100}}' | heatgraph --vmax 3

# Producer ships its own hints, picked up via meta
heatgraph-helpers gh-contributions <user> --theme github-dark

# Live data, anchored right, GitHub-style buckets
heatgraph-helpers game-of-life \
  | heatgraph --follow --direction rtl --normalize quantile
```
