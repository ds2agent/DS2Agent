# GCC: native driver harness and target firmware

Use a host compiler to verify portable exported C at its HAL boundary; use an Arm
cross-compiler to build MCU firmware. These are separate artifacts and evidence levels.
All commands below are **unexecuted templates**; filenames and target choices are
project inputs, not supplied working fixtures.

## Select and record the toolchain

- Native: `gcc` with `-std=c11 -Wall -Wextra`; Clang is an alternative, but record it as
  Clang rather than GCC evidence. Keep generated driver/harness code warning-clean;
  `-Wall` does not mean every possible warning or prove correctness.
- MCU: `arm-none-eabi-gcc` from an explicitly provisioned toolchain. Resolve the exact
  MCU from the selected [board profile](../boards/), not just a Cortex-M family.
  Set `-mcpu`, `-mthumb`, and, only when applicable, `-mfpu`/`-mfloat-abi` from that
  target's vendor project and installed compiler support. All objects and libraries
  must use compatible floating-point calling conventions.
- Record executable path, full version, target triple, host OS, SDK/HAL/CMSIS revision
  and resolved options in `.pipeline/environment.json` and build evidence. Compiler
  defaults and warning sets change between releases; consult the matching GCC manual.
  Do not auto-install a compiler, SDK or library.

## Native: compile the actual exported driver

Keep exported `.c`/`.h` unchanged. Implement its existing HAL interface in a separate
fake-HAL file; use the real public header, not duplicated declarations. Keep the
scenario entry point, assertions and stateful device model separate from the driver.

```text
gcc -std=c11 -Wall -Wextra -g -O0 -Iexport/include -Iharness export/driver.c harness/fake_hal.c harness/device_model.c harness/scenario.c -o build/native-scenario
```

This illustrative layout is not a repository command. On Windows use the host's
executable suffix as needed. Add only actual dependencies; if the driver needs a math
library, resolve the host's requirements and put libraries after referring objects.
Run the resulting executable only as a separate, authorized, deadline-bounded step.
Do not define `NDEBUG` when the harness relies on C `assert`.

Scenarios should check initialization/reset, configuration transactions, read/reply
layout, byte order, signed conversion, documented timing and relevant bus failures.
The fake HAL should log transactions and advance deterministic virtual time, and
reject unmodeled commands. Bind expected values to cited datasheet vectors or an
independent derivation: reproducing the driver's formula in the model is not an oracle.
Model-only Python checks and a second handwritten implementation do not verify exported C.

## Target: complete firmware, not just `-mcpu`

Use the selected vendor project's build recipe rather than guessing a universal command.
In addition to driver and real MCU HAL sources it needs:

1. Exact device headers, preprocessor device selection and HAL configuration.
2. Device startup/vector table and reset handler; correct initial stack, interrupt
   names and runtime initialization of `.data`/`.bss` before application use.
3. A linker script for the actual flash/RAM layout, bootloader reservation, entry/vector
   location, alignment and stack/heap policy. Pass the owned script with `-T`.
   If section garbage collection is enabled, retain required vector/startup sections.
4. System/clock initialization and interrupt/time-base configuration matching the
   board. Floating-point instructions also require the proper runtime FPU setup.
5. Deliberate C-library/syscall policy. `-ffreestanding` does not supply startup or a
   runtime. `-nostdlib` removes startup and libraries, including compiler helpers;
   GCC may still need `libgcc` and memory routines. Do not fix link failures with fake
   successful I/O syscalls or silently enable semihosting.

Retain ELF with symbols, link map and memory-usage evidence. Review section addresses,
reserved regions and overflow diagnostics before producing any raw binary. A raw
binary has no destination address: bind its address/range to that same target record.
Building does not authorize flashing; continue via a selected
[programmer](stm32cubeprogrammer.md) or [debug server](openocd.md) only when requested.

## Interpret and retain evidence

Separate syntax/object compilation, successful link, native assertions, optional
[QEMU execution](qemu.md), flash verification and physical behavior. Undefined symbols
usually mean missing sources/runtime or ABI mismatch; memory overflow requires a real
layout/size correction, not disabling the diagnostic. A native pass cannot validate MCU
clocks, interrupt routing, electrical timing or physical calibration.

Use argument vectors with validated paths, bounded build/run deadlines and explicit
`--allow-code-execution` or host-equivalent approval. Retain arguments, stdout/stderr,
exit/timeout status, source/HAL/model/harness hashes, executable hash and actual
expected/observed checks under the [simulation evidence contract](qemu.md).
An exit-zero compile is build evidence; it is not an executed scenario.

## Primary references

- [GCC warning options](https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html).
- [GCC Arm options and ABI rules](https://gcc.gnu.org/onlinedocs/gcc/ARM-Options.html).
- [GCC linking and omitted-runtime implications](https://gcc.gnu.org/onlinedocs/gcc/Link-Options.html).
- [GNU ld linker scripts](https://sourceware.org/binutils/docs/ld/Scripts.html).
- [Arm CMSIS-Core Cortex-M startup requirements](https://arm-software.github.io/CMSIS_6/latest/Core/startup_c_pg.html).
