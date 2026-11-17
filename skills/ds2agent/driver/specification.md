# Driver model — description specification

Given the device's basic functions (from the knowledge model), describe how to exercise only
the evidenced operations. The canonical structured model is
`devices/<device>/models/driver.json`; `capabilities/driver.md` is its scope-wide projection,
with one device section, following [../aggregation.md](../aggregation.md). Knowledge-only
datasheet2skill does not require a driver model.

The generated portable C header and source implement documented entry points against a small
HAL contract, never `main`, never stdio. Keep the exported driver unchanged in a separate
native fake-HAL harness; model evaluation alone does not exercise that driver. Simulation
backends follow [../external/tools/qemu.md](../external/tools/qemu.md). Unsupported operations
are refused, not replaced by invented reads, writes, defaults, or success responses.

## Board specialization boundary

For Board-Level scope read [board capability](../board.md), the selected
`external/boards/<profile>.md` and matching `external/libraries/*_hal.md` before generating
glue. Portable `.c`/`.h` files stay byte-for-byte unchanged: generate separate target
`device_hal.c/.h` contexts and bus callbacks, real `board_init.c/.h`, cold-boot/control
firmware, startup/linker/build files and pinned/restorable dependencies under
`boards/<board_id>/firmware/`. JSON sequences below document behavior; they do not replace
these executable artifacts or a reproducible actual target build.

Canonical `boards/<board_id>/board.json` binds all N devices to one shared board, independent
of the three device models. Validate sourced pins/AF, normal operating electrical limits,
addresses/CS, clock plan, I2C Timing, per-device SPI profiles and control UART settings.
For G071 do not guess UART instance/pins/baud, clock plan, I2C Timing or device SPI settings.
Missing requested inputs or target toolchain block board-target completion.

Timer/pulse capture (for example G071 TIM2 input capture on PA0/PA1, AF2) is a board-adapter
concern: the adapter owns RCC timer-clock enable, GPIO AF2, `HAL_TIM_IC_*` configuration, NVIC
and the capture/period callbacks, then exposes a typed capture result to the device driver.
The portable driver never initializes a timer peripheral or imports the HAL TIM API; follow the
selected board's timer guidance and treat capture timing as board-level hardware evidence.

The single MCP service reserves `board__<board_id>__specialize_driver`, `__init` and
`__get_state`; metadata uses `model=driver`, `board-level`, board ID and action.
Specialization generates artifacts without flashing or initializing. Cold boot must establish
HAL/time base/verified clock and control UART before a VCP init request can arrive.
Board init configures safe CS and enabled buses/HAL/filter/time base once across bound
devices, not sensor-specific startup; do not reconfigure the live control UART during replies.
Require binding/firmware/protocol identity and exclusive board/port/bus ownership.

Use uninitialized/initializing/ready/failed/unknown states. Same ready binding returns
`already_ready` without resets; changed/conflicting bindings reject busy/rebuild-required.
Failure leaves safe CS/ports and never ready; lost replies mean unknown, not success or blind
retry. `get_state` queries without reinitializing. Only a matching physical firmware reply
supports physical readiness; model/native results carry `physical:false`. No init call builds,
flashes or installs implicitly, and board readiness does not establish sensor calibration.
Verify adapter transactions, lifecycle/failure safety and target build independently;
metadata helper `not_run` is not build or hardware acceptance. Project this evidence and
actual generated paths in the board-grouped seventh output `capabilities/board.md`.

Cross-check every used register/default/coefficient against live canonical behavior records.
When both models are present, the generated server must provide `CROSS_MODEL_CHECKS()` with
nonempty `{name, source, expected, actual}` records as specified in
[../datasheet2mcp/references/runtime-verification.md](../datasheet2mcp/references/runtime-verification.md).
Checks read the current canonical records and actual driver values, not precomputed PASS
flags. This is spot-check evidence, not proof of exhaustive semantic coverage.

## 1. Init

