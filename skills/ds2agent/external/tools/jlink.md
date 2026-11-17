# SEGGER J-Link: explicit probe and device binding

Use J-Link Commander for bounded connection/programming tasks and a separately managed
GDB server for interactive debugging. Probe hardware, software pack, licensing and
exact target support must be appropriate for the selected MCU; a generic Cortex-M
device choice is not enough for flash programming.

Commands below are **unexecuted templates** using the current SEGGER Commander reference.
Record the installed Software and Documentation Pack version and use its own command
help. The documented `-USB` serial/nickname selector is available from V7.92d; do not
assume the same options in older packages. On Windows the executable is normally
`JLink.exe`; other platforms use `JLinkExe`.

## Preflight and exclusive ownership

Require physical-board authorization plus `--allow-code-execution` or host equivalent.
Bind board/revision, exact MCU order code, [board profile](../boards/), probe serial,
interface, approved debug speed and reset strategy. Check the actual supported device
name using that pack's device list (`ExpDevList` exports the DLL's names). Do not infer
support from a similar device name.

Confirm SWD/JTAG wiring, ground, target voltage/reference and power source from the
probe and board manuals; sensing VTref is not permission to supply power. Do not enable
probe target power, force VTref, alter firmware/licenses or reconfigure an on-board
ST-LINK automatically. Reserve the whole board/probe across all integrated devices,
and close other IDEs, flash tools and debug servers.

## Separate build, programming and physical execution

First build and review the target ELF, memory map and hash with [GCC](gcc.md).
Check all programmed sections and affected erase sectors against retained bootloader,
calibration/user data and the approved write range.

For a pack supporting these options, an automated session template is:

```text
JLinkExe -USB <owned-probe-serial> -Device <exact-segger-device-name> -If SWD -Speed <approved-kHz> -AutoConnect 1 -NoGui 1 -ExitOnError 1 -CommandFile <owned-program.jlink>
```

SWD is a selected connection here, not a universal choice. Set a finite host process
deadline even in no-GUI mode. The command file is a reviewed owned artifact, not
caller-supplied Commander commands. Example programming-stage contents:

```text
ExitOnError 1
h
LoadFile "<owned-firmware.elf>" 0 noreset
h
exit
```

The documented `LoadFile` syntax requires an address field when specifying reset
behavior; `0` here is **ignored for ELF**, not a chosen MCU flash address. `noreset`
avoids its default reset request, but connection/halt/programming are still intrusive.
For a raw `.bin`, the address is meaningful and must come from the approved build.
`LoadFile` performs verification by default in the documented version; preserve the
download/verify diagnostics and final halt state, not merely exit status.

For a separately authorized comparison of a known raw image:

```text
VerifyBin "<owned-firmware.bin>" <approved-flash-address>
```

Reset (`r`) and continue (`g`) are separate run-stage decisions; do not append them to
the flash script by habit. Define a finite application observation through implemented
UART/RTT/other instrumentation. RTT needs matching firmware support; a connected probe
or a loaded ELF alone does not produce application evidence.

For GDB debugging use the installed pack's GDB-server documentation, explicit probe
serial/device selection and a restricted local endpoint. A local symbol load is
different from a target download. Bound the session, serialize access and record
halt/breakpoint/reset/continue actions and final state before releasing ownership.

## Failure handling and evidence

No probe or target voltage: inspect ownership, cabling and power before retrying.
Unknown device: stop and resolve exact pack/device support. Connection/reset errors:
review wiring and device-specific reset requirements before an authorized speed or
strategy change. Flash/verify failure or timeout: retain logs and mark partial/unknown
target state; do not run it as verified.

Never use routine erase-all, unlock, protection changes or recovery as an automatic
connection fix. These can destroy data and require separate informed authorization.
No automatic installation, pack/probe upgrade or fallback to another probe.

Retain authorization, board/probe identity, device selection, pack/probe versions,
owned script/hash, ELF/map/hash, write ranges, argument vector, stdout/stderr/logs,
exit/timeout status and explicit program/verify/run outcomes. Keep physical findings
separate from [model/native/QEMU results](qemu.md).

## Primary reference

- [SEGGER J-Link Commander](https://kb.segger.com/J-Link_Commander): commands, current
  CLI options, `LoadFile` verification/reset semantics and versioned probe selection.
  Its command list explicitly applies to the latest version; use the installed pack
  documentation for a pinned older release.
