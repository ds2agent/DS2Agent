# ds2agent

Turn a device datasheet into a reviewed reading skill, a tested MCP server, and — when a
target board is in scope — real board firmware.

## Overview

Given a datasheet (and optional reference driver/example code), `ds2agent` delivers a project
under `dist/<scope>-agent/`:

- a consumer `SKILL.md` that routes requests to the actual delivered tools;
- one MCP service (`agent_mcp.py`) exposing, per device, tools grouped by three models:
  - **knowledge** — cited facts, retrieval, Q&A, tutorials;
  - **driver** — a portable C driver and register/config/measure operations;
  - **behavior** — registers, states, parameter min/typ/max, and transfer functions;
- optional board specialization — target adapters, `board_init`, and a complete build project.

The three models back six scenarios: board-level bring-up, digital twin, hardware
calibration, the MCP interface itself, trial-running, and reference circuits.

Conversion is done by your coding agent, not by hand. Parallel specialist agents handle
selection, implementation, and independent verification; MCP/full outputs include the
generated project-root `SKILL.md` that routes seven kinds of requests to the delivered
instructions and supported tools.

## Quick Start

The simplest way is to ask your coding agent (Claude Code, Codex, etc.) to install the
`ds2agent` skill, then convert a datasheet:

```
Read the ds2agent skill tree at skills/ds2agent and install the ds2agent skill for this
coding agent.

Use the ds2agent skill to convert this datasheet and its associated files, alongside its
reference code repository if available. Follow the skill instructions for the workflow,
verification, and final delivery.

Datasheet and associated files: <DATASHEET_URL_OR_LOCAL_FILES>
Code repository (if available): <GITHUB_URL_OR_LOCAL_PATH>
Output directory: <PROJECT_DIR>
```

