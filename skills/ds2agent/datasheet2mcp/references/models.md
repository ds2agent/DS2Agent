# Device models

MCP/full conversion uses three interlinked per-device models. They describe the delivered
server's in-scope capabilities, not three independent copies of a datasheet. The
authoritative scope-wide layout and knowledge-only exception are in
[../../aggregation.md](../../aggregation.md).

| Model | What it encodes | MCP exposure | Grounded in |
|---|---|---|---|
| knowledge | facts, categories, citations | resources + `retrieve` / `ask` / `tutorial` | datasheet prose + tables |
| driver | documented digital operations + portable C driver | supported register/config/measure tools + `export_driver` | interface chapters + registers + compensation |
| behavior | pins, supply, registers/commands, states, min/typ/max, transfer functions | supported parameter/transfer/register/state tools | electrical/timing/interface chapters |

For MCP/full delivery the canonical structured paths are
`devices/<device>/models/{knowledge,driver,behavior}.json`. Each carries `device_id`,
`model_revision`, declared supported/unsupported scope, source references, and separate
`immutable` and `mutable` records. Missing legitimate capability scope has an explicit
unsupported/out-of-scope/evidence-missing reason, not fabricated model content or a completed
stub. Required requested work still blocked means partial delivery.

Knowledge-only datasheet2skill retains its existing `<device>-datasheet/` package; it does
not require driver/behavior models, MCP artifacts, board packages or seven capability projections.

Immutable records own sourced facts/formulas and reference stable source/record IDs. Driver
operations refer to the canonical behavior register/default/coefficient IDs rather than
maintaining divergent copies. Mutable records contain provenance-bearing observations,
calibration overlays, and model-gap annotations; they do not replace immutable specifications.
Markdown projections and `register_map.json` are derived views, never alternate canonical
stores. The delivered MCP package loads models through portable relative references
`../../models/{knowledge,driver,behavior}.json`, with no workspace-only dependency.

All device modules are integrated behind the scope's single public `agent_mcp.py` service.
Tools use `<device_id>__<tool_name>`; resources/prompts also carry device identity. Integration
changes access paths, not canonical ownership or content identities. Refinement works both
before and after integration against the same live records; target routing must not permit
updates to another device. See [feedback.md](feedback.md) for isolation and revalidation.

## Board binding is not a device model

The canonical board record is `boards/<board_id>/board.json`, independent of these three
per-device stores. Follow [board capability](../../board.md), reading the selected external
board profile and matching HAL guidance before generating target glue. Its schema-1 binding
records sourced board/revision/MCU, pins, clocks, buses, control, HAL/plan hashes and each
bound device's portable-driver identity. Do not duplicate board initialization in each device.
`capabilities/board.md`, the seventh scope-wide projection, groups by board ID and lists
bound devices; the original six retain per-device sections. With no requested board scope,
state out-of-scope/no binding; missing requested inputs remain blocked.

Board specialization creates a real separate HAL adapter/context, init/bootstrap/control
firmware and reproducible target project, not edits to portable driver `.c`/`.h` or JSON
pseudo-code alone. Expose board tools only through the same public service with reserved
`board__<board_id>__{specialize_driver,init,get_state}` names, `model=driver`,
`scenarios` including `board-level`, plus `board_id` and `board_action` metadata.
Firmware configures the MCU; host binding metadata cannot establish readiness. Actual
target-build evidence is required for board-target completion; native/model success and
well-formed `not_run` evidence are lower-scope evidence only.

Effective driver/HAL/pin/clock/firmware changes stale affected board bindings, artifacts and
readiness; rebuild/reflash/reinitialize/revalidate as required, explicitly authorized.
Pure integration, relocation and no-op regeneration leave driver content hashes and valid
calibration unchanged. Refinement keeps the same canonical device stores before/after integration.

## knowledge model

Grounds every fact in a source block (`source` + `section`/`page` + verbatim substring) and
organizes facts into the six datasheet categories:

1. communication characteristics (interface, protocol, parameters, capabilities),
2. power and supply characteristics,
3. functional characteristics (sensing/control functions, measurement specs),
4. timing characteristics (startup, communication, response, setup/hold),
5. electrical and interference characteristics (VIH/VIL/VOH/VOL, absolute max, EMC),
6. reliability and environmental characteristics (temperature, thermal, MTBF, RoHS/REACH).

