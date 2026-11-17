# Capability outputs (detailed)

For MCP/full conversion, seven capability outputs live under `capabilities/` once per scope.
The original six have device sections projecting canonical per-device models; `board.md`
groups shared target initialization and device bindings by board ID. The authoritative
layout and knowledge-only exception are in [aggregation.md](aggregation.md). Knowledge-only
mode does not promise these seven files.

The generated project's root `SKILL.md` is the consumer entry that routes tasks to these
seven documents and the actual supported MCP tools; follow
[project skill generation](datasheet2mcp/references/project-skill.md). They are not seven
independent installed skills, and their existence does not establish seven implementations.
Install/read the whole project skill, discover its one MCP service and load only the
relevant device/board section. Installation alone does not authorize runtime or hardware.

## Overview

| Output | Aggregates from | Content | Regenerates | Refined? |
|---|---|---|---|---|
| `q_a.md` | knowledge (ask/retrieve) | cited facts | — | no (append measurement facts only) |
| `tutorial.md` | knowledge (tutorial) | step-by-step procedures | — | no |
| `driver.md` | driver | driver spec | C driver | yes (calibration overlay) |
| `mock.md` | behavior | evaluator/emulator spec | C evaluator / supported simulation | yes (mutable overlay) |
| `designer.md` | knowledge + behavior | reference circuit | KiCad schematic | no |
| `feedback.md` | behavior + driver | calibration/refinement records | — | yes (accumulates) |
| `board.md` | board bindings + driver/behavior | target adapters, initialization and build/control contract | real board firmware project | regenerated when effective inputs change |
| `availability.md` | none (sourcing service) | `availability__lookup` / `availability__recommend` purchase links and part recommendations | `availability/availability_tools.py` | — |

Device projections update affected device sections; `board.md` updates affected board
sections when bound firmware inputs change. Canonical models/bindings, not Markdown, own
state. Each section carries source/model/native/target/QEMU/hardware evidence, artifact
identities and limitations. Unavailable content has explicit unsupported/out-of-scope/
evidence-missing reasons; requested blocked work remains partial, not a completed stub.

Root `SKILL.md` is also a derived routing view. Regenerate it when the final tool inventory,
supported scope or device/board identities change; read current canonical records and board
state instead of caching readiness or calibration in that entry. Unrelated observations
and no-op regeneration need not rewrite its routing.

Source-verified projections may be aggregated before physical deployment/refinement. A
feedback section with no hardware observations says so; it must not invent calibration.

Refinement may also precede integration when observations already exist. After integration,
the same device-owned operation is reached through `<device_id>__refine` on the single MCP
service; there is no second model store and no automatic freeze at aggregation.

---

## q_a.md — knowledge Q&A

- **Aggregates from**: the knowledge model's `ask`/`retrieve` facts.
- **Content**: each device's facts organized into six categories (communication, power and
  supply, functional, timing, electrical and interference, reliability and environmental).
  Every fact carries `{category, claim, source, section}`.
- **Behavior**: an answer is a cited fact; a question with no evidence is a deterministic
  refusal, never a generated answer.
- **Refined?** No. `apply_measurements` may append measurement facts as separate records, but
  a datasheet fact is never rewritten.

## tutorial.md — tutorials

- **Aggregates from**: the knowledge model's `tutorial` procedures.
- **Content**: an ordered step sequence per device (`init → configure → read → interpret`),
  each step citing its source block.
- **Purpose**: reproduce a workflow step by step, not just state a result.
- **Refined?** No.

## driver.md — driver spec

- **Aggregates from**: the driver model, following [driver/specification.md](driver/specification.md).
- **Content**, per device:
  1. `init` — chip-id check, startup wait.
  2. `configurations` — mode/oversampling/filter/address settings, the exact register or
     command each writes, and the valid enum values.
  3. `registers` — the register/command each function uses, address, access, bitfields.
  4. `delays` — measurement time, minimum read interval, wait after write/reset.
  5. `data interpretation` — raw-to-physical conversion, linking the behavior model's transfer
     function, with units and resolution.
  6. `restrictions` — read-only/reserved registers, shadowing, burst-read requirements,
     command-only interfaces.
  7. `JSON pseudo-code sequence` — the full `init → configure → read → interpret` order.
