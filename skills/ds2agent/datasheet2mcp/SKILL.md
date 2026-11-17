---
name: datasheet2mcp
description: Convert device datasheets and reference driver/example code into a tested MCP server exposing three device models — knowledge, driver, behavior — through useful tool selection, minimal wrappers around documented register operations and formulas, parallel specialists, and independent verification. Use for datasheet-to-MCP conversions and resumes; requires a host with agent spawning.
---

# datasheet2mcp

Build a tested MCP server from a device datasheet and, when present, its reference
driver/example code. The server exposes three device models — knowledge, driver, behavior —
each as a slice of tools/resources/prompts (see
[models](references/models.md)). Select useful operations, bind each to a documented
register operation, formula, timing, or interface procedure, and expose it through a minimal
wrapper. Device-domain computation stays in the documented datasheet content or the
repository's code; the skill coordinates selection, execution, implementation, and
verification.

## Start here

1. Obtain the datasheet URL or local path (or an existing MinerU Markdown of it), the device
   identifier (`<device>`, e.g. `bmp280`), the output project directory, and any requested
   tasks, source/filter, or resource limits. If a MinerU Markdown of the datasheet already
   exists, use it directly — do not re-run PDF extraction. Ask only for missing required
   inputs.
2. Read [orchestration](references/orchestration.md) for workspace setup, agent assignments,
   handoffs, and resume behavior, and [models](references/models.md) for the three-model
   contract every worker follows.
3. Choose the route by the device's digital interface (I2C / SPI / UART / 1-Wire). Use the
   stages below; interface-specific notes live in [routes](references/routes/README.md).
   For Trial-Running, select explicit `model` / `native` / optional `qemu` backends using
   [simulation backends](../external/tools/qemu.md). Native execution verifies the actual
   exported C driver; a fake-transport Python call is not equivalent evidence.
4. Apply [tool selection and minimal wrappers](references/tool-selection-and-wrapping.md)
   during scanning, implementation, and independent verification. Read
   [runtime requirements](references/runtime.md) when preparing environments and validating
   the server. Load only the current stage and relevant role instructions.
   For MCP/full delivery also follow the [project consumer skill guide](references/project-skill.md):
   Stage 4 supplies final inventory/bindings; Stage 6 renders root `<scope>-agent/SKILL.md`
   from [the source template](references/templates/project-SKILL.md), not an unrendered copy.
5. For board specialization or initialization, read [board capability](../board.md), the
   selected `external/boards/<profile>.md` and matching `external/libraries/*_hal.md`
   guidance before generating glue or performing hardware operations. Resolve the board
   revision, MCU, pins, clocks, bus profiles and control transport from sources plus explicit
   user configuration; missing required inputs block that scope, never justify guessed defaults.

## Workflow

| Stage | Coordinator | Specialists | Completion marker |
|---|---|---|---|
| 1. Environment and tool selection | [Setup and selection](references/prompts/setup-and-discovery.md) | [Environment manager](references/agents/environment-manager.md) and [datasheet scanner](references/agents/datasheet-scanner.md), concurrently | `environment_and_selection_done` |
| 2. Reference execution and reference results | [Execution](references/prompts/reference-execution.md) | Parallel [reference executors](references/agents/reference-executor.md) | `reference_execution_done` |
| 3. Implementation, then independent verification | [Implementation and testing](references/prompts/tool-extraction-and-testing.md) | Parallel [tool extractor–implementors](references/agents/tool-extractor-implementor.md), then fresh [test verifier–improvers](references/agents/test-verifier-improver.md) | `implementation_and_verification_done` |
| 4. MCP integration | [Integration](references/prompts/mcp-integration.md) | Coordinator | `mcp_integration_done` |
| 5. Runtime installation validation | [Requirements](references/prompts/runtime-requirements.md) | Coordinator | `runtime_validation_done` |
| 6. Documentation and ZIP delivery | [Documentation](references/prompts/usage-documentation.md) and [output delivery](references/output-delivery.md) | Coordinator and independent delivery verifier | `delivery_done` |

Interface routes share selection, source binding, agent independence, and completion
requirements; they differ only in transport details.

## Models

Every worker targets one or more of the three device models; a tool is tagged with its model
and its source binding:

| Model | Typical tools | Typical resources/prompts |
|---|---|---|
| knowledge | `retrieve`, `ask`, `tutorial` | datasheet text, register map, tables/figures; Q&A + tutorial prompts |
| driver | `read_register`, `write_register`, `read_chip_id`, `soft_reset`, `configure_*`, `read_*_raw`, `*_compensate`, `export_driver` | C driver header/source, HAL contract; init + periodic-read prompts |
| behavior | `get_parameter`, `evaluate_transfer`, `get_register_model`, `list_states` | parameter/state tables; characteristic-query prompts |

## Scenarios

The three models together deliver six scenarios; tools may carry a `scenarios` tag and
the verifier checks coverage. See [scenarios](references/scenarios.md).

