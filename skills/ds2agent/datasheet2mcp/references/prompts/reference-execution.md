# Stage 2: Reference execution and reference results

Coordinator. Continue from `environment_and_selection_done`.

Steps:

1. For each selected tool, identify its reference evidence: a documented register/reset
   value, a documented formula with example coefficients/inputs, or a documented sequence.
2. Launch one reference executor per source module (register blocks, formulas, sequences)
   with exclusive output paths in `reports/` and `tests/data/`. Queue excess work within host
   and machine limits. Record runs in `reports/agent-runs.json`.
3. Wait for all executors to finish; inspect each report. Expected values must come from real
   documented computation, with exact integer/chip-id checks and documented tolerances.
4. Write `.pipeline/references.json` (tool → reference value/artifact + provenance).
5. Write `reference_execution_done` after the workflow gate (`--through execution`) passes.

Do not implement any tool before every reference is recorded.