- Documented power-on sequence, chip-id check if present, and startup wait.
  Do not invent a chip-id register for devices without one. A chip-id or register readback
  check compares against the datasheet-documented valid value(s), masking reserved/don't-care
  bits per the bitfield definition: never require raw equality on bits the datasheet leaves
  undefined, and never accept a value outside the documented set.
- If the datasheet documents an explicit operation sequence, follow that sequence.

## 2. Configurations

- Each documented configuration (mode, oversampling, filter, address, ...) with the exact
  register/command it writes and the valid enum values.

## 3. Sensor / actuator / memory registers

- The register or command each function uses, its address, access, bitfields, and the
  read/write that exercises it. Record reserved/don't-care bits and any documented set of
  valid values so readback comparison can mask undefined bits and accept documented variants.

## 4. Delay between operations

- Documented delays: measurement time, minimum read interval, wait after write/reset.

## 5. Data interpretation

- Preserve the behavior model's documented raw-to-physical conversion or compensation,
  including nonlinear/piecewise/fixed-point form, integer widths, evaluation order, device
  coefficients, units, resolution, and applicability domain. Do not force it into `a*x+b`.
- Keep sourced formulas/constants immutable. Any accepted board-specific calibration is a
  distinct mutable overlay, with observation provenance and applicability binding.

## 6. Restrictions and idiosyncrasies

- Read-only/reserved registers, shadowing, burst-read requirements, command-only interfaces,
  and anything the datasheet warns about.

## 7. Transport transaction structure

Encode the exact read/write transaction sequence, not a generic bus idiom. Each transaction
binds to the datasheet section that specifies its framing:

- How many I2C/SPI/UART transactions each operation uses, where STOP / chip-select falls,
  and the consequence of placing it early (lost frame, NACK).
- **Read length comes from the frame's LEN byte, never a fixed maximum buffer.** A
  fixed-max single read (for example 276 bytes) over-reads past the frame and NACKs the
  device once the frame ends.
- Polling loops implement both sourced branches: not-ready → STOP and retry; ready → read
  the frame to completion. When the transport cannot conditionally continue after the
  status byte (a fixed-length HAL read), the practical form is: read the status byte in one
  transfer, and when RDY=1 read the frame in a **second** transfer of the LEN-derived
  length. This satisfies the datasheet's intent (the frame is read to completion); do not
  replace it with a single fixed-maximum read.
- A short settling delay after each transfer may be required on real hardware even when the
  datasheet does not state one; record it as an observed board note, not a magic constant.

## JSON pseudo-code sequence

- The full init → configure → read → interpret sequence as an ordered JSON list of
  `{op, addr/command, payload, expect, wait_ms}` steps, matching the behavior model's
  sequence.

## Canonical records, evidence, and regeneration

Separate immutable datasheet facts from mutable calibration/measurement records in the
canonical JSON. A generated `refine` tool requires the live `IMMUTABLE_DATASHEET` mapping
and before/after verification defined in
[../datasheet2mcp/references/runtime-verification.md](../datasheet2mcp/references/runtime-verification.md);
documentation assertions alone do not satisfy the contract.

The per-device projection declares separate source/model/native/qemu/hardware evidence,
artifact identities, and missing/unsupported limits. Physical refinement can run before
or after integration when observations exist; both paths update the same canonical device
records. It is not an aggregation prerequisite. Unavailable requested validation remains
blocked/unverified; another backend cannot substitute.

Regenerate only affected artifacts from canonical records. `driver_sha256` is a deterministic
content hash of the portable driver artifact set, not a version counter; no-op generation
keeps it unchanged. Track model/calibration revisions and validate input/output calibration
bindings according to
[../datasheet2mcp/references/feedback.md](../datasheet2mcp/references/feedback.md).

Effective emitted driver, HAL, pin, clock or firmware changes stale affected board binding
and readiness evidence. Rebuild/reflash/reinitialize/revalidate affected scope as required
with authorization; do not reuse old readiness. Pure merge/path relocation, no-op generation
or unrelated knowledge changes do not invalidate calibration or change driver content hashes.
