# Behavior model — description specification

Describe only evidenced finite device behavior: observable operations, state transitions, and
documented conversions. The canonical structured source is
`devices/<device>/models/behavior.json`; `capabilities/mock.md` is a scope-wide projection,
one section per device, following [../aggregation.md](../aggregation.md). Knowledge-only
datasheet2skill does not require this model.

Keep immutable datasheet formulas/constants, reset values, min/typ/max, and timings separate
from mutable observations and board-specific calibration overlays. Refinement never rewrites
a documented transfer formula or turns a measured value into a datasheet specification.

The worked [SHT30 example](examples/sht30.md) illustrates a **transfer evaluator only**,
not a command/reply emulator. For each device, declare which of the following is implemented.

## Register / command surface

- Each evidenced readable/writable register or supported command, its address, access class,
  reset value, bitfields, and source reference.
- For command-based devices, list sourced command words and reply layouts instead of
  inventing registers. Mark missing command/layout/CRC details unmodeled. Completeness is
  relative to the declared supported scope, not an implied claim to emulate the whole chip.

## State and transitions

- Power/operating modes and the documented transitions (e.g. sleep/forced/normal).
- Startup and reset behavior: what value each register takes after reset/POR.

## Transfer functions

- Preserve each documented affine, nonlinear, piecewise, fixed-point, or multi-input
  compensation formula. Include coefficients and their provenance, units, resolution,
  integer widths/evaluation order where relevant, and applicability domain.
- Keep documented coefficients and device-provided trim inputs distinct from mutable
  calibration overlays. Never simplify nonlinear compensation to `physical = raw*a+b`.
- Independently derive reference vectors from source evidence; agreement between a driver
  and an evaluator copied from it is not independent validation.

## Timing and constraints

- Measurement/conversion time, minimum interval between reads, required wait after a write,
  and any "or it will not reply" constraint.

### Extraction robustness (shared with the knowledge layer)

Parameters and timing values follow the same extraction rules as
[`../knowledge/specification.md`](../knowledge/specification.md): map interleaved
`rowspan`/`colspan` tables by row semantics (including unnamed continuation rows), treat
`<details>image content` OCR blocks as source text, and record qualitative constraints as
facts with the numeric value marked `not_stated` when the datasheet gives none. A value that
is only inferable from current × duration is an inference, not a sourced figure — record the
relationship, never emit a fabricated number.

## Transport framing and transaction constraints

Model the transport-level atomicity rules, not only per-command timings:

- Status/ready byte placement (for example "a status byte precedes every read frame").
- Whether a frame must be read or written in **one** transaction, and where the STOP /
  chip-select must fall (for example "when RDY=1 the whole frame must be read before STOP;
  an early STOP discards the remaining bytes").
- Polling/retry semantics for not-ready (STOP and retry) versus ready (read the frame to
  completion; a second transfer of the LEN-derived length is acceptable when the transport
  cannot conditionally continue).
- **The frame read length is LEN-derived, never a fixed maximum** — a fixed-max read
  over-reads past the frame and NACKs the device.
- The consequence of violating a framing rule (lost frame, NACK, bus hang).

These are `{category, claim, source, section}` facts, not implementation notes. The emulator
and the native fake HAL must reproduce them; a fake that ignores a framing rule can
green-light a driver that violates it.

## C transfer evaluator vs stateful emulator

- A transfer evaluator maps raw inputs to physical values. Label it formula-only; it does
  not prove bus replies, CRC, reset, state, or timing. It never implements `main` or stdio.
- A stateful emulator has a deterministic register/command surface, writes and reset where
  supported, modeled state transitions, reply layout/CRC when exercised, and virtual time
  enforcing documented delays. A separate harness drives it.
- Declare finite supported operations and reject unknown inputs/operations explicitly.
  Missing source evidence is not permission to invent plausible device responses.
- Value selection: the mock uses the per-device measured value or accepted calibration
  overlay when one exists for that device, otherwise the datasheet-documented value. A
  measured value layers over the immutable documented value and never replaces it; with no
  recorded observation the mock returns the documented value.

## JSON pseudo-code sequence

- The evidenced observable sequence as an ordered JSON list of
  `{op, addr/command, payload, expect, wait_ms}` steps. Include only modeled operations;
  formula-only examples have evaluation steps, not fabricated bus transactions.

## Runtime evidence and canonical consistency

Explicit model/native/optional QEMU backends follow
[../external/tools/qemu.md](../external/tools/qemu.md). Model simulation proves modeled
operations only. Native executes the actual exported C driver through a fake HAL; QEMU
requires a separately verified machine/device pairing and exercised firmware. Neither is
physical hardware evidence, and none supplies hardware calibration.

Every per-device projection declares source/model/native/qemu/hardware status, checks,
artifact identities, limitations, and absent-scope reasons. Source verification precedes
delivery; refinement is allowed before and after integration when physical observations exist.
Unavailable requested validation remains partial/blocked, never silently substituted.

The driver and behavior models share canonical register/default/coefficient records.
Generated servers with both models must expose live `CROSS_MODEL_CHECKS()` records; those
with `refine` must expose the live `IMMUTABLE_DATASHEET` facts mapping, checked before and
after every refine acceptance even on failure. The authoritative executable hook contract is
[../datasheet2mcp/references/runtime-verification.md](../datasheet2mcp/references/runtime-verification.md).
Stable model/calibration revisions, driver content hashes, and input/output bindings follow
[../datasheet2mcp/references/feedback.md](../datasheet2mcp/references/feedback.md).
