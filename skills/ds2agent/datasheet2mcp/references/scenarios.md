# Engineering scenarios

The three device models (knowledge, driver, behavior) are the device-level representations.
Together they enable six cross-cutting engineering scenarios. The MCP server exposes each
scenario as tools/resources/prompts; a conversion is complete only for the scenarios in scope.

| Scenario | Enabled by | MCP exposure |
|---|---|---|
| Board-Level | driver + behavior | `board__<board_id>__specialize_driver`, `board__<board_id>__init`, `board__<board_id>__get_state`, board resource |
| Digital-Twin | behavior + driver | `twin_state`, `twin_diff`, register-state simulation |
| Hardware-Calibration | behavior + driver | `calibrate`, `correct`, `apply_measurements`, `refine` |
| MCP Interface | all three | the server itself (tools/resources/prompts) |
| Trial-Running | driver + behavior | `run_sim` (`model` / `native` / optional `qemu`), `run_hardware` |
| Reference-Circuit | knowledge + behavior | `recommend_reference_circuit`, `recommend_wiring` |

Each MCP tool may carry a `scenarios` tag listing which scenarios it serves; the verifier
checks that every requested scenario has at least one delivering tool.

## Board-Level

Specializes unchanged portable device drivers for a real board, then initializes the board
through implemented firmware, not `attach_board` metadata. First read
[board capability](../../board.md), the selected external board profile and matching HAL
guidance. Source-check normal operating supply/logic limits (absolute maximum is only a
hard limit), pin/AF/net mapping, bus instance/address/CS, clocks, I2C Timing, SPI profiles
and control UART. Missing requested inputs block this scope. In particular a G071 profile
does not supply a guessed UART instance/pins/baud, clock plan, I2C Timing or device SPI profile.

One canonical `boards/<board_id>/board.json` binds N devices and their portable-driver
hashes, independently of the three device models. Generate real `device_hal.c/.h`,
`board_init.c/.h`, cold-boot/bootstrap and control bridge, startup/linker/build files and
pinned/restorable vendor dependencies. Keep portable `.c`/`.h` unchanged.
`capabilities/board.md` is the seventh scope-wide projection, grouped by board ID with
bound devices, actual paths/identities and separate evidence. No requested board scope
means explicit out-of-scope/no binding, not a fake board implementation.

Expose three tools through the one public `agent_mcp.py`, reserving `board__` against device
ID collisions. Each registry record has `model=driver`, `scenarios` including `board-level`,
`board_id`, and `board_action`:

- `board__<board_id>__specialize_driver` binds verified configuration and selected device IDs,
  generates real target adapters/init/project and artifact identities, without flashing/init.
- `board__<board_id>__init` requires authorization, matching binding/firmware/protocol identity
  and exclusive board/probe/COM ownership, then returns actual matching firmware outcomes.
  It never builds, flashes or installs implicitly.
- `board__<board_id>__get_state` queries actual or explicitly model-labelled state and
  identities without reinitializing.

For VCP control, cold boot must first establish HAL/time base, verified clock and control
UART; an init command cannot bootstrap its own unavailable UART. Separate enabled-bus,
safe-CS and board peripheral initialization from this control bootstrap and sensor-specific
startup, leaving the live UART stable while replying. Firmware, not host Python, configures
RCC/GPIO/HAL. Share board init once across N devices and serialize complete bus transactions.

States are uninitialized/initializing/ready/failed/unknown. The same ready binding returns
`already_ready` without resetting active devices; changed binding or conflicting active
work rejects busy/rebuild-required. Failed init leaves ports/CS safe and never ready.
Timeout/lost response yields unknown, never assumed success or automatic blind retry.
Only a matching hardware acknowledgement supports physical readiness; model/native evidence
is labelled backend and `physical:false`, and readiness does not prove sensor accuracy.
Actual target build is required for board-target completion; metadata verification accepting
explicit `not_run` cannot establish build/hardware acceptance. Hardware init remains opt-in,
and requested unavailable hardware means partial/blocked. Effective binding/firmware changes
stale readiness and require authorized rebuild/reflash/reinit/revalidation as appropriate;
pure merge/relocation/no-op regeneration does not invalidate driver hashes or calibration.

## Digital-Twin

Establishes the mapping between real hardware and a virtual model. The virtual side is the
behavior model's finite register state (reset values, declared state transitions, parameter
records). `twin_state()` returns the current register/state shadow; `twin_diff(expected)`
compares a real observation against the model per register/parameter and classifies each as
`consistent`, `model_gap` (model cannot reproduce the observation), `hardware_deviation`
(real differs from model), or `unmodeled`. A hardware deviation is one board at one time —
never a datasheet correction.

