# OpenOCD: owned debug-server and programming sessions

OpenOCD connects a supported adapter/transport to a configured MCU and flash driver.
It is not a firmware compiler or a generic way to program any Cortex-M. Adapter support,
target scripts and flash capabilities vary by build and version.

All examples are **unexecuted templates**. Resolve installed executable/version,
compiled adapter drivers and the matching configuration-script tree first. Record
script paths/hashes and any vendor patches; do not mix a binary with a random release's
scripts or automatically download a tool/probe update.

## Admit a board/probe configuration

Require physical-board authorization and `--allow-code-execution` or host equivalent.
Bind the exact MCU order code, board/revision and [board profile](../boards/), probe
serial, transport, speed, reset wiring, power/reference voltage and approved memory
ranges. Family-level target scripts must still be checked against the exact part's
flash/RAM geometry. Never suppress an unexpected IDCODE to make a connection proceed.

Select the owned probe explicitly with the installed adapter driver's documented
serial selector (`adapter serial <serial>` for supported drivers). Verify the
connection report matches the target; first-enumerated USB is not a stable binding.
Reserve the entire board and probe across devices, and stop competing
[ST-LINK](stlink.md), [J-Link](jlink.md), CubeIDE and other sessions.

Prepare one reviewed session configuration that:

- Sources the exact board script, or appropriate interface and target scripts without
  duplicating an interface already selected by a board script.
- Selects the serial before initialization; chooses the actual transport supported by
  that driver. `swd` and ST-LINK HLA transport names are not universally interchangeable.
- Sets a board-supported speed and reset strategy; no generic reset wiring is assumed.
- Disables unnecessary GDB/Tcl/telnet listeners for one-shot programming, or restricts
  debugging listeners to the local host with explicit ports and access policy.

The upstream manual distinguishes configuration commands from execution commands.
Set adapter/transport/ports before `init`. Command names can differ across releases
(for example older underscore-style server commands); use matching installed help.
Configuration files are executable Tcl: only load owned reviewed files.

## Build, program/verify, then run

Build separately with [GCC and target startup/linker inputs](gcc.md); retain ELF/hash,
link map and approved ranges. Inspect the image and flash-sector overlap with any
bootloader, calibration or user data before permitting a write.

```text
openocd -f <owned-session.cfg> -c "program <owned-firmware.elf> verify exit"
```

This requests initialization, reset/halt, flash write with affected erase operations,
verification and server exit. It deliberately omits `reset` from the `program` options:
adding it requests `reset run`. Shutdown alone is not a guarantee of a nonintrusive
operation; retain the observed final CPU state. Raw binary programming additionally
requires its approved load address; ELF/HEX uses image addresses. Do not invent a
universal flash address.

Only after successful verification and a separate run authorization:

```text
openocd -f <owned-session.cfg> -c "init; reset run; shutdown"
```

The reset behavior depends on the selected target/board scripts. Application success
needs a bounded scenario with expected observations over an implemented interface;
OpenOCD exit zero or flash comparison does not establish sensor behavior.

## Debug-server lifecycle and failures

For debugging, run an explicitly owned server with local-only access and a finite
session deadline. Load matching ELF symbols in GDB. Attaching, reset/halt, breakpoints
and stepping affect timing; GDB `load` writes firmware and is not merely symbol loading.
Avoid exposing GDB/Tcl/telnet publicly. Route server diagnostics to retained logs,
not an MCP server's protocol stdout. Shut down only the owned process and release
probe ownership after recording the target's final state.

- Adapter not found/busy: check serial, compiled driver, USB permissions and competing
  processes. Do not silently switch adapter.
- Initialization/IDCODE failure: stop and correct exact target/transport/wiring/power;
  do not disable identity checks.
- Timeout/reset or unstable link: inspect the board reset strategy and justified speed;
  no unbounded retries or speculative reset modes.
- Flash geometry/protection/verify failure: stop, retain the failing address/diagnostic
  and mark unverified/partial state. Do not automatically erase all, unlock, alter
  option bytes/protection or recover; destructive operations need separate authorization.

Use argument vectors and validated paths. Even `-c` Tcl must come from fixed reviewed
recipes, not concatenated untrusted input. Bound each subprocess, reap it on timeout
and retain partial logs. Record tool/config/probe versions, board/serial binding,
artifact hashes/ranges, exact arguments, exit/timeout state and separate build,
program/verify and physical-run results. [Simulation evidence](qemu.md) stays distinct.

## Primary references

- [OpenOCD adapter configuration and serial selection](https://openocd.org/doc/html/Debug-Adapter-Configuration.html).
- [Configuration stages and server ports](https://openocd.org/doc/html/Server-Configuration.html).
- [Flash programming sequence and optional verify/reset/exit](https://openocd.org/doc/html/Flash-Programming.html).
  Online documentation may track a newer build; retain the manual corresponding to
  the actual executable.
