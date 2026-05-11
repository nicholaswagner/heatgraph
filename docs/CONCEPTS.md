# Concepts

A shared vocabulary for the other docs. If a term shows up in a flag table or
a schema field and you're not sure what it means, the answer is probably here.

| Term            | Definition                                                                                                                                |
|-----------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| **bucket**      | One slot in the colormap. A cell's value is mapped to a bucket; the bucket picks the color and the glyph.                                 |
| **palette**     | The ordered list of colors used to fill buckets, low to high.                                                                             |
| **glyph**       | The character drawn in a cell. Each bucket has one glyph; the palette colors it.                                                          |
| **spacer**      | The character placed between cells. Default is a single space. Set to `""` for a dense grid.                                              |
| **prefix**      | The left-margin region used for row labels. Width is computed from the longest label.                                                     |
| **viewport**    | The drawable width — terminal columns minus prefix. Trim and pad are computed against the viewport.                                       |
| **direction**   | Which edge real data anchors to: `ltr` (default) anchors on the left, `rtl` anchors on the right. Controls which edge trim/pad happen on. |
| **padding**     | When data is narrower than the viewport and `--pad-to-width` is set, extra zero-valued, unlabeled cells fill the side opposite `direction`. |
| **trim**        | When data is wider than the viewport, columns are dropped from the side opposite `direction`.                                             |
| **normalize**   | The bucketing strategy. `linear` bins values evenly across `[vmin, vmax]`. `quantile` reserves bucket 0 for `v <= 0` and bins the rest by quantile (the GitHub look). |
| **gamma**       | Exponent applied during linear bucketing. Lower = more contrast at the low end. Ignored under quantile.                                   |
| **vmin / vmax** | The colormap's lower and upper bounds. Computed from the data if unset.                                                                   |
| **header**      | The row(s) of column labels. Position controlled by `invert_headers`; orientation by `header_orientation`.                                |
| **message**     | Footer text. Accepts template placeholders.                                                                                               |
| **legend**     | Right-aligned footer text next to the message. Same template machinery.                                                                   |
| **template**    | A string with `[NAME]` placeholders expanded at render time (`[GRADIENT]`, `[CELL:i]`, `[MIN]`, `[MAX]`, `[TOTAL]`, `[COUNT]`, `[MEAN]`, `[CELLS]`, `[FROM]`, `[TO]`). |
| **matrix doc**  | The JSON object `heatgraph` reads from stdin. See [SCHEMA.md#matrix-doc](SCHEMA.md#matrix-doc).                                            |
| **calendar doc**| A sparse, date-keyed JSON object that `cal2matrix` consumes. See [SCHEMA.md#calendar-doc](SCHEMA.md#calendar-doc).                         |
| **follow mode** | `--follow` reads NDJSON and redraws each line as a new frame in place. See [SCHEMA.md#streaming-follow-mode](SCHEMA.md#streaming-follow-mode). |
