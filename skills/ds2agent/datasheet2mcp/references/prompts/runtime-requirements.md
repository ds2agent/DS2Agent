# Stage 5: Runtime installation validation

Coordinator. Continue from `mcp_integration_done`.

Steps:

1. Record `PROJECT_PYTHON`, tested dependencies (`mcp`, `jsonschema`) and selected native/
   QEMU toolchain versions in `.pipeline/environment.json`. Do not install external
   toolchains or QEMU implicitly.
   For board scope read [board capability](../../../board.md), selected external board
   profile and matching HAL guidance; record actual MCU compiler/linker/build tooling and
   pinned/restorable HAL/CMSIS dependencies. Missing required board/UART/clock/bus inputs or
   toolchains block board-target completion, never guessed configurations or no-op backends.
2. Preserve component verification reports separately, then run
   `verify_mcp_server.py agent_mcp.py --project-root <WORK_ROOT>/checks/unified` with the
   agreed model/scenario lists. Fix failures or record a hard blocker; keep evidence outside delivery.
   For advertised board scope require `BOARD_CAPABILITIES`, canonical
   `boards/<board_id>/board.json` and board-grouped `capabilities/board.md`, the seventh
   projection. Check binding/artifact/unchanged portable-driver hashes and reserved
   `board__<board_id>__{specialize_driver,init,get_state}` routing after saved calls.
   All board tools use `model=driver`, `board-level`, `board_id` and `board_action`;
   reject colliding device IDs, orphan manifests/tools and unsafe paths.
3. Copy the complete scope tree elsewhere, create one fresh environment, install root
   `requirements.txt` and re-run the unified helper. All canonical references remain portable;
   SDK inventory must actually run, not be skipped due to a missing `mcp`.
4. Start the single public service and use one real MCP connection to initialize/list/call
   every delivered tool against an independently specified final inventory. Check namespaced
   device/resources/prompts, before/after-integration refinement, other-device isolation and
   failure without partial commit. Follow [feedback](../feedback.md).
   Exercise actual board-control identity checks, one shared init across N devices,
   already-ready idempotence, active/changed binding rejection, safe failure,
   timeout-to-unknown without blind retry, and state queries without reinitialization.
   Verify cold boot establishes HAL/time base/clock/control UART before VCP requests
   and that init leaves the live UART stable. No metadata attach operation establishes ready.
5. Execute advertised simulation scenarios with permission; retain backend/artifact/check
   evidence per [simulation backends](../../../external/tools/qemu.md). Do not count model
   success as native/QEMU/hardware execution.
   For board-target completion build the real init/adapter/bootstrap/control project with
   actual startup/linker/build inputs; record toolchain, firmware artifact and hashes.
   Metadata helper `target_build:not_run` acceptance is not target-build PASS, nor is
   native/model execution physical acceptance. With explicit hardware authorization only,
   execute a separate authorized flash if needed (never implicitly), then init through
   matching firmware/protocol/binding acknowledgement with exclusive board/probe/COM
   and complete bus-transaction ownership. Init never builds/flashes/installs. Hardware
   unavailable when requested stays blocked/partial; model/native results are nonphysical.
   Recheck manifest/evidence identities after calls; changed driver/HAL/pin/clock/firmware
   stales affected binding/readiness and requires authorized rebuild/reflash/reinit/
   revalidation. Pure merge/path relocation/no-op generation does not invalidate calibration.
6. Write `runtime_validation_done` only for the actual requested scope that passed.

A server that fails to import, or a tool that fails its acceptance checks, must not proceed
to delivery.