- **Regenerates**: `driver.md` + board profile + HAL → C driver. Retargeting a new board or
  changing pins only swaps the board profile; the datasheet is not re-read.
- **Refined?** Yes, only a mutable calibration overlay; documented compensation and
  coefficients remain immutable. Regenerate affected C and recompute `driver_sha256` from
  bytes; unchanged driver content retains the same hash. Model/calibration revisions and
  binding rules follow [datasheet2mcp/references/feedback.md](datasheet2mcp/references/feedback.md).

## mock.md — behavior spec

- **Aggregates from**: the behavior model, following
  [behavior/specification.md](behavior/specification.md); the canonical example is
  [behavior/examples/sht30.md](behavior/examples/sht30.md).
- **Content**, per device:
  - `register/command surface` — address, access class, reset value, bitfields.
  - `state & transitions` — power modes and the documented transitions, reset behavior.
  - `transfer functions` — documented affine, nonlinear, piecewise, or fixed-point
    compensation, preserving evaluation order, units, domain, and required device inputs.
  - `timing & constraints` — sourced measurement/conversion delays and supported virtual
    time/state behavior; unknown timing or replies are explicitly unmodeled.
  - `C transfer evaluator` — raw-to-physical arithmetic only, labeled as such; it does not
    generate bus replies or prove commands, CRC, reset, or timing.
  - `stateful emulator`, when supported — deterministic register/command operations,
    writes/reset, reply layouts/CRC when exercised, states and virtual time constraints.
    Each supported operation requires evidence; other operations are refused.
  - `JSON pseudo-code sequence` — only evidenced operations within the declared model.
- **Regenerates**: only the implemented evaluator/emulator. A formula-only evaluator is not
  the Digital-Twin's stateful device backend or native compiled-driver evidence. Explicit
  model/native/optional QEMU backends follow
  [external/tools/qemu.md](external/tools/qemu.md); no silent fallback or hardware claim.
- **Refined?** Yes, only mutable calibration parameters/observations. The documented
  transfer function and immutable constraints are never rewritten.

## designer.md — reference circuit

- **Aggregates from**: the knowledge model (pin table, electrical facts) and the behavior
  model (supply domains, absolute-maximum ratings), following
  [external/reference-circuit.md](external/reference-circuit.md).
- **Content**, per device (standalone, no cross-device assumption):
  - `supply wiring` — each supply/ground pin to its domain, decoupling where required.
  - `interface wiring` — bus lines to the board controller, documented pull-ups/pull-downs,
    max clock.
  - `address / mode selection` — ADDR/SDO/BOOT strapping that selects a documented address/mode.
  - `reset / enable` — documented reset or chip-enable wiring and timing.
  - `passives` — pull-up/down resistors, decoupling caps, series resistors, with values.
- **Regenerates**: `designer.md` → KiCad schematic.
- **Refined?** No; it is datasheet-grounded. Aggregation does not wire devices together — the
  cross-device conflict check is deferred to "Deferred board assembly" in
  [aggregation.md](aggregation.md).

## feedback.md — calibration and refinement records

- **Aggregates from**: the behavior model (parameters, transfer functions) and the driver
  model (bus read/write).
- **Content**:
  - calibration records — fit kind and parameters, physical sample provenance, training and
    independent-validation error, and applicability domain; affine fitting is not a
    replacement for documented nonlinear compensation.
  - refinement records — mutable fields changed, source observations, model/calibration
    revisions, and input/output artifact bindings.
  - measurement facts — observations that never overwrite a datasheet value.
