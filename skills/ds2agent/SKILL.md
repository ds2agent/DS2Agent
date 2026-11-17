---
name: ds2agent
description: Convert device datasheets and associated files, reference driver/example code, or both into a reviewed datasheet skill and a tested MCP server exposing knowledge, driver and behavior models. Deliver a project consumer SKILL.md routing seven capabilities to actual tools. Specialize portable drivers for verified target boards, generate real board initialization projects and board.md, and support conversion/refinement before or after integration.
---

# ds2agent

Turn device datasheets into interactive, reliable AI agents that expose **three device
models** — knowledge, driver, behavior — rather than passive text:

- **knowledge model** — cited facts, retrieval/Q&A/tutorial over the six datasheet categories.
- **driver model** — portable C driver and register/config/measure operations.
- **behavior model** — registers, states, parameter min/typ/max, and transfer functions.

The canonical definition lives in
[datasheet2mcp/references/models.md](datasheet2mcp/references/models.md).

The three models together enable six scenarios: **Board-Level**, **Digital-Twin**,
**Hardware-Calibration**, **MCP Interface**, **Trial-Running**, and **Reference-Circuit**. See
[datasheet2mcp/references/scenarios.md](datasheet2mcp/references/scenarios.md).
Hardware observations refine the models' mutable layer through the closed loop in
[datasheet2mcp/references/feedback.md](datasheet2mcp/references/feedback.md).

## Context directories

Read as needed while converting:

| Directory | Purpose |
|---|---|
| [external/tools/](external/tools/) | versioned extraction, compilation, emulation, schematic and flash/debug workflows |
| [external/boards/](external/boards/) | exact NUCLEO-F103 / G071 / F767 PCB, wiring, power and probe bindings |
| [external/libraries/](external/libraries/) | STM32F1 / G0 HAL initialization, address handling, errors and portable-driver boundaries |
| [external/interfaces/](external/interfaces/) | I2C / SPI / UART / 1-Wire framing, electrical constraints and host/MCU bridge limits |
| [external/reference-circuit.md](external/reference-circuit.md) | sourced standalone/topology wiring, passive selection and circuit verification |
| `knowledge/specification.md` | what the knowledge model extracts (5 fact groups) |
| `behavior/specification.md` + `behavior/examples/sht30.md` | how the behavior model describes a device |
| `driver/specification.md` | how the driver model describes exercising a device |
| [app/specification.md](app/specification.md) | APP (control) firmware: cold boot, line protocol, dispatch and acceptance invariants |
| [board.md](board.md) | specialize portable drivers for a board, generate real initialization/target code, and expose board-owned MCP actions |
| [project skill generation](datasheet2mcp/references/project-skill.md) | render the delivered project's consumer SKILL.md, binding seven task routes to actual supported tools and portable instructions |

For any board-specialization or initialization request, **read [board.md](board.md),
[app/specification.md](app/specification.md), the selected physical board profile and its
matching HAL guidance before generating glue or performing hardware operations**. Board
reference files are required inputs for that task, not optional background. Missing
clock/UART/bus/project inputs block the affected scope.

## Outcomes and delivery

Route by the requested outcome, not solely by whether reference code was supplied:

- **Knowledge only:** follow [datasheet2skill](datasheet2skill/SKILL.md). Deliver its reviewed
  `<device>-datasheet` package; no driver, behavior emulator or seven-capability claim.
- **MCP/device agent:** follow [datasheet2mcp](datasheet2mcp/SKILL.md). A datasheet with
  documented operations is sufficient; reference driver/example code is optional evidence.
- **Combined:** run both workflows and include the reviewed datasheet skill beside each
  device's MCP component.

For MCP and combined runs, [aggregation.md](aggregation.md) is the authoritative delivery
contract. Deliver `dist/<scope>-agent/` and its tested `dist/<scope>-agent.zip`:

