# Feedback and refinement (closed loop)

Physical observations may refine a device's mutable canonical model layer **before or
after MCP integration**. Refinement is an observation-driven operation, not a mandatory
pre-aggregation stage or a capability restricted to post-deployment use. Source/simulation
delivery without hardware remains valid when hardware validation was not requested;
unavailable requested hardware work stays blocked/partial. Layout and unified-entry rules
are in [../../aggregation.md](../../aggregation.md).

## Mutable vs immutable

| Layer | Contents | Refined by observations? |
|---|---|---|
| immutable | sourced register reset values, min/typ/max, timings, chip ID, ratings, documented formulas/constants | no |
| mutable | provenance-bearing calibration overlays, measured values, observations, model-gap/unmodeled annotations | yes |

Canonical records live in `devices/<device>/models/{knowledge,driver,behavior}.json`,
separating `immutable` and `mutable` records. A measured typical value stays separate from a
datasheet typical value. Documented nonlinear/fixed-point compensation and device trim inputs
are not replaced by a fitted line. Source corrections require a separately source-verified
model revision, not a hardware `refine`.

Measured values and observations record per-device real readings as mutable evidence,
including physical quantities (temperature/voltage), timing samples (startup/conversion
delay), and identity/register reads (chip ID/part/revision). None overwrite the immutable
datasheet-documented value or bound; a measured value stays separate from the documented
spec. A chip-id read differing from the documented ID set (the `mask`/`valid` scope in
[runtime-verification.md](runtime-verification.md)) is still recorded, then classified as a
hardware deviation or a source revision — it never rewrites the immutable documented ID.

Servers exposing `refine` provide the live `IMMUTABLE_DATASHEET` facts mapping used by the
models. The verifier snapshots it before/after **every** refine acceptance, even if the call
raises or rebinds the mapping. Live cross-model checks are required when driver and behavior
models coexist. The authoritative hook contract is [runtime-verification.md](runtime-verification.md).

## Before and after integration

- Before integration, invoke the owning device module's `refine(targets, report)` against
  its canonical model store; revalidate affected outputs before integrating that revision.
- After integration, call `<device_id>__refine(targets, report)` through the one public MCP
  connection. The namespace binds the target device; conflicting device/board identities
  inside the report are rejected, not redirected to another device.
- These are two access paths to the same implementation and canonical records, not two
  copies or separate refinement algorithms. Subsequent calls must observe the committed
  revision; do not leave cached driver/model values at the gateway.
- Refine A must not change B's models, revisions or calibration. Re-emit only A's affected
  projection sections. Serialize writes to shared capability files and access to a shared
  physical board/probe; expand verification only when shared dependencies are affected.
- Moving files, adding the unified entry point or rebuilding an unchanged projection does
  not invalidate calibration. Changed device/board/driver/HAL/plan bindings still require
  revalidation. If refinement changes flashed firmware, rebuild, flash and verify affected
  hardware scenarios before claiming that hardware revision passed.
- Failed candidates leave committed models/artifacts and active bindings unchanged. Do not
  relabel old hardware evidence as validation of new driver or firmware bytes.

Unified-entry acceptance must exercise refinement before integration, read that revision
through the integrated service, then refine through the service and read the new revision
through the component. Also verify other-device isolation, immutable facts, rejection of a
misbound report and failure without a partial commit.

## Observation loop (`refine_from_observations` prompt)

1. `run_hardware` produces physically sourced trace/serial/instrument observations, retaining
   board, artifact, plan, instrument/operator, and timestamp provenance. `run_sim` results
   remain separate model/native/qemu diagnostic evidence; they cannot feed hardware
   calibration or masquerade as physical samples.
2. `apply_measurements(samples)` records physical `{raw, reference}` pairs and measurement
   facts with the full input binding below. It never overwrites a datasheet fact.
3. `twin_diff(expected)` classifies observations as `consistent`, `model_gap`,
   `hardware_deviation`, or `unmodeled`, preserving evidence scope and domain. A deviation on
   one board at one time is not a datasheet correction.
4. `calibrate(pairs)` fits only the declared supported calibration overlay. An affine fit
   `reference = slope*raw + intercept` needs at least three training points whose raw inputs
   are not all equal, separately identified independent-validation data, errors, units,
   domain, and acceptance criteria. Use it only where justified; do not linearize documented
   nonlinear compensation. Unsupported fit kinds are refused.
5. `refine(targets, report)` validates a candidate update, regenerates affected artifacts,
   checks the resulting output binding and independent validation, then commits atomically.

An initial feedback projection may simply state that no physical observations/calibration
exist. No fabricated samples, coefficients, PASS records, or hardware-refinement prerequisite.

## `refine` tool

`refine(targets: ["behavior" | "driver" | "knowledge"], report)` changes only mutable records:

- **behavior** — accepted calibration overlays/measured values and sourced gap annotations;
  immutable reset/min/typ/max/formula/timing records remain unchanged.
