# Runtime requirements

## Environment

- Python 3.11+.
- PDF→Markdown: **MinerU** — `mineru parse <pdf> -o <markdown-file> --pages all`; `-o`
  denotes a file. Use [MinerU guidance](../../external/tools/mineru.md) for version-specific
  structured/image exports. No lossy extractor fallback or implicit model download.
- Bus access (optional, only when a tool performs real device I/O):
  - I²C → `smbus2`; SPI → `spidev`; UART/1-Wire → `pyserial`.
  - A register-model-only server (no physical bus) needs none of these.
- MCP hosting: `mcp` (FastMCP) for delivered stdio/HTTP servers and runtime delivery checks.
- Verifier: `jsonschema` for schema and acceptance-input validation. The helper can inspect
  offline registries without `mcp`, but reports SDK exposure as not checked; such a run alone
  does not satisfy MCP delivery acceptance.
- Board-target scope: the actual MCU toolchain, startup/linker/build tooling and
  pinned/restorable vendor HAL/CMSIS dependencies from the selected profile. A host compiler
  or Python metadata check does not satisfy a target build. Declare missing inputs/tools
  blocked; do not download SDKs/toolchains or run hardware operations implicitly.

The environment manager creates an isolated project environment, installs dependencies,
and records tested versions in `.pipeline/environment.json` (one entry per package:
`{name, version, source}`). Generated environments and results stay outside the device
source tree.

## Consumer skill and active root

MCP/full packages include a rendered root `SKILL.md`; follow
[project skill generation](project-skill.md) and [its source template](templates/project-SKILL.md).
Stage 4 supplies final inventory/bindings; Stage 6 binds concrete supported routes and limits.
This routing projection changes neither canonical model ownership nor the runtime API or
mandatory manifest schema. Knowledge-only datasheet2skill keeps its standalone contract.

Root `USAGE.md` explains whole-package installation into a host-compatible skill directory
and enabling the skill, separately from authorizing dependencies and the single `agent_mcp.py`
connection. Select one active delivered root/store and resolve paths from it, independent of CWD.
Reading/installing `SKILL.md` alone performs no registration, execution, installation or flash.
Discover actual tools and, when supported, resources/prompts; match current schemas and final
inventory before calling. A missing connection/dependency/route is a named prerequisite,
not a fabricated call. Local Markdown is not automatically an MCP resource; remote-only MCP
access does not grant local skill-file access.

Coordinator/extraction acceptance must also cover whole-package host-like relocation,
frontmatter/tokens/portable links and route-to-real-MCP wiring under safe isolated fixtures
per [runtime verification](runtime-verification.md); existing helpers do not implement a
new project-skill verifier or prove automatic host selection or physical hardware support.

## Transport

Every tool that touches the bus goes through one transport adapter selected by the
interface route: `i2c` (address width 7-bit, optional 10-bit), `spi` (chip-select, mode,
max clock), `uart` (baud, bits, parity, stop), or `onewire`. The adapter is the only place
that imports a bus library; register tools call it through typed `read_register` /
`write_register` / `burst_read` helpers. This keeps generated tools transport-agnostic and
testable against a fake adapter.

## Board target and initialization

Read [board capability](../../board.md), the selected external board profile and matching
HAL guidance before generating glue or operating hardware. Validate exact revision/MCU,
pin AF/net/electrical limits, clock plan, bus configurations and control transport from
sources plus explicit configuration. G071 UART instance/pins/baud, clock plan, I2C Timing
and device SPI profiles are required, not guessed.

Generate separate target `device_hal.c/.h` contexts and `board_init.c/.h`, bootstrap/control
code, startup/linker/build recipe and pinned dependencies under `boards/<board_id>/firmware/`,
leaving portable drivers unchanged. `boards/<board_id>/board.json` owns the canonical
multi-device binding, artifact hashes and target-build/hardware evidence; the seventh
`capabilities/board.md` projects it by board ID, not per-device duplicate initialization.
Ship an actual firmware ELF when built. A pseudo-code plan or no-op backend is not delivery.

Use only the one `agent_mcp.py`, with reserved
`board__<board_id>__{specialize_driver,init,get_state}` routing and `BOARD_CAPABILITIES`
mapping each advertised board ID to its root-relative manifest. Reserve/reject colliding
device IDs and give board entries `model=driver`, `scenarios` including `board-level`,
`board_id`, and `board_action`. Do not register a board backend with missing required inputs.

The target cold-boot path must establish HAL/time base/verified system clock and control
UART before any VCP command arrives. Subsequent board init initializes safe CS and enabled
buses/HAL/filter/time base, not the live UART or sensor startup. Validate protocol, firmware
and binding identities and serialize board/probe/COM ownership and complete bus transactions
across N devices. Firmware configures RCC/GPIO/HAL; a host-side attached record is not init.

Track uninitialized/initializing/ready/failed/unknown. Same ready binding returns
`already_ready` without device resets; changed/conflicting active bindings reject
busy/rebuild-required. Failure leaves safe ports/CS; timeout/lost acknowledgement means
unknown, no automatic blind retry. State queries do not initialize. Native/model replies
are explicitly labelled `physical:false`; only a matching actual firmware reply establishes
physical readiness, not calibration.

Specialization never flashes or initializes; init never builds/flashes/installs. Hardware
is opt-in with explicit authorization. For G071, explicit flash operations use
STM32CubeProgrammer over ST-LINK/SWD and control uses ST-LINK VCP, after selected tool guidance.
Source/native/target-build/hardware evidence remain separate: actual target build is
mandatory for board-target completion; a helper accepting `not_run` is not build acceptance.
Requested unavailable hardware remains blocked/partial. Changed driver/HAL/pin/clock/
firmware inputs stale affected bindings/readiness; rebuild/reflash/reinit/revalidate as
required with permission, never silently retaining ready.

## Fake transport

For model-only verification, replace the transport with a deterministic register/command
state model seeded with documented reset values and coefficients. Implement the documented
write/reset, reply, state and virtual-time behavior exercised by each scenario; refuse
unmodeled behavior. Never seed invented datasheet values or present this as physical I/O.

This checks model operations, not the exported C driver. For a selected portable C driver,
compile the actual exported source unchanged with a separate fake-HAL harness. Optional
QEMU execution requires a verified machine/peripheral pairing. Follow
[simulation backends](../../external/tools/qemu.md) for request/result contracts, permission
gates, artifacts and evidence limits. Explicitly label `model`, `native` or `qemu`; never
silently substitute one for another. All simulation results carry `physical: false`.

## Missing tools

No automatic download of MinerU models, SDKs, compilers, or device tools. A missing
dependency returns a clear failure naming the package and the install command. Executing
generated C or launching an external tool requires an explicit `--allow-code-execution`
flag; native execution is not a security sandbox.
