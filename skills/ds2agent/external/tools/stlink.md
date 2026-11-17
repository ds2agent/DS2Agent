# ST-LINK probe and the open-source stlink tools

ST-LINK is probe hardware/firmware; `st-info`, `st-flash` and `st-util` here are the
independent **stlink-org** toolset, not aliases for [STM32CubeProgrammer](stm32cubeprogrammer.md).
Probe-generation support does not establish support for every MCU in every release.
Use the installed tool version's supported-device list, chip database and help.

All commands are **unexecuted templates**. No connected board, supported project target
or working USB driver is asserted. Never auto-install tools or update probe firmware.

## Select and own the physical connection

Before any probe access require physical-board authorization and
`--allow-code-execution` or host equivalent. Record exact MCU/board/revision and
[board profile](../boards/), probe serial/generation/firmware, SWD routing, reset
connection, supply and voltage-reference arrangement. Nucleo on-board probe routing
and standalone use depend on that board's manual/jumpers; do not assume all boards
can be repurposed identically.

Serialize board/probe access across all devices; stop other IDE/programmer/debug
servers before acquisition. Discovery is diagnostic, not permission to modify targets:

```text
st-info --version
st-info --probe
```

Match reported serial, chip ID, flash/page/SRAM sizes and description to the intended
target. A chip-family description is not sufficient to infer the exact package/order
code. Refuse ambiguous or unexpected identities rather than selecting the first probe.

## Program only an approved image range

Build separately with the [target toolchain](gcc.md); retain its ELF/link map and
derive the raw binary's base address and byte range from that same build/target record.
Do not pass an ELF to the binary workflow below. Check flash-page overlap with any
bootloader, calibration or retained data; programming may erase affected pages.

```text
st-flash --serial <owned-probe-serial> write <owned-firmware.bin> <approved-flash-address>
st-flash --serial <owned-probe-serial> read <readback.bin> <approved-flash-address> <hex-byte-count>
```

The second operation is optional authorized readback of the intended flash range.
Compare readback bytes with exactly the programmed image range and retain the result.
Also preserve any built-in verification diagnostics; do not label a reported mismatch
as success merely because a file exists. Avoid arbitrary peripheral-memory reads,
which can have side effects.

Keep flashing and reset/run separate: `--reset` requests resets before and after
flashing, so it is intentionally absent here. Tool internals may still halt/reset the
MCU as part of programming; record actual final state rather than promising a passive
operation. Use the installed release's documented reset/debug controls only when
separately authorized. Readback equality proves bytes in a range, not application behavior.

## Debug sessions are also hardware operations

`st-util` serves GDB, typically on port 4242; its serial-selection support is documented
but exact syntax and network binding must be checked in the installed release's help.
Launch only with explicit probe selection and a local-only/restricted endpoint; do
not rely on default network exposure. `-n`/`--no-reset` requests no reset on connection,
not a guarantee of nonintrusive debugging. Keep a finite session deadline and terminate
only the server you own.

Load symbols from the matching ELF in an Arm-capable GDB. Attaching, halt/step,
breakpoints, reset and continue can alter timing/state. GDB `load` writes the target;
it is not needed just to load local symbols. Request a specific bounded observation
and detach/release ownership with the final CPU state recorded.

## Failures and retained evidence

- USB/probe failure: check process ownership, permissions/driver and cabling.
- Wrong/unknown chip: stop; consult that release's support database rather than forcing
  a flash size or treating a similar family as equivalent.
- No voltage/target or SWD errors: check board power/routing before changing clocks or
  reset strategy. Such changes must come from a board-specific plan.
- Verify mismatch or interrupted write: failed/partial state; no automatic run.
- Protection error: stop. No routine erase-all, option-byte changes, unlock or recovery;
  destructive actions need separate informed authorization.

Use validated argument vectors and per-command deadlines. Retain tool/probe versions,
board/serial binding, approved address/range, artifact hashes, exact arguments, logs,
exit/timeout status, byte-verification evidence and any independent physical observations.
Do not merge these with [native/QEMU evidence](qemu.md).

## Primary references

- [stlink project and support lists](https://github.com/stlink-org/stlink).
- [Project st-flash manual](https://github.com/stlink-org/stlink/blob/testing/doc/man/st-flash.md):
  binary read/write, address/size and serial selection.
- [Project st-info manual](https://github.com/stlink-org/stlink/blob/testing/doc/man/st-info.md).
- [Project st-util manual](https://github.com/stlink-org/stlink/blob/testing/doc/man/st-util.md).
  The linked development-branch manuals are discovery references; pin the actual release
  used in evidence.