- **driver** — apply a validated overlay and regenerate affected portable C artifacts.
  Compute the resulting `driver_sha256` from bytes; never increment/bump it.
- **knowledge** — append physical measurement facts, distinct from datasheet facts.

Every change cites its observations, input binding, and acceptance evidence. Return the
changed records, model/calibration revisions, input/output bindings, and resulting artifact
hashes. Markdown projections and derived register maps are regenerated from canonical
records, not edited by `refine`. No-op artifact regeneration retains its content identity.

## Stable identities

`driver_sha256` identifies the **portable driver artifact set**, not the board, model revision,
or refinement event. The artifact manifest explicitly lists every exported portable C source,
header, and required portable generated include/table; it excludes the manifest itself,
timestamps, build products, HAL/board glue, and feedback/model/markdown records.

Compute it deterministically:

1. Use each listed file's path relative to the device MCP package, with `/` separators
   (for example `driver/<device>_driver.c`). Paths must be unique, portable, and inside it.
2. SHA-256 each file's exact bytes, without newline/content normalization; use lowercase hex.
3. Sort entries lexicographically by relative path. Serialize the list of
   `[relative_path, file_sha256]` pairs as UTF-8 JSON with no BOM, no whitespace or final
   newline, and no ASCII escaping (`ensure_ascii=False`, `separators=(",", ":")`).
4. `driver_sha256` is the lowercase SHA-256 of those serialized manifest bytes.

The same paths and bytes give the same hash across regeneration, relocation, and timestamps.
A knowledge-only edit cannot change this hash. If no driver is produced, declare it
unavailable; do not hash an empty stub and call it a driver. Record separate effective
`hal_sha256` and `plan_sha256` identities over their declared artifact/plan bytes.

`model_revision` is a separate per-model canonical-content revision, not `driver_sha256`.
Change it only when canonical content changes, excluding revision/timestamp bookkeeping;
no-op projection/regeneration does not create a revision. `calibration_revision` identifies
an accepted fit, with its parameters, samples, validation, domain, and bindings. A new
accepted fit has its own revision; regeneration alone does not.

## Calibration bindings and atomic acceptance

Every observation/calibration binds
`{device_id, board_id, driver_sha256, hal_sha256, plan_sha256}` and captures the knowledge,
driver, and behavior `model_revision` values and relevant `calibration_revision`.
`board_id` identifies the actual board/profile revision, not just a device type.

Keep two explicit bindings when refinement changes driver artifacts:

- `input_binding`: the driver/HAL/plan/board and model/calibration revisions that produced
  the physical observations.
- `output_binding`: the resulting driver/HAL/plan/board and resulting revisions against
  which the newly accepted calibration has been independently validated.

Build the candidate overlay/driver and compute its content hash before committing the output
binding. Validate that the fit, resulting driver's application of it, and declared domain
agree; replaying the same samples against a different driver is not automatic revalidation.
Commit the candidate model/artifacts and accepted calibration binding together. Thus a fit
derived from driver D0 and applied by regenerated driver D1 records D0 as input and D1 as
output; it does not immediately invalidate itself by remaining bound only to D0.

A change to device, board, effective HAL, plan, or driver binding makes an older calibration
non-applicable to that new configuration. Archive it, never delete it or silently rebind it;
revalidation is required. A no-op regeneration leaves applicable calibration applicable.
Model revisions preserve traceability; assess whether a changed model affects fit semantics
instead of treating an unrelated knowledge edit as changed driver bytes. Never relabel prior
validation as evidence for a changed formula/domain.

## Board specialization and readiness

[Board specialization](../../board.md) reuses portable driver bytes and generates target
HAL/init/bootstrap/control artifacts from canonical board bindings. It does not rewrite
device facts or silently make board bindings a fourth model/refine target.

When a refinement changes emitted driver or other effective firmware inputs, regenerate
affected board bindings/artifacts and mark their previous readiness/build/hardware evidence
stale. Changed HAL, pins, clocks or control configuration also needs affected revalidation.
Rebuild, explicitly reprogram and initialize the physical board when required; a matching
MCP tool name or old ready reply cannot validate a new firmware binding. Shared firmware
can affect multiple devices even when only one portable driver changed.

Pure integration, relocation, no-op regeneration and unrelated knowledge edits do not
change driver hashes or invalidate applicable calibration. Preserve input/output bindings,
history and device isolation, and re-emit the affected `capabilities/board.md` sections
without making Markdown the canonical state.

## Safety and failure

- Keep source/model/native/qemu/hardware evidence scopes, checks, artifact identities, and
  limitations distinct in records and projections. Simulation is never physical calibration.
- Refuse extrapolation beyond the accepted domain unless explicitly authorized and labeled.
- Missing/incorrect binding, insufficient physical/independent evidence, validation failure,
  immutable mutation, or unsupported targets reject refinement without modifying committed
  models, artifacts, or active calibration. Retain the rejected attempt as separate audit
  evidence, not a successful model update.