If the skill does not appear after installation, restart your coding agent. For manual
installation, see [Installation & Setup](#installation--setup).

See the [skill instructions](skills/ds2agent/SKILL.md) for supported inputs, workflows, and
deliverables.

## Advanced Usage

### Targeted tasks or sections

Specify the device tasks, register-map section, or datasheet URL to focus on:

```
Use the ds2agent skill to convert <DATASHEET_URL> into MCP tools in <PROJECT_DIR>.
Focus on <TASKS, SECTION, or DATASHEET_URL>.
```

### Repository with API key

Make credentials available through your host's secret mechanism or process environment, then
tell the agent the variable name:

```
Use the ds2agent skill to convert <GITHUB_URL> into MCP tools in <PROJECT_DIR>.
Read the required API key from the environment variable <VARIABLE_NAME>.
```

Credentials stay outside generated code, reports, and the delivered ZIP.

### Board specialization and initialization

Use the [board capability](skills/ds2agent/board.md) to turn verified portable drivers into
real target adapters, board initialization and a complete firmware project:

```text
Use ds2agent's board capability for the selected device IDs and NUCLEO-F103RB.
Read board.md, the F103 profile and matching HAL guide first.
Use I2C1 PB8/PB9 (AFIO remap) and SPI1 PA5/PA6/PA7 with a software CS; resolve PA5/LD2.
Program through STM32CubeProgrammer/ST-LINK SWD; use ST-LINK Virtual COM for control.
Use the supplied pinned target project, clock plan and UART/bus configuration.
If any required input is missing, report it rather than inventing defaults.
Generate real adapter/init/bootstrap/control sources, the target build project and
capabilities/board.md. Expose specialization/init/state through the one MCP service.
Do not flash or initialize hardware without separate explicit authorization.
```

The APP (control) firmware — `main.c`, `control.c/.h`, `board_binding.h` — follows
[app/specification.md](skills/ds2agent/app/specification.md) and is hash-recorded in the
board manifest.

Board tools use `board__<board_id>__specialize_driver`, `board__<board_id>__init` and
`board__<board_id>__get_state`. They preserve portable driver bytes. Initialization
executes in firmware, needs a working control bootstrap and is not `attach_board` metadata.
Native tests, actual target build, programming verification and physical init remain
separate evidence scopes. Missing requested prerequisites makes board delivery partial.

### Examples

The examples below use Claude Code's `/ds2agent` invocation. In Codex, replace it with
`$ds2agent`.

#### BMP280 pressure sensor agent

```
/ds2agent Convert test/bmp280.pdf into tested MCP tools in bmp280_agent.
```

#### MPU-6000A motion-tracking agent

```
/ds2agent Convert datax/RM-MPU-6000A.pdf into tested MCP tools in mpu6000_agent.
Focus on the I2C register map and motion data readout.
```

#### STM32G0 MCU agent

```
/ds2agent Convert mcu-packs/stm32g0 into tested MCP tools in stm32g0_agent.
```

## Installation & Setup

### Prerequisites

- **Coding-agent host:** a host with skill support, shell access, and parallel subagent
  spawning enabled. The coordinator launches specialists and fresh verifier agents through
  the host.
- **Runtime:** Python 3.11+, Git, and **MinerU** (`pip install mineru`) for PDF-to-Markdown.
  MCP delivery uses `mcp`; its verifier also requires `jsonschema`. Optional physical
  transports: `smbus2` (I2C), `spidev` (SPI), `pyserial` (UART/1-Wire).
- **C-driver verification:** a native C compiler for executing the exported driver with a
  fake HAL. Board firmware additionally requires its actual target toolchain and pinned
  SDK/project; native compilation does not satisfy that build. QEMU stays optional per
  verified machine/peripheral pairing. Tools are not auto-installed.

### Manual installation steps

1. Copy the skill folder.

2. Install it for your host (the entire folder, including subdirectories):

   **Claude Code** — personal skill location:

   ```bash
   mkdir -p "$HOME/.claude/skills/ds2agent"
   cp -R skills/ds2agent/. "$HOME/.claude/skills/ds2agent/"
   ```

   **Codex** — personal skill location:

   ```bash
   mkdir -p "$HOME/.agents/skills/ds2agent"
   cp -R skills/ds2agent/. "$HOME/.agents/skills/ds2agent/"
   ```

3. Start your coding agent in your analysis workspace, then use the [Quick Start](#quick-start)
   prompt. The skill installs the generated server's dependencies in its project environment
   during conversion.

## Using the delivered agent

Connect the generated datasheet MCP server to an AI coding agent, such as Claude Code, Codex,
or the Gemini CLI, to use its device tools in conversation.

### Use the generated project skill

The delivered root `SKILL.md` is a project operation skill, distinct from the installed
`ds2agent` generator and the optional per-device datasheet reading skills. Its generation
contract is [project skill generation](skills/ds2agent/datasheet2mcp/references/project-skill.md).
It binds actual device/board identities, routes seven task types to the matching capability
section and discovers supported tools through one MCP connection.

Install/copy the **entire delivered root**, not just `SKILL.md` or `capabilities/`, using
the generated `USAGE.md` and the host-compatible skill name. Preserve relative paths and
choose one active model store. Enabling the skill does not configure MCP, install dependencies
or authorize execution; connect the service only when requested, as described below.
Unavailable routes stay explicit. The seven Markdown files are instructions/evidence
projections, not executable implementations or seven separate skills.

### Connect a generated local MCP server

Extract `dist/<scope>-agent.zip` and follow its root `USAGE.md` to install the unified
dependencies and connect **one** MCP service through `agent_mcp.py`. It exposes tools for
all included devices as `<device_id>__<tool_name>`, plus namespaced resources/prompts.
The `devices/<device>/mcp/<device>-mcp/` packages are internal modules, not additional
required client connections. Canonical models and runtime assets travel with the delivery.

### Connect a remote MCP server

For an HTTP endpoint in Claude Code:

```
claude mcp add --transport http <MCP_NAME> <MCP_ENDPOINT_URL>
```

A helper is provided in [scripts/connect_remote_mcp.sh](scripts/connect_remote_mcp.sh).

### Verification

In Claude Code, check connection status with `claude mcp list` or `/mcp`, then call an
actual namespaced tool (for example `<device_id>__read_chip_id` when delivered).

## Models and scenarios

The canonical definitions live in
[models.md](skills/ds2agent/datasheet2mcp/references/models.md) and
[scenarios.md](skills/ds2agent/datasheet2mcp/references/scenarios.md).

| Model | Encodes | MCP exposure |
|---|---|---|
| knowledge | facts, categories, citations | resources + `retrieve` / `ask` / `tutorial` |
| driver | portable C driver + register operations | register/config/measure tools + `export_driver` |
| behavior | registers, states, params min/typ/max, transfer functions | `get_parameter` / `evaluate_transfer` / `get_register_model` / `list_states` |

| Scenario | Meaning |
|---|---|
| Board-Level | specialize portable drivers for a verified board and generate/execute real board initialization |
| Digital-Twin | mapping between real hardware and a virtual register/state model |
| Hardware-Calibration | calibrate and refine real hardware/sensor parameters via a versioned closed loop |
| MCP Interface | expose tools and data to AI agents via the MCP protocol |
| Trial-Running | run and test programs in simulation or on real hardware |
| Reference-Circuit | recommend a datasheet-grounded reference circuit and wiring |

Hardware observations refine the models' mutable layer (never the datasheet layer) through
the closed loop in [feedback.md](skills/ds2agent/datasheet2mcp/references/feedback.md).

Refinement can run before integration through a device module and afterwards through
`<device_id>__refine` on the unified MCP connection. Both update the same canonical device
records; merging alone does not invalidate calibration or freeze the models. Revalidate
affected driver/firmware/hardware changes and retain other devices' state unchanged.

## Capability outputs (multi-device aggregation)

For MCP and combined conversions, deliver one `dist/<scope>-agent/` directory and tested
`dist/<scope>-agent.zip`. `<scope>` is the device identifier for a single device, a stable
project identifier for multiple devices. [Aggregation](skills/ds2agent/aggregation.md) owns
the exact layout:

- `SKILL.md`: the generated project consumer entry, with actual scope and seven task routes
  bound to delivered instructions and supported tools.
- `agent_mcp.py`, root `manifest.json` and `requirements.txt`: one public service, explicit
  device routing and a unified tested dependency set.
- `capabilities/`: seven scope-wide projections; six have device sections, `board.md` groups by board.
- `devices/<device>/models/`: canonical knowledge, driver and behavior JSON.
- `devices/<device>/mcp/<device>-mcp/`: internal device module and runtime artifacts.
- `devices/<device>/skill/<device>-datasheet/`: reviewed skill when combined output is requested.
- `boards/<board_id>/`: canonical binding and real init/HAL/bootstrap/control/build artifacts
  for requested board scope; built firmware when available.

| Output under `capabilities/` | Content |
|---|---|
| `q_a.md` | cited knowledge Q&A |
| `tutorial.md` | cited tutorials |
| `driver.md` | portable C driver specifications |
| `mock.md` | transfer evaluators and explicitly supported stateful device models |
| `designer.md` | grounded reference circuits and wiring |
| `feedback.md` | calibration/refinement audit records |
| `board.md` | board-specialized driver bindings, real initialization, target project and build/control evidence |

Knowledge-only conversion instead retains the standalone `<device>-datasheet` reading skill;
it does not produce this project-root operation entry or promise an MCP server, three models
or all seven capability files. Missing requested work is blocked/partial, never filled with
invented device behavior.

### Verification scopes and QEMU

Source, model-operation simulation, native C-driver execution, optional QEMU firmware
execution and physical hardware checks are separate evidence scopes. A pass in one does
not establish another. Hardware refinement is not required before source/simulation delivery.

[Simulation guidance](skills/ds2agent/external/tools/qemu.md) defines explicit `run_sim`
backends and evidence requirements. Native execution tests the actual exported C driver
against a fake HAL; QEMU additionally needs a verified machine, firmware boot configuration
and modeled peripherals. A C mock is not automatically a QEMU device. Neither backend proves
electrical compatibility or physical calibration.

## Repository layout

```text
skills/ds2agent/
├── SKILL.md                     # entry: knowledge-only / MCP / combined outcomes
├── aggregation.md               # delivered layout and multi-device aggregation
├── capabilities-detail.md       # seven capability projections
├── board.md                     # board-specialization/init generation and acceptance contract
├── app/specification.md         # APP cold boot, control protocol and dispatch invariants
├── knowledge/specification.md   # knowledge extraction (five fact groups)
├── driver/specification.md      # driver model and portable C boundary
├── behavior/
│   ├── specification.md         # registers, states, parameters and transfer functions
│   └── examples/sht30.md        # transfer-evaluator example
├── external/                    # sourced tools, boards, HAL libraries, interfaces and circuit guidance
├── datasheet2mcp/
│   ├── SKILL.md                 # six-stage workflow + completion markers
│   ├── references/              # orchestration, models, scenarios, project-skill guide/template,
│   │                            # runtime, workflow state, verification, delivery, prompts, agents
│   └── scripts/                 # verify_workflow.py, verify_mcp_server.py,
│                                # verify_board_capabilities.py
└── datasheet2skill/
    ├── SKILL.md                 # PDF -> Markdown (MinerU) knowledge layer
    ├── references/
    └── scripts/datasheet_bundle.py
```