## Hardware-Calibration

Calibrates real hardware or sensor parameters against reference readings. `calibrate(pairs)`
fits a documented linear calibration relation `reference = slope × raw + intercept` from
physical instrument/operator `{raw, reference}` pairs (≥3 points, raw values not all equal),
computes training and independent-validation error, and records the applicability domain.
This calibration overlay does not replace a nonlinear datasheet compensation formula.
`apply_measurements(samples)` writes measurement facts and property observations without
overwriting datasheet values; `correct(name, raw, conditions)` applies the calibration within
its domain and refuses extrapolation unless explicitly allowed; `refine(targets, report)`
writes the versioned, hash-bound refinement into the target models (see feedback.md).

## MCP Interface

The scope exposes one public MCP service (`agent_mcp.py`, stdio by default, HTTP optional).
Internal device modules register `<device_id>__<tool_name>` tools, namespaced resources and
prompts through that single connection. Preserve typed schemas and device-owned canonical
stores; package aggregation alone is not runtime integration.

Refinement works before integration through the component and afterwards through its
namespaced tool, against the same records. Validate routing, other-device isolation and
committed-version visibility per [feedback](feedback.md). Final acceptance includes real
MCP initialize/list/call coverage from the unified entry; direct imports and SDK inventory
checks alone do not establish protocol operation.

## Trial-Running

Uses the explicit backend contract in [simulation backends](../../external/tools/qemu.md):

- `run_sim(backend="model", operations=...)` runs documented operations against a finite
  register/command/state model and returns the trace, final state and error code.
- `run_sim(backend="native", scenario_id=...)` executes the actual exported C driver
  unchanged against a fake HAL and stateful device model in a host harness. This is the
  baseline for a selected C driver, not a requirement for knowledge-only conversion.
- `run_sim(backend="qemu", scenario_id=..., firmware_id=..., target_id=...)` executes
  firmware on a verified machine/peripheral pairing. QEMU is optional; a physical board
  profile is not evidence that the machine or its peripherals are supported.

Require an explicit backend; reject mixed argument shapes, unsupported operations and
missing target support without silent fallback. Results identify backend, artifact hashes,
executed checks and limitations, and always include `physical: false`. A model-only result
does not establish that either C or target firmware executed. Exit zero alone is not a pass.
Native/QEMU build and execution require `--allow-code-execution` or the host equivalent;
missing tools are reported, never automatically installed.

`run_hardware` executes the supported scenario against the real transport and requires
execution permission plus its transport dependency (`smbus2`/`spidev`/`pyserial`).
Hardware records additionally identify device, board, driver, HAL and plan binding.
Simulation passing never implies hardware passing or supplies physical calibration samples.

Delivery records source, model, native, QEMU and hardware verification as separate scopes,
each with artifact identities, actual outcomes and limitations. Hardware refinement occurs
when physical observations exist; it is not a prerequisite for source/simulation delivery.
If requested hardware work cannot run, report that scope as blocked and the requested
overall result as partial.

## Reference-Circuit

Recommends a datasheet-grounded reference circuit and wiring for a device on a target board:
supply decoupling, bus wiring with the documented pull-ups/pull-downs, address/mode
strapping, and reset/enable wiring. `recommend_reference_circuit(requirements)` returns the
full reference circuit; `recommend_wiring(device, board)` returns the net list
`[{device_pin, net, components, source}]`. Every recommendation cites the datasheet; a
binding that would exceed the absolute-maximum ratings is refused, never recommended. See
`external/reference-circuit.md`.

## Refinement (closed loop)

Hardware observations refine the three models' mutable layer only — calibration parameters,
measured typical values, transfer-function coefficients, unmodeled markers, measurement
facts. The immutable datasheet layer (reset values, min/typ/max, timings, chip id) is never
rewritten. The loop, the `refine` tool, and its versioning/invalidation rules are specified
in [feedback.md](feedback.md).

## Scenario vs model

A scenario is a composition of model-tagged tools, not a fourth model. Board-Level and
Trial-Running lean on the driver model (bus ops) and behavior model (limits, state);
Digital-Twin and Hardware-Calibration lean on the behavior model (state, params, transfer
functions) plus the driver model (to read/write the bus); Reference-Circuit leans on the
knowledge model (pin table, electrical facts) and behavior model (supply domains,
absolute-maximum ratings); MCP Interface is the transport for all of them. Cross-model
consistency (a register's reset value, a parameter's min/typ/max, a coefficient used by the
driver) is what makes the scenarios trustworthy.