```text
<scope>-agent/
├── SKILL.md                      # generated project consumer entry, not this generator
├── USAGE.md
├── agent_mcp.py                  # single public MCP entry for every device
├── manifest.json                 # device routing and final inventory
├── requirements.txt              # unified runtime dependencies
├── capabilities/
│   ├── q_a.md
│   ├── tutorial.md
│   ├── driver.md
│   ├── mock.md
│   ├── designer.md
│   ├── feedback.md
│   └── board.md
├── boards/<board_id>/             # requested board scope only
│   ├── board.json
│   ├── firmware/                  # real init/HAL/control/target project sources
│   └── artifacts/                 # built firmware when available
└── devices/<device>/
    ├── models/                    # canonical knowledge/driver/behavior JSON
    ├── mcp/<device>-mcp/
    └── skill/<device>-datasheet/   # combined output only
```

Use the device identifier as `<scope>` for one device, a stable project identifier for
multiple devices. The seven capability files are scope-wide: the original six have device
sections; `board.md` groups shared initialization and driver bindings by board ID. See
[capabilities-detail.md](capabilities-detail.md).
Record unavailable capability content with its reason; never invent it to fill a file.
Unfinished requested work makes the requested result partial.

Every MCP/full project includes a generated root `SKILL.md` following
[project skill generation](datasheet2mcp/references/project-skill.md). It guides a fresh
agent through the seven task routes, reads the relevant capability section and discovers
actual tools through the one MCP connection. It is distinct from the optional per-device
datasheet reading skill. Install the whole delivered root, not only its Markdown files;
skill installation does not register MCP, install dependencies or authorize execution.

The client registers only the root MCP service. Internal device modules expose namespaced
tools such as `chip_a__read_value` and `chip_b__refine`; resources and prompts are namespaced
too. Refinement is allowed before and after integration against the same canonical records.
Integration alone does not invalidate calibration; affected driver/HAL/board/plan changes
still require revalidation. See [feedback](datasheet2mcp/references/feedback.md).

Board specialization preserves the portable C driver and emits real target adapters,
`board_init.c/.h`, control/bootstrap code and a complete build project. The same public
service exposes `board__<board_id>__specialize_driver`, `__init` and `__get_state`; reserve
that namespace against device-name collisions. Metadata attachment is not initialization,
and board init never implicitly flashes firmware. See [board.md](board.md) for the contract.

A requested **availability** scope adds an opt-in scope-wide sourcing service —
`availability__lookup` and `availability__recommend` — under the reserved `availability__`
namespace. Copy `availability/availability_tools.py` from the
[availability skill](../availability/SKILL.md) and project it as
`capabilities/availability.md` per [../availability/references/mcp-tools.md](../availability/references/mcp-tools.md).
It reads and produces no device model and is not one of the six conversion scenarios;
without an explicit request it is out of scope.

Resolve scripts and references relative to their component directory; bind `SKILL_ROOT` to
that component. Keep review/work directories separate and outside delivery. Independent
datasheet and code tasks may run concurrently within host limits. Every MCP tool binds to
documented registers, formulas, timings, interface procedures or existing repository code.

Build datasheet skills at their final component paths and pass strict verification.
Follow MCP runtime and fresh-extraction checks on the scope-wide ZIP, including portable
references to the delivered canonical models. Report delivery paths, actual verification
scopes and limitations.

## Simulation and hardware evidence

Follow [simulation backends](external/tools/qemu.md): model operations, native execution of
the exported C driver, and optional QEMU firmware execution are distinct backends. QEMU
requires verified machine/peripheral support, not just a board profile or matching CPU.
Keep source, model, native, QEMU and hardware evidence separate. Board refinement is not a
prerequisite for source/simulation delivery; unavailable requested hardware work remains
blocked. Simulation never supplies physical calibration observations.

Hard contracts:

- Never fabricate register addresses, bit fields, formulas, timings, chip IDs, or PASS
  results. Every tool cites the datasheet section or register it binds to.
- The three models share one source of truth; cross-model consistency is a verification
  target, not an aspiration.
- Datasheet facts and runtime observations are separate; an observation never rewrites a
  datasheet value.
- `--allow-code-execution` (or the host equivalent) is required before anything builds,
  flashes, installs, or executes generated code.