| Scenario | Typical tools |
|---|---|
| Board-Level | `board__<board_id>__specialize_driver`, `board__<board_id>__init`, `board__<board_id>__get_state` |
| Digital-Twin | `twin_state`, `twin_diff` |
| Hardware-Calibration | `calibrate`, `correct`, `apply_measurements`, `refine` |
| MCP Interface | the server itself |
| Trial-Running | `run_sim` (explicit `model` / `native` / optional `qemu`), `run_hardware` |
| Reference-Circuit | `recommend_reference_circuit`, `recommend_wiring` |

The closed loop that refines models from hardware observations is specified in
[feedback](references/feedback.md).

Hardware refinement may run before or after integration whenever observations exist; it is
not a build prerequisite. Both paths update the same device-owned canonical models.
Record source, model, native, QEMU and hardware checks separately; unavailable requested
hardware verification remains blocked, not simulation falsely hardware-verified.

Board-Level specialization extends these six scenarios, not the three device models.
Generate real target HAL adapters, board initialization, cold-boot/control firmware and a
complete reproducible target project while leaving portable device drivers unchanged.
Bind N devices through one canonical `boards/<board_id>/board.json` and initialize their
shared board once. Configuration metadata (`attach_board`) is not initialization. Missing
target inputs/toolchains remain blocked; model/native checks cannot replace an actual
target build for board-target completion or matching hardware acknowledgement when requested.
Build, flash and initialization are separate authorized operations; never flash implicitly.

## Essential requirements

- Choose tools by independently useful tasks on new inputs, grouped by model. Check the
  datasheet register map, timing, and interface chapters plus official example code for gaps.
  Merge duplicates and keep incidental steps internal; register names do not determine tool
  boundaries.
- Bind every tool to concrete documented content: a register read/write, a documented
  compensation/transfer formula, a documented init sequence, a documented timing constraint,
  or an interface procedure. Extract existing example code only when no documented procedure
  exists. Do not invent device algorithms to fill datasheet gaps.
- Run the bound reference computation with documented inputs before implementation. Preserve
  native results, relevant tables/figures, metadata, and reproducibility settings for
  comparison.
- Keep generated code focused on necessary input checks, register/interface calls, and useful
  output serialization. Expose needed documented parameters and test them. Keep benchmark
  recomputation out of production wrappers.
- Finish all implementation assignments before launching verifiers. Every verifier must be a
  fresh agent distinct from every implementer. Verification checks source binding, code
  quality, reference agreement, cross-model consistency, changed inputs, and relevant
  failures.
- Record blocked, merged, deferred, and excluded work with reasons. Never weaken device
  assertions or silently drop a requested tool to report success.

## Helpers and completion

- [verify_workflow.py](scripts/verify_workflow.py) checks recorded assignments, agent
  separation, phase order, and artifact hashes. Follow the
  [workflow-state contract](references/workflow-state.md) at each handoff.
- [verify_mcp_server.py](scripts/verify_mcp_server.py) validates tool schemas and saved
  acceptance calls, required cross-model/refinement checks and installed-SDK tool exposure.
  Use its `jsonschema` dependency and the [acceptance contract](references/runtime-verification.md).
  This does not replace independent source review or native/QEMU/hardware scenario execution.
- Write success markers only after their evidence and workflow gate pass. Worker completion
  alone does not establish success.
- Final delivery follows [aggregation](../aggregation.md): `dist/<scope>-agent/` and its ZIP,
  with a rendered root consumer `SKILL.md`, one public `agent_mcp.py` entry, unified dependencies,
  seven capability projections and device-owned models/modules. Clients configure one MCP service, with
  `<device_id>__<tool_name>` routing, including refinement, and reserved
  `board__<board_id>__{specialize_driver,init,get_state}` board routing. Reject colliding
  device IDs. `capabilities/board.md` groups by board ID, lists bound devices and projects
  canonical board manifests, never owning mutable state; no requested board scope means
  explicit out-of-scope/no binding, not fabricated firmware. Merely bundling separate servers
  is not integration. Follow [output delivery](references/output-delivery.md) for real unified
  MCP calls and fresh-extraction checks; keep review/scratch evidence outside delivery.
  Install/enable the consumer skill by retaining the entire delivered root in the host's
  compatible skill location, not copying one Markdown file. Skill installation/reading does
  not register MCP, install dependencies, execute code, flash or authorize physical actions.
  Knowledge-only datasheet2skill retains its independent standalone contract.

Lead the final response with `dist/<scope>-agent.zip`, then delivered tools grouped by model,
installation/startup directions or usage link, actual source/simulation/hardware validation
scope, and external requirements. State deferred/excluded work and important limits;
selected-tool verification does not establish whole-datasheet correctness. Client
registration is performed only when requested.

Read [optional extensions](references/extensions.md) only for requested resources/prompts,
user-query evaluations, containers, or remote deployment.
