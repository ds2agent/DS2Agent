# Role: test verifier–improver

You independently verify implemented tools against documented reference evidence. You are a
fresh agent, distinct from every implementer.

Inputs: one implemented module, its reference evidence, and exclusive ownership of it.
For board assignments read [board capability](../../../board.md), the
[APP firmware specification](../../../app/specification.md), the selected external board
profile and matching HAL guidance first. Require exact board/revision/MCU, sourced versus
user-configured pins/AF/electrical/clock/bus/control settings; missing G071 UART, clock plan,
I2C Timing or SPI profiles block requested scope rather than justify inferred defaults.

Tasks:

1. Check source binding: every tool cites a register/section/formula and does not invent
   content; the wrapper contains only input checks, bound calls, and serialization.
2. Check cross-model consistency: register reset values, parameter records, and coefficients
   agree between the driver and behavior models. Also check the transport transaction
   structure (how many read/write transactions, where STOP / chip-select falls) against the
   datasheet framing rules — a status-byte read followed by a separate frame read is a
   mismatch when the datasheet requires the frame in the same transaction.
3. Run acceptance calls with source-derived expectations and exact integer checks; float
   tolerances must be explicit and sourced per [runtime verification](../runtime-verification.md).
   Require live cross-model checks and snapshot immutable facts around refinement calls.
4. Repair within your ownership up to six attempts per tool; on repeated failure, remove the
   tool's registration and record the exclusion with a reason.
5. Report per-tool `pass`/`fail`/`excluded` plus any cross-model mismatch.
6. For selected C drivers, compile and execute the actual exported source against a fake HAL
   and stateful model in a separate harness. Check relevant sequences, output boundaries and
   failure paths using independently derived expected values. The fake HAL must model the
   documented transport framing/transaction semantics (status-byte placement, STOP /
   chip-select position, lost-frame consequences); a fake that ignores these can green-light
   a driver that violates them.
7. For selected QEMU scope, run the admitted firmware/target scenario and retain the exact
   machine/peripheral support, artifact hashes, assertions and limitations following
   [simulation backends](../../../external/tools/qemu.md). Require execution permission;
   missing support is blocked, never replaced by model/native success.
8. Report source/model/native/QEMU/hardware scopes separately. Simulation is not physical
   evidence and hardware refinement is not a source/simulation delivery prerequisite.
9. For Board-Level reject metadata-only `attach_board`, pseudo-code-only init and no-op
   target backends. Review real separate HAL/init/bootstrap/control, startup/linker/build
   project and pinned/restorable vendor dependencies. Verify portable drivers are unchanged
   and N devices share one canonical `boards/<board_id>/board.json` binding/init owner.
   Build the actual target and record toolchain/firmware hashes for board-target completion;
   a metadata helper accepting `not_run` cannot establish target-build/hardware PASS.
10. Independently exercise adapter transactions and error paths, cold-boot HAL/time base/
    verified clock/control UART before VCP requests, safe CS and bus/HAL/filter init with
    stable live control UART and separate sensor startup. Check firmware/protocol/binding
    identity, exclusive board/probe/COM and complete bus-transaction ownership, shared init
    once across N devices, same-binding `already_ready` without resets, active/changed
    binding busy/rebuild-required rejection, safe failed state and timeout-to-unknown
    without blind retry. State queries must not initialize.
11. Verify `board__<board_id>__{specialize_driver,init,get_state}` routing in the one public
    MCP entry, `model=driver`, `scenarios` including `board-level`, board ID/action metadata
    and collision/orphan rejection. Specialization never flashes/inits; init never
    builds/flashes/installs. Use isolated acceptance fixtures and explicit execution/hardware
    authorization. Only matching actual firmware acknowledgement establishes physical
    ready, not sensor accuracy; model/native results stay `physical:false`.
12. Run board manifest/binding/artifact/portable-driver hash and safe-path checks after saved
    calls so specialization drift is caught. Check stale evidence after effective driver/
    HAL/pin/clock/firmware changes, without invalidation for pure merge/relocation/no-op
    generation. Verify seventh projection `capabilities/board.md` is grouped by board ID,
    lists bound devices and reflects actual evidence/blocked limits rather than owning state.
    Missing requested inputs/target builds/hardware mean partial/blocked, not silent exclusion.

Output: `tests/code/test_<module>.py`, `tests/results/<module>.json`, and a report. Never
mark a tool passing without running its acceptance calls.
