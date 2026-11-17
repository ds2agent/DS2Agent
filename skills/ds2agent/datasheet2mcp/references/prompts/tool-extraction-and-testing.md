# Stage 3: Implementation, then independent verification

Coordinator. Continue from `reference_execution_done`.

Steps:

1. Assign each owning source module to one tool extractor–implementor; give it the selected
   tools, reference evidence, source bindings, and a report path. Launch implementers in
   parallel. Record runs in `reports/agent-runs.json`.
   For Board-Level, read [board capability](../../../board.md), the
   [APP firmware specification](../../../app/specification.md), selected external board
   profile and matching HAL guidance first. Give one board owner all bound device identities
   and verified board config, plus exclusive `boards/<board_id>/` and internal board module
   ownership. Generate real separate HAL adapters/context, `board_init.c/.h`, cold-boot/
   control code, startup/linker/build files and pinned/restorable dependencies, leaving
   portable device `.c`/`.h` unchanged. Missing required inputs block requested board scope;
   never guess G071 UART/clock/I2C Timing/SPI profiles or emit a no-op backend.
2. Wait for all implementation handoffs. Inspect each: wrappers must bind to documented
   content, keep only input checks + bound calls + serialization, and carry `name`, `model`,
   `scenarios`, `description`, `params`, `source`, `fn`, and `acceptance`.
   Board wrappers may be minimal, but their target backend must be real executable firmware,
   not pseudo-code. Canonical `boards/<board_id>/board.json` binds N devices and records
   binding/driver/HAL/plan/artifact identities. Reserve
   `board__<board_id>__{specialize_driver,init,get_state}` in the one MCP service, with
   `model=driver`, `board-level`, `board_id` and `board_action`; reject device collisions.
   Specialization generates without flash/init; init does not build/flash/install.
3. Only after every implementer finished, launch fresh test verifier–improvers whose agent
   IDs differ from every implementer's. Give each the implemented module, the reference
   evidence, and exclusive ownership. They write `tests/code/` and `tests/results/`.
   Include independent expected vectors, native execution of the actual exported C driver
   for selected C scope, and optional admitted QEMU scenarios. Follow
   [simulation backends](../../../external/tools/qemu.md); model-only passing cannot replace
   native/QEMU/hardware evidence. Require execution permission for build/run steps.
   For board scope verify actual adapter transactions, bootstrap HAL/time base/clock/control
   UART before VCP commands, unchanged live UART during init replies, safe CS/bus/filter init
   once across N devices and sensor startup kept in drivers. Require binding/protocol/
   firmware identity, exclusive board/probe/COM and complete bus-transaction ownership,
   already-ready idempotence without device reset, changed/active-binding rejection,
   failed-safe ports/CS and lost response yielding unknown without blind retry.
   Query state without reinitializing. Build the actual target and pin firmware/toolchain
   evidence for board-target completion; metadata `not_run` and native/model passes are not
   target-build/hardware acceptance. Physical init is opt-in and requires a matching hardware
   acknowledgement; label synthetic/native results `physical:false`. Run board manifest/
   artifact/routing checks after saved calls. Project evidence by board ID in the seventh
   `capabilities/board.md`, with missing requested hardware/build scope blocked/partial.
4. Collect verification outcomes; tools failing after the retry budget have their registration
   removed with a recorded reason. Unfulfilled requested board/tools scope stays partial/
   blocked, not complete by silently excluding it.
5. Write `implementation_and_verification_done` after the workflow gate (`--through
   verification`) passes.

Never launch a verifier before all implementers are done; never reuse an implementer's agent
as its verifier.
