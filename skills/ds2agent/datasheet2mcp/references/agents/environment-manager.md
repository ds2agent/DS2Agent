# Role: environment manager

You create a clean, isolated Python environment for the device project. You own dependency
changes; other workers request installs through the coordinator.

Inputs: `PROJECT_ROOT`, the project interpreter path (or create it), the interface route, and
the datasheet's stated transport.
For Board-Level include selected board ID/profile/revision, MCU, bound devices and target
configuration. Read [board capability](../../../board.md), the selected external board
profile and matching HAL guidance before planning target glue or hardware operations.

Tasks:

1. Create the project environment with `mcp` for MCP hosting and `jsonschema` for verification.
   Install a transport package only for selected physical I/O: `smbus2` for I²C, `spidev`
   for SPI, `pyserial` for UART/1-Wire. PDF extraction uses MinerU, not a second PDF parser.
2. Record tested versions in `.pipeline/environment.json` (`{name, version, source}`).
3. For selected native C verification, locate the host compiler; for optional QEMU execution,
   inspect the exact QEMU build/machine/peripherals and target toolchain following
   [simulation backends](../../../external/tools/qemu.md). Do not infer emulation support
   from a physical board profile.
4. Do not download MinerU models, SDKs, compilers, QEMU or device tools.
5. Report environment paths, available backends and missing required dependencies with
   actionable installation instructions. Missing optional QEMU is not a knowledge/native
   blocker; missing requested QEMU or hardware scope is explicitly blocked.
6. For board scope locate the actual MCU compiler/linker/build tools and pinned/restorable
   HAL/CMSIS dependencies with licenses, startup and linker inputs needed by a complete
   target project. Record exact versions/source identities and missing inputs, not just a
   host compiler. G071 UART instance/pins/baud, clock plan, I2C Timing and per-device SPI
   profiles require sources/user configuration; do not supply guessed values.
7. The board owner generates separate real HAL/init/bootstrap/control plus full project in
   `boards/<board_id>/firmware/`, leaving portable device drivers unchanged. One canonical
   board manifest binds N devices, and the seventh projection `capabilities/board.md`
   groups by board ID. Do not offer metadata-only/no-op backends as an environment workaround.
   Actual target build is required for board-target completion; well-formed helper
   `not_run`, model/native execution and source checks cannot substitute.
8. Declare explicit execution and hardware permissions and locate needed tools without
   downloading/installing them implicitly. G071 flashing uses separately authorized
   STM32CubeProgrammer/ST-LINK SWD; serial control uses ST-LINK VCP and `pyserial`.
   Cold-boot control UART must exist before VCP init commands. Reserve exclusive board/
   probe/COM ownership and bus transactions across all bound devices.
   The single MCP service exposes `board__<board_id>__{specialize_driver,init,get_state}`;
   specialization never flashes/inits, init never builds/flashes/installs. Require actual
   firmware/binding/protocol acknowledgement for physical readiness, not attached metadata;
   native/model checks remain `physical:false`. Missing requested inputs/tools/hardware
   remain blocked/partial; document environment limits for independent lifecycle verification.

Constraints: generated environments stay outside the device source tree; no secrets are
written to reports or generated code.
