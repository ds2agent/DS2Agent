# Optional extensions

Read this file only when the requested conversion needs these; the core workflow does not.

## Resources and prompts beyond the knowledge model

- Additional MCP resources (datasheet page images, packaging/DFM figures, application notes)
  are added only when requested; they must come from the supplied sources and be content-addressed.
- MCP prompts encode reusable device workflows (init sequence, forced-mode single read,
  periodic read, error handling). They are inferred from the datasheet's documented sequences,
  never hand-authored to match a specific tool.

## User-query evaluations

When a benchmark of user queries is requested, generate ground-truth answers by executing the
documented procedure (register ops + compensation) directly, then grade the agent's answers
with a rubric keyed on entities (register, value, unit, condition). Report inter-rater
agreement when multiple graders are used.

## Containers and remote deployment

- A container build is optional; the default delivery is a plain ZIP + `USAGE.md`.
- Remote hosting (e.g. Hugging Face Spaces) is a deployment step, not part of conversion; it
  needs the recipient's platform credentials and must not embed secrets.

## Additional source formats

- Scanned datasheets require OCR before MinerU; the operator supplies the OCR text or a
  text-bearing PDF. MinerU handles image-only pages but the skill does not fabricate text it
  cannot extract.
