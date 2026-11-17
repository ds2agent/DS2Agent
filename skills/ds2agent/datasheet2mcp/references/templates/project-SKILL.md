---
name: {{PROJECT_SKILL_NAME}}
description: {{PROJECT_SKILL_DESCRIPTION}}
---

# {{PROJECT_TITLE}}

Use this delivered project's capabilities, not the ds2agent generation workflow.
**Scope:** {{SCOPE_BINDING}}

**Devices:** {{DEVICE_BINDINGS}}

**Boards:** {{BOARD_BINDINGS}}

## Start here

1. Resolve the active package root as the directory containing this `SKILL.md`, regardless
   of the shell's working directory. Read [USAGE.md](USAGE.md) and
   [manifest.json](manifest.json) for supported operations, dependencies, connection setup
   and final inventory. Read only the relevant device/board section of the capability
   reference selected below; do not load all models or manuals for every task.
2. Connection prerequisites: {{CONNECTION_PREREQUISITES}}
   Use the host's MCP discovery on **one** root `agent_mcp.py` connection. List tools and,
   when supported, resources and prompts. Match exact names, device/board identities and
   current input schemas to the delivered inventory before calling anything. Do not guess
   client commands, tool names, resource URIs or arguments. Internal device modules are not
   additional client registrations. If discovery and the delivered routes disagree, stop
   the affected operation and report the specific mismatch/missing prerequisite.
3. Installing/reading/enabling this skill does not register MCP, start a server, install
   dependencies, execute generated code or authorize hardware. Configure/start/connect MCP,
   install, build or execute only within explicit existing permission, following USAGE.
   Missing connection, dependencies, backend, authorization or route is a named prerequisite,
   not a pretend call or permission to substitute another implementation.

## Choose one route

Availability and callable entries below are specific to the bound devices/boards. A route
may use multiple tools, or have **no callable entry**; seven documents do not mean seven
implemented tools. Use only entries confirmed by live discovery and their current schemas.
Local documents remain readable even when a route has no callable entry.

| Request | Portable local reference | Actual entry / availability by binding |
|---|---|---|
| Q&A: facts, limits, evidence | [Q&A](capabilities/q_a.md) | {{QA_ROUTE}} |
| Tutorial: sourced procedures | [Tutorial](capabilities/tutorial.md) | {{TUTORIAL_ROUTE}} |
| Driver: device operations | [Driver](capabilities/driver.md) | {{DRIVER_ROUTE}} |
| Mock / simulation | [Mock](capabilities/mock.md) | {{MOCK_ROUTE}} |
| Designer / circuit | [Designer](capabilities/designer.md) | {{DESIGNER_ROUTE}} |
| Feedback / refinement | [Feedback](capabilities/feedback.md) | {{FEEDBACK_ROUTE}} |
| Board specialization / init / state | [Board](capabilities/board.md) | {{BOARD_ROUTE}} |

- **Q&A:** preserve device identity and cite the delivered source/section. Refuse unsupported
  facts explicitly; another device's data or a simulation is not a substitute source.
- **Tutorial:** use the selected device's cited sequence and prerequisites. Describing a
  procedure does not authorize executing its steps; separate instructions from actual runs.
- **Driver:** check the selected device, operation restrictions, backend and any board/
  firmware binding and readiness before execution. Hardware needs a real implemented
  backend, matching firmware and explicit permission; tool presence is not physical readiness.
- **Mock:** select only an explicitly supported `model`, `native` or `qemu` backend. Keep
  simulation `physical: false`; never silently switch backends. A transfer evaluator is not
  a stateful device emulator, native C execution is not an MCU test, and QEMU is not hardware.
- **Designer:** allow a selected device subset. Standalone circuits do not silently wire
  devices together. A combined schematic needs supplied topology and checks for every
  electrically present boundary device/component, shared rails, addresses, nets and pull-ups.
  Missing electrical/topology inputs block the affected design; never guess defaults.
- **Feedback:** only supported tools may write permitted mutable canonical records. Retain
  physical provenance, device/board and driver/HAL/plan identities, model/calibration revisions
  and input/output bindings. Simulation is not calibration; “room temperature” is not a
  numeric reference. No arbitrary code edits or immutable datasheet fact changes. Failed
  candidates must not change committed state. Firmware-affecting changes stale affected
  build/readiness evidence and need authorized rebuild/reflash/reinit/revalidation; preserve
  unrelated device state and revalidate shared firmware consequences.
- **Board:** verify exact board, bound devices, pins/bus/control/firmware identities and
  readiness. Missing inputs block work. Specialization never implicitly flashes or initializes;
  init never implicitly builds, installs or flashes. Serialize shared board/probe/COM and
  complete bus transactions. A timeout is unknown, not ready or permission for a blind
  side-effecting retry; use the documented owned recovery procedure. State queries must not
  initialize hardware. Model/native readiness remains nonphysical.

## Evidence and state

{{EVIDENCE_LIMITS}}

Keep source, model, native, target-build, QEMU and hardware evidence distinct, with artifact
identities and limitations. Missing requested work stays blocked/partial; no old or simulated
result establishes current physical readiness, measurement accuracy or calibration.

{{STATE_OWNERSHIP}}

Canonical device models and board bindings own state; these seven Markdown files and this
routing skill are projections, not independent stores. Do not manually edit projections to
simulate refinement. Use only discovered/registered resource URIs: local Markdown is not
implicitly an MCP resource. A remote-only MCP connection does not expose these local files;
obtain the whole package locally if the host cannot read them.

Read current model revisions/evidence from the active canonical store and current board
readiness through its discovered state-query tool; this skill is not a cache of live state.
Re-render this entry when inventory, supported scope or device/board identities change,
not for unrelated measurements or no-op updates.


## Install or relocate this skill

Retain/copy the **entire delivered root**, including runtime, dependencies declaration,
models, capability docs and any board artifacts, into a host-compatible skill directory;
never install only this file or seven documents. Follow USAGE for host name/folder rules,
enabling the skill and the separate MCP connection configuration. Choose one active root/
canonical store; stop or disconnect the old service before switching, and point MCP at the
chosen copy so reads and writes cannot split between installed and development roots.
Preserve all package-relative references after copying/extraction. Skill discovery, MCP
registration and hardware authorization are three separate steps; none implies the others.
