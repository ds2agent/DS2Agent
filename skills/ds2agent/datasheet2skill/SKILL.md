---
name: datasheet2skill
description: Convert datasheet PDFs, register-map tables, pin descriptions, and figures into a compact agent-readable datasheet skill (the knowledge model) with source hashing and verification. PDF-to-Markdown uses MinerU.
---

# datasheet2skill

Use `scripts/datasheet_bundle.py` for every conversion. It snapshots sources, runs MinerU to
convert PDFs to Markdown, prepares editable review plans, builds the fixed reading package,
and keeps review evidence outside the deliverable. It does not execute datasheet content (no
driver, no simulation, no bus access).

## Output

Name the folder `<device>-datasheet`.

This knowledge-only output is an explicit exception to the MCP/full-agent layout in
[aggregation.md](../aggregation.md). It does not produce an MCP ZIP, C driver, behavior
emulator, board package or the seven scope-wide capability files. For combined output,
build this same package under `<scope>-agent/devices/<device>/skill/`; the enclosing agent
workflow owns aggregation and ZIP delivery. A board-specialization/initialization request
belongs to [board capability](../board.md), not this knowledge-only converter; that workflow
must read the selected external board profile and matching HAL guidance and produce real
target artifacts/evidence or mark missing inputs blocked. Extracted wiring prose alone is
not board initialization.

This package's `SKILL.md` is a datasheet reading entry, not the MCP project's operation
router. MCP/full delivery separately generates the root consumer `SKILL.md` defined in
[project skill generation](../datasheet2mcp/references/project-skill.md); this standalone
converter does not generate that project entry or connect an MCP service.

```text
<device>-datasheet/
├── SKILL.md
├── references/
│   ├── index.md
│   ├── datasheet.md        # main datasheet, continuous by section
│   ├── register_map.md     # extracted register map, when present
│   └── pin_table.md        # pin-out and connection tables, when present
└── assets/
    ├── figure/
    └── table/
```

Keep the datasheet text continuous by section. Main figures go in `assets/figure`, tables in
`assets/table`. Captions remain searchable text with ordinary relative links. Originals,
review plans, previews, metadata, and verification reports stay in the external review
directory.

## Prepare and route sources

```bash
python scripts/datasheet_bundle.py prepare '/path/main.pdf' '/path/register-map.xlsx' \
  --work '/path/review' --name bmp280 --title 'BMP280 Digital Pressure Sensor' --main '/path/main.pdf'
```

Review `inventory.json` and edit `bundle.json` before extraction. Assign every source a role
(`main` / `supplement` / `register-map` / `pin-table`), a title, an asset name, and table
routing where applicable. See [bundle-review.md](references/bundle-review.md).

If a source already has an acceptable MinerU Markdown (a `.md` next to the PDF, or a
previously extracted document), reuse that Markdown directly and skip `extract` for that
source. Only extract sources that lack a usable Markdown; never re-run MinerU against a PDF
whose Markdown already exists.

```bash
python scripts/datasheet_bundle.py extract --work '/path/review'
```

`extract` runs `mineru parse <pdf> -o <source-output>/document.md --pages all` per PDF.
`-o` is a Markdown file, not a directory. The helper records that exact export and any
available local images; it does not guarantee a structured/content-list export or acquire
every referenced image. For full structured/image artifacts, follow the separately reviewed
[MinerU export workflow](../external/tools/mineru.md). Missing assets remain an explicit
review limitation/blocker, never fabricated completeness. If MinerU is missing, fail with
installation instructions rather than silently switching extractors.

## Review

Read [review-plan.md](references/review-plan.md) before editing
`documents/<source-id>/plan.json`. Inspect every source. Check reading order, section
hierarchy, register-map rows, pin tables, equation blocks, and figure/table boundaries. Mark a
source `reviewed: true` only after inspection and add specific `review_notes`.

Multi-agent review: give each parallel reviewer exclusive sources and a separate report path;
the coordinator owns `bundle.json` and the build commands. Use a fresh verifier, distinct from
reviewers and coordinator, to compare the assembled package against the visible originals.

## Build and verify

`--output` names the parent directory; the builder appends `<device>-datasheet`. For combined
delivery, pass `<scope>-agent/devices/<device>/skill`, not the final datasheet package path.

```bash
python scripts/datasheet_bundle.py build --work '/path/review' \
  --output '/path/staging' --require-reviewed
python scripts/datasheet_bundle.py build --work '/path/review' --output '/path/delivery' --require-reviewed
python scripts/datasheet_bundle.py verify --work '/path/review' --strict
```

Verification statuses:

- `mechanical_failure` — files, links, hashes, or MinerU output failed.
- `unreviewed` — a source or page review is incomplete.
- `reviewed_with_limitations` — review complete, remaining limits documented.
- `reviewed` — review and mechanical verification complete with no recorded limitations.

`verify --strict` exits 2 for the first two states and 0 for the two reviewed states. A final
skill is labelled a draft only for the first two states. Before delivery, inspect the generated
index, representative prose, register rows, and the smallest figure labels; answer one realistic
retrieval question using only the package.
