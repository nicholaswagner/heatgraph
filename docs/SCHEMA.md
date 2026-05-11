# heatgraph JSON schemas

The contract between `heatgraph` and whatever upstream process is courageous
enough to feed it.

Producers emit one of these shapes. Consumers validate on the boundary, not
three function calls deep — that's how you end up with a stack trace inside
the renderer at 2am.

There are two documented shapes:

- **[Matrix doc](#matrix-doc)** — the one `heatgraph` itself reads.
- **[Calendar doc](#calendar-doc)** — a sparse, date-keyed shape that
  `cal2matrix` turns into a matrix doc.

Unfamiliar with a term like *bucket*, *palette*, or *direction*? See
[CONCEPTS.md](CONCEPTS.md).

---

## Matrix doc

The one and only document `heatgraph` reads from stdin.

```json
{
  "values": [[0.0, 1.5, 3.2], [1.1, 2.4, 0.8]],
  "cols": ["Jan", "Feb", "Mar"],
  "rows": ["Mon", "Wed", "Fri"],
  "meta": { "vmin": 0, "vmax": 10, "gamma": 0.8 }
}
```

The relationship between the three arrays:

```
            cols[0]  cols[1]  cols[2]
            ───────  ───────  ───────
rows[0] │   v[0][0]  v[0][1]  v[0][2]
rows[1] │   v[1][0]  v[1][1]  v[1][2]
```

### Fields

| Field    | Type                      | Required | Description                                                          |
|----------|---------------------------|----------|----------------------------------------------------------------------|
| `values` | `array<array<number>>`    | yes      | 2D grid of cell values. Outer list is rows; inner lists are columns. |
| `cols`   | `array<string>` or `null` | no       | One label per column. Empty strings render as blank slots.           |
| `rows`   | `array<string>` or `null` | no       | One label per row. Empty strings render as blank slots.              |
| `meta`   | `object` or `null`        | no       | Producer-suggested defaults. See [Meta keys](#meta-keys).            |

### Meta keys

`meta` is free-form. These well-known keys are picked up if present; anything
else is politely ignored.

**Bucketing**

| Key         | Type   | Effect                                                                                                                                  |
|-------------|--------|-----------------------------------------------------------------------------------------------------------------------------------------|
| `vmin`      | number | Lower bound for the colormap. Computed from the data if absent.                                                                         |
| `vmax`      | number | Upper bound for the colormap. Computed from the data if absent.                                                                         |
| `gamma`     | number | Gamma correction applied during bucketing. Ignored when `normalize == "quantile"`.                                                      |
| `normalize` | string | `"linear"` (default) or `"quantile"`. Quantile reserves bucket 0 for `v <= 0` and bins the rest by quantile — the GitHub look.          |

**Layout**

| Key                  | Type    | Effect                                                                                                                  |
|----------------------|---------|-------------------------------------------------------------------------------------------------------------------------|
| `direction`          | string  | `"ltr"` (default) anchors data on the left; `"rtl"` anchors it on the right. Controls which edge trim and pad happen on. |
| `pad_to_width`       | boolean | If true, fills any leftover viewport columns with zero-valued, unlabeled cells. Default false. Padding lands opposite `direction`. |
| `invert_headers`     | boolean | Put column labels at the bottom and message/legend at the top. Default true. The default is correct.                    |
| `header_orientation` | string  | `"auto"` (default), `"horizontal"`, or `"vertical"`. `auto` goes vertical only when adjacent labels would collide.      |
| `row_labels`         | boolean | Show row labels in the left prefix. Default true.                                                                       |
| `col_labels`         | boolean | Show column labels in the header. Default true.                                                                         |

**Templates**

| Key       | Type   | Effect                                                |
|-----------|--------|-------------------------------------------------------|
| `message` | string | Footer message template. See [Templates](#templates). |
| `legend`  | string | Right-aligned footer legend template.                 |
| `from`    | string | First-period label. Fills `[FROM]` in templates.      |
| `to`      | string | Last-period label. Fills `[TO]` in templates.         |

CLI arguments win over meta. See [Precedence](#precedence).

### Templates

`message` and `legend` are templates regardless of whether they came from the
CLI or `meta`. The renderer expands these placeholders using the active theme,
glyphs, and computed value stats:

| Placeholder  | Expands to                                                                              |
|--------------|-----------------------------------------------------------------------------------------|
| `[GRADIENT]` | A swatch of the active palette: one colored glyph per bucket, joined by the spacer.     |
| `[CELL:i]`   | A single colored glyph at bucket index `i`. Out-of-range `i` clamps to the last bucket. |
| `[MIN]`      | The effective `vmin` (CLI > `meta` > computed).                                         |
| `[MAX]`      | The effective `vmax`.                                                                   |
| `[TOTAL]`    | Sum of all input cell values. Padded cells don't count — they're scenery.               |
| `[COUNT]`    | Number of input cells with non-zero values.                                             |
| `[MEAN]`     | Arithmetic mean of all input cell values.                                               |
| `[CELLS]`    | Number of real (non-padded, pre-fit) input cells.                                       |
| `[FROM]`     | `meta.from` if present, else `?`.                                                       |
| `[TO]`       | `meta.to` if present, else `?`.                                                         |

A placeholder whose source is unavailable expands to `?`. Cheerful, isn't it.

There is no escape syntax. Literal `[NAME]` text isn't supported in v1 — pick
a non-colliding word and move on.

### Precedence

For every render parameter:

```
CLI argument  >  meta key  >  theme value  >  computed default
```

If you're surprised by something, walk the chain from left to right.

### Validation rules

- Top-level value must be a JSON object.
- `values` must be a list of lists of numbers. Booleans aren't numbers here —
  we're onto you, JavaScript.
- `cols` / `rows`, if present, must be lists of strings.
- `meta`, if present, must be an object.

Failure modes are loud and on stderr. We don't guess.

---

## Streaming (follow mode)

Without `--follow`, `heatgraph` reads one document and exits — civilized.

With `--follow`, it reads **NDJSON**: one complete doc per line, rendering each
as a new frame in place.

```bash
tail -f events.log | events-to-matrix --window 1m | heatgraph --follow
metrics-to-matrix --interval 5s | heatgraph --follow
heatgraph-helpers game-of-life | heatgraph --follow --glyphs terminal
```

### Framing rules

- One doc per line, delimited by `\n`.
- Each line MUST be a self-contained, compact JSON object — no embedded
  literal newlines. Use `json.dumps(separators=(",",":"))` or `jq -c`.
- Blank lines are ignored.
- A line that fails JSON parsing or schema validation is reported on stderr
  with its line number. The previous frame stays on screen. The stream
  continues. We don't kill the process over one bad line.
- EOF on stdin terminates with exit code 0.

### Rendering behavior

Each frame is drawn in place (cursor-home + erase-to-end-of-screen) so the
terminal doesn't accumulate scrollback. `--follow` therefore assumes a TTY on
stdout; piping `--follow` output elsewhere is undefined and unsupported.

### Producer obligations

If you're feeding a `--follow` consumer:

- Emit compact JSON, one doc per line.
- Line-buffer your stdout (`PYTHONUNBUFFERED=1`, `stdbuf -oL`, or
  `sys.stdout.flush()` after each emit). Otherwise your "live" feed will pile
  up in a 4KB buffer and surprise you all at once.

### What `--follow` does *not* do

- It does not introduce a "delta" doc shape. State and windowing live in the
  producer, where they belong.
- It does not aggregate or merge frames. Each doc fully replaces the previous.
- It does not poll. Cadence is whatever the producer emits.

---

## Calendar doc

A sparse, date-keyed shape. `cal2matrix` consumes it and emits a matrix doc —
weeks, months, and day-of-week labels are derived downstream, so you don't
have to think about which Sunday week 14 started on.

```json
{
  "data": {
    "2026-01-01": 3.0,
    "2026-01-02": 1.0,
    "2026-01-04": 5.0
  }
}
```

### Fields

| Field  | Type                     | Required | Description                                                                                                                                                |
|--------|--------------------------|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `data` | `object<string, number>` | yes      | `YYYY-MM-DD` ISO date strings → numeric values. Missing dates are zero.                                                                                    |
| `meta` | `object` or `null`       | no       | Forwarded straight through to the emitted matrix doc. Use it for `message` / `legend` templates and render hints (`vmin`, `vmax`, `gamma`, `normalize`, …). |

Producer-supplied `meta.from` / `meta.to` win over the ones `cal2matrix`
derives from the data. If you want different bookends than "first and last
date we saw", say so explicitly.

### Validation rules

- Top-level value must be a JSON object.
- `data` must be an object. Keys must parse via `datetime.date.fromisoformat`
  (i.e. real `YYYY-MM-DD`, not "Tuesday-ish").
- Values must be numbers.
- `meta`, if present, must be an object.

### Output of `cal2matrix`

`cal2matrix` reads a calendar doc and emits a matrix doc with:

- `values` — a 7-row × N-column grid (day-of-week × week).
- `cols` — month names, populated at the column where each new month begins.
  Most columns are empty strings, which is correct.
- `rows` — `Mon`, `Wed`, `Fri` populated; the others blank. Looks like the
  GitHub graph because it is the GitHub graph.
- `meta.from` / `meta.to` — ISO strings of the first and last date keys
  observed. Lets `[FROM]` / `[TO]` placeholders just work.

Row alignment follows `--week-starts-on` (default `6` = Sunday-first, matching
GitHub).

### Streaming behavior

One input calendar doc → one output matrix doc, emitted as compact JSON on its
own line and flushed immediately. The pipeline

```
producer --follow | cal2matrix --follow | heatgraph --follow
```

speaks the same NDJSON dialect end to end. No state, no aggregation, no
surprises. See [Streaming (follow mode)](#streaming-follow-mode) for the
framing contract.
