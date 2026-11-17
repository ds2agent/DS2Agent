# Deliverable layout and multi-device aggregation

This is the authoritative root layout for MCP/full conversions. The seven capability
markdown files are scope-wide projections of per-device models and canonical board
bindings, not substitutes for runnable artifacts. A single-device scope uses its device
identifier; a multi-device scope uses a stable project/scope identifier.

## Modes and final artifacts

For any MCP/full conversion, deliver **both** `dist/<scope>-agent/` and the tested
`dist/<scope>-agent.zip`. The ZIP contains one `<scope>-agent/` root with this same layout:

```text
<scope>-agent/
├── SKILL.md                          # generated consumer entry for the whole project
├── USAGE.md
├── agent_mcp.py                      # the single public MCP entry point
├── manifest.json                     # scope/device routing and final exposed inventory
├── requirements.txt                  # unified tested runtime dependency set
├── capabilities/
│   ├── q_a.md
│   ├── tutorial.md
│   ├── driver.md
│   ├── mock.md
│   ├── designer.md
│   ├── feedback.md
│   ├── board.md
│   └── availability.md               # optional sourcing scope
├── availability/                     # optional sourcing tools, requested scope only
│   ├── availability_tools.py
│   └── USAGE.md
├── boards/<board_id>/                # requested board scope only
│   ├── board.json                    # canonical project/board binding
│   ├── board_tools.py                # internal board tool module when needed
│   ├── firmware/                     # init/HAL/APP/startup/linker/build project inputs
│   └── artifacts/                    # built firmware and its declared identities
└── devices/
    └── <device>/                     # repeat for each device in scope
        ├── models/
        │   ├── knowledge.json
        │   ├── driver.json
        │   └── behavior.json
        ├── mcp/
        │   └── <device>-mcp/
        │       ├── <device>_mcp.py
        │       ├── manifest.json
        │       ├── USAGE.md
        │       ├── requirements.txt # or explicit dependency installation instructions
        │       ├── driver/
        │       │   ├── <device>_driver.h
        │       │   └── <device>_driver.c
        │       ├── register_map.json
        │       ├── resources/
        │       └── simulation/     # harness/model/build/target records for exposed backends
        └── skill/                   # only when combined skill output is requested
            └── <device>-datasheet/  # existing fixed datasheet2skill package
```

The C header **and source** travel together when a driver is produced. Unsupported driver or
behavior scope is declared in its canonical model and per-device projections with a reason;
an empty stub is not a completed implementation. `register_map.json` is a derived behavior
view, not an independent model; command-only devices must not acquire invented registers.
Each MCP manifest resolves canonical models relative to its package:
`../../models/{knowledge,driver,behavior}.json`. Resources and all other runtime references
are portable relative paths within the delivered root, never hidden workspace dependencies.
No separate or nested per-device MCP ZIPs are final deliveries.

Root `USAGE.md` names the requested modes, devices, actual configured runtime/model,
supported and excluded operations, dependencies, tested commands, and evidence limits.
Delivery requires verification of the extracted ZIP at a new location; do not call an
untested archive tested. Keep development/review logs outside the ZIP. The capability
feedback audit is delivered data, not a development log.

Root `SKILL.md` is the generated project's consumer/operation entry, following
[project skill generation](datasheet2mcp/references/project-skill.md). Render concrete
project/device/board bindings and seven routes against the final actual tool inventory.
Unavailable routes remain explicit, not fabricated callable entries. Link root `USAGE.md`,
`manifest.json` and all seven capability files through portable local references; read only
the relevant task/device/board section. The skill is a routing projection, not another
canonical model or a cached owner of board readiness.

Install/copy the entire delivered root into the host's compatible skill location and
preserve its relative layout. Select one active root/model store; do not mix an installed
copy with a development server's state. Enabling a skill, connecting its one MCP service,
executing code and authorizing hardware are separate actions. Merely reading/installing
`SKILL.md` does not configure a client, install dependencies, build, flash or open a port.

