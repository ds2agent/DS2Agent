# MinerU: versioned datasheet conversion and review

MinerU converts a source PDF to reviewable content; it does not certify extracted
registers, equations or pin tables. Use the
[datasheet bundle workflow](../../datasheet2skill/SKILL.md) for the project knowledge
layer; this reference explains its conversion boundary and optional standalone exports.

## Identify the installed command contract

The official current **4.1** documentation distinguishes two command trees:

| Entrypoint | Intended output and behavior |
|---|---|
| `mineru parse` | Document-library client; Markdown file export, cached/background parsing and bounded stdout reading |
| `mineru-kit parse` | Stateless parsing/export; documented `markdown`, `middle_json` and `zip` output formats |

All commands here are **unexecuted templates**, not evidence of a locally installed
MinerU or successful PDF extraction. Record package version, executable path, matching
help/docs, selected tier/backend/engine, local model versions and effective configuration.
Older MinerU CLI/output layouts differ; do not apply these options to a different
release or infer an output schema from a filename.

For complete PDF Markdown through the current document-library client:

```text
mineru parse <input.pdf> --pages all -o <output.md> --wait 600
```

`-o` is a **Markdown file**, not an output directory. `--pages all` requests every PDF
page; the current `mineru parse` default is the first ten. This default is not shared
by every MinerU entrypoint. Page-range CLI indices are one-based; current structured
`page_idx` values are zero-based.

File export contains the requested pages' complete rendered content, independent of
stdout's reading window. Without `-o`, stdout is bounded and can include a continuation
marker; receiving text or using `--pages all` alone does not prove complete output.
`--json` returns a command/status/locator response, **not** Middle JSON.

The bundle helper invokes document-library Markdown export and records available local
images. It is **not** a full kit ZIP exporter and does not guarantee a content-list file
or a complete image/structured-data package. Do not claim it automates the optional
full-export/import workflow below.

## Optional complete structured/assets export

When structured page/block information and packaged images are required, explicitly
select the current stateless ZIP path rather than silently substituting a backend:

```text
mineru-kit parse <owned-input-directory> -o <owned-export-directory> --format zip
```

The documented saved package contains `markdown.md`, `middle_json.json`,
`structured_content.json` and `images/`; inspect each actual archive/result rather than
constructing legacy `<stem>/...` paths. `content_list.json` is not a guaranteed current
CLI export: content-list rendering capability does not make it an exposed CLI option.
Middle JSON and Structured Content are distinct schemas, not interchangeable aliases.

Review/import those artifacts explicitly with source bindings and safe relative image
references. Follow actual asset references instead of guessing filenames; structural
JSON alone may omit image bytes and is not necessarily a complete package. Keep the
original PDF and hash available for page/figure comparison.

## No implicit downloads, services or fallback

Require explicit tool-execution approval (`--allow-code-execution` or host equivalent),
local provisioned dependencies/models, and an approved input/output location. Do not
install packages, download model weights, start a remote service or upload a datasheet
automatically. Inspect existing configuration for remote parsing/VLM/post-processing
endpoints before parsing; endpoint and network use need separate authorization.

The documented `MINERU_MODEL_SOURCE=auto` can choose Hugging Face then ModelScope;
it is **not** an offline setting. For current versions, select `local` and known local
models; missing assets must fail without downloads. Explicit `models download` still
downloads even with `local` configured, so do not invoke it as a readiness check.
The documented `mineru-kit models show` displays readiness but does not fail for every
missing file; `mineru-kit models verify` is the appropriate separately authorized
readiness check, not proof of a successful parse.

Use validated argument vectors and finite host deadlines with retained stdout/stderr.
The sample `--wait 600` is a client wait window, not a universal task deadline: the
document-library parse may continue after `parse_wait_timeout`/exit 1. Preserve returned
task identity, inspect status through the matching version's documented commands and
manage only owned work; do not report timeout as completed or launch duplicate parsers
blindly. Missing executable/models, incompatible CLI/schema, corrupt PDF or incomplete
output is a clear blocked/failed extraction, not permission to fall back to another
extractor, synthetic text, a lower tier or an external service.

## Review before promoting facts

- Check requested/source page coverage, including appendices, blank pages and rotated
  or multi-column layouts. A Markdown file existing does not establish full coverage.
- Compare register/pin/characteristics tables with source images: merged headers,
  continuation rows, units, min/typ/max columns, footnotes, reserved bits and signedness.
- Check equations visually for fractions, subscripts, exponents, minus signs, Greek
  letters, rounding and units. Image-only equations are not usable numeric models until
  explicitly transcribed and source-reviewed.
- Review images for pin-1 orientation, package variants, axis scales, timing diagrams
  and reference circuits. OCR/text order cannot recover electrical connectivity.
- Retain unresolved ambiguities; never silently repair a suspect value or claim
  extraction verifies device behavior.

Keep PDF/hash/revision, MinerU version and effective model configuration, command
arguments, page selection, task/status/timeout evidence, output/assets hashes,
page/block locators and human/agent review findings. Source extraction remains distinct
from [driver compilation](gcc.md), [simulation](qemu.md) and physical measurements.

## Primary references

- [Official quick usage](https://opendatalab.github.io/MinerU/usage/quick_usage/).
- [CLI tools: export files, stdout continuation and task waits](https://opendatalab.github.io/MinerU/usage/cli_tools/).
- [Output schemas, ZIP/assets and saved files](https://opendatalab.github.io/MinerU/reference/output_files/).
- [Model sources, local-only behavior and remote endpoint distinctions](https://opendatalab.github.io/MinerU/usage/model_source/).
