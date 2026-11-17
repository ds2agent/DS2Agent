# Stage 4: MCP integration

Coordinator. Continue from `implementation_and_verification_done`.

Steps:

1. Assemble verified device modules with `MCP_TOOLS`, resources, prompts and component
   verification hooks. Preserve each device's typed operations and independent source evidence.
2. Stage canonical JSON under `devices/<device>/models/` and internal modules under
   `devices/<device>/mcp/<device>-mcp/`, following [aggregation](../../../aggregation.md).
   Include the actual exported driver and required runtime models/harnesses/build recipes.
   Resolve paths relative to the delivered component, not the work directory.
   For board scope read [board capability](../../../board.md), the selected external board
   profile and matching HAL guidance; stage `boards/<board_id>/board.json`, real unchanged-
   driver adapters/init/bootstrap/control, startup/linker/build/dependencies and built
   firmware at portable final paths. Require actual target-build evidence for board-target
   completion; absent required inputs/toolchain block it, never a guessed/no-op backend.
3. Create root `agent_mcp.py` and one `build_server()` using the installed SDK's supported
   registration/mounting API. Do not assume every FastMCP variant has the same mount API.
   Load each module once and bind `<device_id>__<tool_name>` to its original callable,
   preserving argument schemas; namespace resources/prompts and reject collisions.
   Reserve `board__` and reject colliding device IDs. Register each implemented board's
   `board__<board_id>__{specialize_driver,init,get_state}` through this same service,
   with `model=driver`, `scenarios` including `board-level`, `board_id` and `board_action`.
   Expose `BOARD_CAPABILITIES = {board_id: "boards/<board_id>/board.json"}`; board modules
   are internal, not extra endpoints. Reject orphan/wrong-route board tools.
4. Expose the combined registry and live verification hooks per
   [runtime verification](../runtime-verification.md). Prefix cross-model check names per
   device and reference canonical immutable facts without constructing a second model store.
5. Exercise refinement before integration and through the unified entry after integration.
   Both must observe the same committed records; check other-device isolation, immutable
   facts, invalid binding rejection and atomic failure per [feedback](../feedback.md).
   Serialize shared board/probe and projection-file writes.
   Share one board initialization/lifecycle across N devices and serialize complete bus
   transactions. Effective driver/HAL/pin/clock/firmware changes stale affected binding,
   readiness and evidence; coordinate authorized rebuild/reflash/reinit/revalidation.
   Pure merge/relocation/no-op generation does not invalidate calibration or driver hashes.
6. Write root `manifest.json` with device/module/original-tool routes, independently selected
   final inventory, artifact identities and supported scopes. Keep component provenance too.
   Resolve one tested runtime dependency set in root `requirements.txt`; unresolved conflicts
   block unified delivery rather than requiring multiple client connections.
   Supply Stage 6 the concrete scope/device IDs, board bindings (or none), actual namespaced
   inventory/schemas, backend/evidence limits and blocked/out-of-scope routes for
   [project skill generation](../project-skill.md). Map Q&A, tutorial, driver, mock/simulation,
   designer/circuit, feedback/refinement and board to real independently selected tools;
   a route may need several tools or have no callable entry. Seven projections do not imply
   seven implementations. Preserve canonical ownership; no new mandatory manifest schema.
   Stage 6 renders root `SKILL.md` from [the template](../templates/project-SKILL.md)
   after these bindings are final; do not stage the unrendered template as a consumer entry.
7. Run component checks, then verify `agent_mcp.py` and execute real MCP initialize/list/call
   acceptance through that one entry. Imports or separately passing servers are insufficient.
   Check board manifests/artifact/driver hashes after saved calls to catch drift.
   Exercise bootstrap-before-VCP and real control-path identities, ready-binding idempotence,
   changed/active-binding rejection, safe failure and timeout-to-unknown without blind retry.
   `get_state` never initializes; no `attach_board` metadata can establish ready.
   Specialization never flashes/inits; init never builds/flashes/installs. Calls involving
   hardware require explicit authorization and matching firmware acknowledgement; native/
   model results stay `physical:false`. Helper acceptance of `not_run` is not target/hardware
   PASS. Use isolated fixtures without mutating pinned delivery or active devices.
   Integrate seven projections including board-grouped `capabilities/board.md` from the
   canonical manifest and device models; no board scope means out-of-scope/no binding.
8. Write `mcp_integration_done` only after actual unified-runtime acceptance.

Integrate only verified tools; do not add excluded tools back.
