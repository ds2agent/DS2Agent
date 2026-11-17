# Review plan

Read this before editing `documents/<source-id>/plan.json` or marking a source reviewed.

Inspect every source and every supplied figure. Check, in order:

1. Reading order and section hierarchy (headers, cross-page prose joins).
2. Register-map rows: every `{address, name, reset, access, bitfields}` cell matches the
   visible table; no invented addresses or reset values.
3. Pin tables and connection diagrams: pin names, package pad numbers, and supply/ground
   groups.
4. Equation blocks (compensation/transfer formulas) transcribed faithfully; use a
   source-rendered image when a formula cannot be transcribed.
5. Figure and table boundaries and captions; captions stay searchable text.

Set a source to `reviewed: true` only after inspection, with specific `review_notes`. The
compact builder removes only repeated short margin headers/footers and a duplicated first-page
title automatically; other content changes are explicit review decisions.

For table routing, record which table goes to `register_map.md` vs `pin_table.md` vs stays in
`datasheet.md`, and any cell-level corrections. A correction must be grounded in the visible
source, not inferred.