**Knowledge-only exception:** a datasheet2skill-only request retains its
`<device>-datasheet/` package and its existing delivery rules. It does not require the MCP
directory/ZIP, driver/behavior models, or seven capability projections. Do not fabricate them
or claim that knowledge-only conversion generated all three models/seven outputs.

## Board specialization and initialization

[board.md](board.md) defines the seventh capability. Read it and the selected external
board/HAL references before board work. Generate actual adapters, `board_init.c/.h`,
bootstrap/control code and a complete target build project; do not relabel the profile's
pseudocode as an implementation. Portable device driver artifacts remain unchanged. The APP
(control) firmware — `main.c`, `control.c/.h`, `board_binding.h` — follows
[app/specification.md](app/specification.md).

`capabilities/board.md` groups by board ID and lists bound devices, pins/buses/CS, clocks,
VCP/control settings, generated paths, tool names, artifact identities and actual evidence.
It projects `boards/<board_id>/board.json` plus the existing device models; board bindings
are not a fourth device model. Without requested board scope, record out-of-scope/no binding
instead of inventing firmware. Missing requested inputs or target-build/hardware evidence
leave that scope blocked/partial.

Integrate board tools into the same root service with the reserved
`board__<board_id>__specialize_driver`, `board__<board_id>__init` and
`board__<board_id>__get_state` names. Reject device IDs/final names that collide with this
namespace. Root `BOARD_CAPABILITIES` maps board IDs to their portable `board.json` paths.
Keep bootstrap/control-UART availability separate from bus initialization. Repeated init
for the same ready binding is non-resetting; changed/active bindings are rejected, failed
init never becomes ready and uncertain replies become unknown. No implicit programming.

## Unified MCP runtime

Aggregation includes runtime integration, not just file co-location. Clients configure
**one** scope-level `agent_mcp.py` service (one stdio command or HTTP endpoint) to access
all in-scope devices. Device MCP packages remain internal modules and standalone verification
units, not separate required client registrations.

Expose each device tool as `<device_id>__<tool_name>`, including single-device scopes so
adding a device does not rename existing tools. For example, `chip_a__refine` and
`chip_b__refine` target different canonical model stores through the same MCP connection.
Namespace resources and prompts by device too. Preserve each tool's typed input schema;
do not replace all operations with an untyped catch-all dispatcher.

The root manifest maps final names to device/module/original-tool identities and records
the independently selected expected inventory. Reject duplicate IDs/names and unresolved
bindings before startup. Load each component once and use its live canonical models;
do not copy model values into a second gateway-owned store. One tested environment must
support the integrated dependency set; conflicts block unified delivery rather than being
hidden behind multiple client connections.

The root module exposes the combined `MCP_TOOLS`, `MCP_RESOURCES`, `MCP_PROMPTS` and
`build_server()`. Its live cross-model checks cover each applicable device; its immutable
facts mapping references every device's canonical immutable layer. Component checks remain
necessary but do not substitute for real MCP initialize/list/call acceptance of the unified
entry point, device routing, and before/after-integration refinement.

## Merge workflow and evidence lifecycle

1. Extract and source-verify each device's in-scope canonical models. Preserve citations and
   distinguish immutable datasheet facts from mutable observations/calibration overlays.
2. Project devices into the original six capability files, once per device per file, and
   project canonical board bindings into `board.md`, once per board with its device list.
   Unavailable capability content has an explicit unsupported/out-of-scope/evidence-missing reason.
3. Integrate the verified device modules behind the single public MCP entry point without
   merging their facts. This does not re-extract a datasheet or require physical hardware.
4. Render root `SKILL.md` from the final inventory and supported scopes; package it with
   models, projections and the unified runtime. Verify the extracted package and skill-location
   relocation, including portable links, concrete routes and actual MCP discovery/calls.
   Required requested work that remains blocked makes the delivery partial.
5. Refinement may run before integration through the owning device module and after
   integration through its namespaced tool. Both update the same canonical store, validate
   affected artifacts and incrementally reproject; integration is not a freeze boundary.