Exposure: MCP resources hold the datasheet text, the register map, and tables/figures;
`retrieve(query)` returns cited facts, `ask(question)` returns a cited answer or a
deterministic refusal when no evidence exists, `tutorial(topic)` composes cited facts into a
step-by-step procedure. A refusal is never replaced by a generated answer.

Real observations append per-device measurement facts to the model's mutable records —
physical quantities, timing samples, and identity/register reads (chip ID/part/revision) —
distinct from and never overwriting the sourced datasheet facts above (see
[feedback.md](feedback.md) `apply_measurements` / `refine(knowledge)`).

## driver model

Encodes the device's evidenced digital-interface operations. The runnable layer uses a
minimal transport/HAL contract; `export_driver` renders both the portable C header and
source with documented entry points, never `main` or stdio. Advertise register access,
configuration, reset, raw reads, and compensation only when implemented and sourced; not
every device has registers, chip ID, or reset.

Preserve documented nonlinear, piecewise, multi-input, and fixed-point compensation,
including evaluation order, widths, device trim inputs, domain, and units. Do not reduce it
to an affine fit. Accepted board calibration is a separate mutable overlay.

Native simulation exercises this actual exported C unchanged through a separate fake-HAL
harness. A formula evaluation is not native driver execution.

## behavior model

Encodes the device as a finite, parameterized behavior: pins and supply domains, the
register map with reset values and read/write access, declared state transitions (e.g. power
modes), parameter min/typ/max values with conditions and units, and transfer functions with
their applicability domain.

Exposure: implemented `get_parameter`, `evaluate_transfer`, `get_register_model`, and
`list_states` operations return sourced records and explicit applicability limits.
`evaluate_transfer` evaluates a formula only; it is not a stateful sensor emulator. A
supported emulator needs deterministic commands/registers, writes/reset where modeled,
reply layout/CRC when exercised, states, and virtual time constraints, each with evidence.
Never infer these from a transfer equation.

A per-device measured value or accepted calibration overlay is a mutable record layered on
the immutable formula/parameter/register record, never a rewrite of it: `get_parameter` may
return both the datasheet spec and that device's measured value (physical or timing, e.g.
startup delay), `get_register_model` may return the documented reset alongside the measured
register/identity read (e.g. chip ID), and `evaluate_transfer` applies the accepted overlay
when computing physical values for that device. Without observations, evaluation and
parameter/register reads use the documented records unchanged.

The behavior model is deliberately finite: unknown behavior, unmodeled operations, and
unsupported protocols are refused, not guessed. Explicit model/native/optional QEMU
backends and their distinct evidence follow [../../external/tools/qemu.md](../../external/tools/qemu.md).

## interlinking

- A driver's register/default/coefficient use refers to the canonical behavior record.
  Match addresses, access, reset values, applicable constants, and device trim semantics;
  not every compensation input is a datasheet min/typ/max parameter.
- When driver and behavior models are present, the server must expose
  `CROSS_MODEL_CHECKS()` returning nonempty `{name, source, expected, actual}` records.
  Read live canonical records and the actual values used by the driver. Precomputed PASS
  flags or two copied constants detached from runtime use do not satisfy the contract.
- When `refine` exists, the server must expose `IMMUTABLE_DATASHEET`, the live immutable
  facts mapping actually used by the models. The verifier snapshots it before and after
  every refine acceptance, including failures and mapping rebinding.
- The authoritative hook/acceptance/schema contract is
  [runtime-verification.md](runtime-verification.md). These checks are spot checks, not
  exhaustive semantic verification; saved vectors still require independent source derivation.

## Refinement boundary and evidence lifecycle

Immutable records include sourced reset values, min/typ/max, timings, chip ID, formulas,
and documented coefficients. Mutable records hold board-specific calibration, measured
values, observations, and gap annotations separately. A measured typical value does not
overwrite a datasheet typical value. `refine` never writes immutable records or markdown.
Bindings, deterministic driver content hashing, and model/calibration revisions follow
[feedback.md](feedback.md).

Source verification is required. Each device retains distinct source/model/native/qemu/
hardware evidence status, checks, artifact identities, and limitations through projection
and delivery. Hardware refinement can run before or after integration whenever physical
observations exist; it is not an aggregation prerequisite. Simulation never becomes physical
evidence or calibration. Unavailable requested validation remains explicitly blocked/partial.

The in-scope models support only the implemented scenarios described in
[scenarios.md](scenarios.md); the presence of three JSON files alone does not establish
Board-Level, Digital-Twin, Hardware-Calibration, MCP Interface, Trial-Running, or
Reference-Circuit verification.
