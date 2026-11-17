# Stage 1: Environment and tool selection

Coordinator. You own `PROJECT_ROOT`, `DEVICE_NAME`, and the requested scope: which models
(knowledge / driver / behavior) and scenarios (board-level / digital-twin /
hardware-calibration / mcp-interface / trial-running / reference-circuit) are in scope, plus any task/source
filter.

Inputs: datasheet URL or local path, device identifier, requested models and six-scenario
scope, optional reference code repository; for Board-Level, selected board ID/profile/
revision, MCU, all bound devices, sourced pins/clocks/bus/control configuration and explicit
execution/hardware permissions. Board binding is independent of the three device models.

Steps:

Before board glue or hardware work, read [board capability](../../../board.md), the
[APP firmware specification](../../../app/specification.md), the selected external board
profile and matching HAL guidance. A board profile alone does not supply
G071 UART instance/pins/baud, clock plan, I2C Timing or per-device SPI profile: resolve
required inputs from sources/user config or mark requested board scope blocked.

1. Create `PROJECT_ROOT` and `.pipeline/`. Write `project_setup_done`.
2. Place or clone the source at `sources/<device>/`; retain its source identity. Write
   `source_setup_done`.
3. Create `registers/`, `src/tools/`, `tests/{code,data,results,logs,summary}/`,
   `reports/`, `tmp/{inputs,outputs}/`. Write `workspace_setup_done`.
4. Launch the environment manager and the datasheet scanner concurrently. Give each its role
   prompt, bound inputs, and a report path. Record both runs in `reports/agent-runs.json`
   (schema 1).
5. When both return, review the scanner's selection — tools per model, source bindings,
   evidence feasibility, deferred/blocked items — against the environment result.
6. Write `.pipeline/selection.json` (scope identifier, requested outputs, tool → model,
   scenarios, source, owner module, reference evidence, selected simulation backends) and
   `.pipeline/route.json` (interface, address/clock/CS/baud). Select backend scope using
   [simulation backends](../../../external/tools/qemu.md); record unsupported requested
   targets/hardware as blocked. A board profile or matching CPU does not certify QEMU.
   Record board configuration provenance, missing inputs and N-device binding/driver
   identities; reserve `board__` against colliding device IDs. Select the three
   `board__<board_id>__{specialize_driver,init,get_state}` tools as `model=driver`,
   `scenarios` including `board-level`, with `board_id` and `board_action`; do not select
   metadata `attach_board` as a substitute for real initialization. Assign one board owner
   to generate `boards/<board_id>/board.json`, separate target HAL/init/bootstrap/control
   and full startup/linker/build/dependency artifacts without changing portable drivers.
   Require actual target build for board-target completion, not helper `not_run` acceptance.
   Init requires matching firmware reply and authorized exclusive board/port ownership;
   specialization/init never implicitly flash, and init never builds/installs.
   Plan the VCP cold-boot UART before command-driven board init, shared init once across
   devices, idempotence/conflict/failure/unknown behavior and separate native/hardware evidence.
   Plan seven capability projections including board-grouped `capabilities/board.md`;
   no requested board scope means explicit out-of-scope/no binding, not fabricated firmware.
7. Write `environment_and_selection_done` only after the workflow gate
   (`verify_workflow.py --through setup`) passes and the selection is coherent.

Do not proceed to stage 2 with an empty or unreviewed selection.