Every device's projections retain evidence records for distinct `source`, `model`, `native`,
`qemu`, and `hardware` scopes: status, source/check references, artifact identities,
limitations, and reasons for missing/unsupported/not-run scopes. A source check is required;
no other scope is implied by it. Model simulation does not verify compiled C; native fake-HAL
execution does not verify an MCU peripheral; QEMU does not verify a physical board. Missing
hardware does not block source/simulation delivery unless hardware validation was requested;
then that requested scope remains blocked/partial. Never convert simulation into hardware
verification or calibration.

## The seven scope-wide projections

Details are in [capabilities-detail.md](capabilities-detail.md).

| File under `capabilities/` | Per-device source | Content |
|---|---|---|
| `q_a.md` | knowledge | cited facts and deterministic evidence-missing refusals |
| `tutorial.md` | knowledge | cited procedures |
| `driver.md` | driver | documented operations, restrictions, interpretation, JSON sequence |
| `mock.md` | behavior | transfer evaluator and/or explicitly supported stateful emulator |
| `designer.md` | knowledge + behavior | standalone reference-circuit specification |
| `feedback.md` | mutable model records | observations, calibration bindings, refinement audit |
| `board.md` | board bindings + device driver/behavior models | target driver specialization, real board initialization and build/program/control evidence |
| `availability.md` | none (sourcing service) | `availability__lookup` / `availability__recommend` purchase links and part recommendations |

`availability.md` is an optional, opt-in scope-wide sourcing service — not a device model,
not one of the six conversion scenarios, and it owns no device state. Its tools live in
`availability/availability_tools.py` (reference:
[../availability/scripts/availability_tools.py](../availability/scripts/availability_tools.py)),
are registered on the root service under the reserved `availability__` namespace, and are
specified in [../availability/references/mcp-tools.md](../availability/references/mcp-tools.md).

No hardware observations yet is a valid feedback section stating that no calibration has
been performed. A formula evaluator is not a device-reply emulator. Nonlinear, piecewise,
fixed-point, and compensation formulas retain their documented form; unmodeled operations
are refused. Simulation backends and evidence follow
[external/tools/qemu.md](external/tools/qemu.md).

## Canonical models, refinement, and artifact identity

`devices/<device>/models/{knowledge,driver,behavior}.json` are the canonical structured
models; markdown files, register maps, and generated C are downstream projections. The
model structure and live verification hooks are defined in
[datasheet2mcp/references/models.md](datasheet2mcp/references/models.md) and
[datasheet2mcp/references/runtime-verification.md](datasheet2mcp/references/runtime-verification.md).
`refine` writes only mutable model records, never immutable datasheet facts or markdown.
Refining device A re-emits only affected sections/artifacts for A, not other devices.

Driver projections plus board profile/HAL generate portable C; behavior projections generate
only the evaluator/emulator capabilities actually modeled; reference-circuit projections
generate the schematic when requested. Live cross-model checks must still agree after
regeneration.

Board specialization changes target glue/configuration, not portable driver content. If
refinement changes emitted firmware inputs, regenerate affected board bindings/artifacts
and mark prior board readiness/evidence stale. Rebuild/reflash/reinitialize the affected
requested scope; pure integration or no-op regeneration does not invalidate it.

Content hashes are computed, never bumped. The stable `driver_sha256` algorithm and
`model_revision`/`calibration_revision` bindings are defined in
[datasheet2mcp/references/feedback.md](datasheet2mcp/references/feedback.md). Unchanged
driver bytes retain their hash, including no-op regeneration and knowledge-only edits.
When calibration changes driver bytes, its accepted record retains the observation's input
binding and the validated resulting output binding, so it applies to the regenerated driver
rather than immediately invalidating itself.

## Deferred board assembly and device isolation

Aggregation co-locates devices; it does not wire them together. Check shared bus addresses,
supply rails, and shared-net pull-ups only when the user supplies a board topology. Until
then, reference circuits stand alone. Facts, registers, coefficients, calibration, and
evidence from device A never become device B's facts; cross-device conflicts are reported,
not fused.