- **Binding**: device, board, driver content hash, effective HAL hash, and plan hash, with
  model/calibration revisions captured. See the stable hash and binding contract in
  [datasheet2mcp/references/feedback.md](datasheet2mcp/references/feedback.md).
  Retain archived non-applicable records; no-op regeneration does not invalidate them.
- **Refined?** Yes, after physical observations exist. Simulation is separate diagnostic
  evidence and never a hardware calibration source.

`feedback.md` is the **trace** of the runtime refine loop, not a pre-aggregation requirement.
The capability measures, compares, fits where justified, and writes only mutable canonical
model records. It then regenerates affected projections/artifacts and validates the resulting
calibration binding. The newly accepted calibration applies to that resulting driver;
unrelated prior bindings are not silently carried across.

## board.md — board specialization and initialization

- **Contract:** [board.md](board.md). This extends Board-Level; there are still three device
  models and six engineering scenarios.
- **Source:** canonical `boards/<board_id>/board.json`, selected board/HAL/project inputs and
  unchanged portable driver artifacts. One section per board, listing all bound devices.
- **Content:** exact board/revision, provenance and device/driver identities; pin/net/bus/
  address/CS bindings; electrical/clock/I2C Timing/SPI/VCP settings; bootstrap/init/error/
  ownership/idempotence semantics; actual source/build/firmware paths and dependencies;
  namespaced board tools; build/program/serial evidence and missing/blocked scope.
- **Regenerates:** real `board_init.c/.h`, target HAL adapters and a complete startup/linker/
  bootstrap/control/build project. Pseudocode, no-op hooks and metadata attachment are not
  completed board initialization. Native checks do not replace the actual target build.
  APP firmware (`main.c`, `control.c/.h`, `board_binding.h`) follows
  [app/specification.md](app/specification.md).
- **MCP:** one public service exposes board-owned specialization/init/state actions, using
  the reserved `board__<board_id>__...` namespace. Initialization requires an implemented
  matching firmware/control path and permission; it does not implicitly build or flash.
- **Refinement:** not an additional refine target. Device refinement may invalidate affected
  generated board bindings/firmware/readiness; regenerate and revalidate that scope without
  changing unrelated devices or unchanged portable driver hashes.
- **No board requested:** state out-of-scope/no binding. Missing requested configuration,
  SDK/compiler or physical evidence is blocked/partial, never a fabricated completed board.

## availability.md — sourcing tools

- **Scope**: optional, opt-in, scope-wide. Not a device model and not a conversion
  capability; it reads no device model and produces no device model.
- **Aggregates from**: nothing device-owned; it is a standalone sourcing service.
- **Content**: the two tool names (`availability__lookup`, `availability__recommend`), the
  distributor/standards/region mapping, evidence rules, and the recommendation basis.
- **MCP**: the root service exposes the reserved `availability__` namespace from
  `availability/availability_tools.py` (reference
  [../availability/scripts/availability_tools.py](../availability/scripts/availability_tools.py)).
- **Regenerates**: `availability/availability_tools.py` and `capabilities/availability.md`.
- **Refined?** No canonical device state; results are live or constructed at call time and
  never cached into a model.

Reference: [../availability/SKILL.md](../availability/SKILL.md) and
[../availability/references/mcp-tools.md](../availability/references/mcp-tools.md).

## The thread that ties them together

```
q_a / tutorial   ← knowledge (read-only facts and procedures)
driver / mock    ← driver + behavior (specs; refine updates the mutable layer, then
                   regenerates the C driver / C mock)
designer         ← knowledge + behavior (datasheet-grounded reference circuit; no
                   cross-device assumption)
feedback         ← behavior + driver (the trace of the refine closed loop)
board            ← canonical board binding + portable drivers (target adapters/init,
                   complete firmware project and board-wide control lifecycle)
```

`refine` writes only device models' mutable layer. All seven capability files are derived
projections; affected device sections and board bindings are regenerated without making
Markdown the canonical state.
