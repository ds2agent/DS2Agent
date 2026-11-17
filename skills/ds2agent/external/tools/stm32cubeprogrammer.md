# STM32CubeProgrammer: authorized STM32 programming

ST's GUI/CLI programs supported STM32 devices through documented debug or bootloader
interfaces. This guide uses the ST-LINK/SWD path; serial/USB bootloader and other probe
paths have different prerequisites and are not interchangeable fallbacks.

Commands are **unexecuted templates**, based on the official 2.23.0 command reference.
Use the manual/help for the installed version; record executable path, version, probe
firmware and relevant options. Never install/update tools or probe firmware automatically.

## Bind the intended board before connecting

Require explicit physical-board authorization and `--allow-code-execution` or host
equivalent. Record exact board/revision, MCU order code, board-profile ID, ST-LINK serial,
transport, wiring/jumper configuration, power source and expected target voltage.
Check the [board profiles](../boards/) and vendor board manual; an on-board probe's
external-target routing is board-specific. Do not assume the probe powers the target.

Reserve the board and probe exclusively across all integrated devices. Close competing
CubeIDE, [st-util](stlink.md), [OpenOCD](openocd.md) and other debugger sessions. Discovery
is not permission to halt/reset or overwrite every attached target.

```text
STM32_Programmer_CLI -l
STM32_Programmer_CLI -c port=SWD sn=<owned-probe-serial>
```

Select by serial, not enumeration index/first detected probe; do not combine serial
and index selection. Check the connection report's device ID, memory size and voltage
against the exact target. A family ID alone need not distinguish package/order code.
Treat connection as potentially intrusive; even a diagnostic attach belongs to the
authorized session.

## Keep build, write/verify and run distinct

1. Build using [GCC/target project inputs](gcc.md). Bind the reviewed ELF/HEX or binary
   hash, allowed memory ranges and linker map to this board. Keep bootloader,
   calibration and user-data regions outside the approved write range.
2. Program and verify only the approved artifact. ELF/HEX carries addresses; raw binary
   requires the approved destination address. Normal programming can erase affected
   flash sectors, so assess sector overlap with retained data first.

   ```text
   STM32_Programmer_CLI -c port=SWD sn=<owned-probe-serial> -w <owned-firmware.elf> -v
   STM32_Programmer_CLI -c port=SWD sn=<owned-probe-serial> -w <owned-firmware.bin> <approved-start-address> -v
   ```

   These are alternative image formats, not two writes to perform. In this command
   family verification follows the write; preserve the actual verification result.
3. Reset/start only as a separate authorized action, after verification:

   ```text
   STM32_Programmer_CLI -c port=SWD sn=<owned-probe-serial> -rst
   ```

   This requests a system reset; firmware execution depends on the target's boot
   configuration. It does not prove application or sensor behavior. Capture a bounded
   UART/other application scenario with independently specified expected observations.

For an authorized readback of known flash, the documented operation is:

```text
STM32_Programmer_CLI -c port=SWD sn=<owned-probe-serial> -u <approved-start-address> <byte-count> <readback.bin>
```

`-d`/download means writing to the device, not reading flash. Never probe arbitrary
MMIO with bulk reads: reads can have side effects. Store only authorized readback data.

## Stop conditions and evidence

- No probe/USB access: check ownership, permissions/driver and USB path; do not auto-update.
- No target/voltage or unstable SWD: check supply, ground, routing and reset state before
  a bounded retry. Frequency/reset-mode changes need a documented board reason.
- Unexpected identity, memory map or image range: stop before writing.
- Protection/locked flash or verify mismatch: preserve diagnostics; do not mass erase,
  change option bytes/RDP, unlock or attempt recovery. These need separate informed
  authorization and a device-specific plan; lowering protection can destroy data.
- Timeout/interruption during programming: mark state unknown/partial, not verified.
  Do not immediately run an incompletely verified image.

Use validated argument vectors, finite per-stage deadlines and owned-process cleanup.
Retain authorization scope, board/probe binding, image/hash/map, tool/probe versions,
exact arguments, logs, exit/timeout status, write/verify results, observed reset/run
state and remaining limitations. Keep build, flash verification and physical scenario
results separate; simulation is not hardware evidence.

## Primary references

- [ST STM32CubeProgrammer 2.23.0 MCU command lines](https://dev.st.com/stm32cube-docs/prog/2.23.0/en/docs/markup/CubeProg_Command_Lines.html).
- [ST ST-LINK connection settings](https://dev.st.com/stm32cube-docs/prog/2.23.0/en/docs/markup/STLink_Connection_page.html).
- [UM2237 software description](https://www.st.com/resource/en/user_manual/um2237-stm32cubeprogrammer-software-description-stmicroelectronics.pdf)
  (obtain the revision matching the installed release).
