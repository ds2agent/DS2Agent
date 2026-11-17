# NUCLEO-F767ZI: physical board binding

Use this profile to select a physical F767ZI project and document its actual connections.
It is not a firmware implementation, F7 HAL adapter, ready-to-flash target or QEMU
machine declaration.

## Sourced identity, defaults and limits

| Item | Baseline for this order code |
|---|---|
| Board / PCB family | **NUCLEO-F767ZI / MB1137**, STM32 Nucleo-144 |
| MCU / CPU | **STM32F767ZI**, LQFP144, Arm Cortex-M7 with FPU/cache |
| User LEDs | **LD1 green PB0**, **LD2 blue PB7**, **LD3 red PB14** in the standard BSP configuration |
| User/reset buttons | **B1 PC13** in the default configuration; separate NRST reset button |
| Expansion | **ST Zio** (including ARDUINO Uno V3-compatible positions) and ST morpho connectors |
| Debug | Embedded **ST-LINK/V2-1**, SWD; virtual COM is a separate serial function |
| Power | USB 5 V through the documented board power path; target normally **3.3 V**; external VIN **7–12 V**, E5V 5 V or regulated 3.3 V input only as configured in the manual |

References: [UM1974, STM32 Nucleo-144 boards (MB1137), Rev 11](https://www.st.com/resource/en/user_manual/um1974-stm32-nucleo144-boards-mb1137-stmicroelectronics.pdf),
[NUCLEO-F767ZI product/resources](https://www.st.com/en/evaluation-tools/nucleo-f767zi.html),
[STM32F767ZI specifications](https://www.st.com/en/microcontrollers-microprocessors/stm32f767zi.html),
and [official F7 Nucleo-144 BSP header](https://github.com/STMicroelectronics/stm32f7xx-nucleo-144-bsp/blob/main/stm32f7xx_nucleo_144.h).
UM1974 documents routing alternatives: LD1 can be routed to **PA5** instead of PB0, and
B1 to **PA0** instead of PC13 through solder-bridge configuration. Therefore the BSP
defaults are not proof of the fitted wiring; LED loading can conflict with SPI clock use.

**Revision boundary:** no particular PCB revision or assembly configuration is established
here. Record the fitted MCU's complete marking, MB1137 revision, actual solder bridges,
jumpers, oscillators and modifications, and obtain that revision's schematic from the
product resources. UM1974 covers multiple order codes; their optional peripherals,
populations and alternate functions are not automatically F767ZI capabilities. Do not
copy a newer Nucleo-144 board's STLINK, connectors or pin map, and do not invent a BOOT0
jumper from the word “Nucleo.”

## Bind the actual project

Before generating code, record:

1. **Every external signal:** connector/contact, schematic net, MCU pin, peripheral
   instance and F767 AF, direction, pull/idle state and device contact. Check ST Zio versus
   morpho numbering/orientation and solder-bridge routing. Audit onboard LED, Ethernet,
   USB, debug, virtual-COM and oscillator use against the actual schematic; headers are
   not a promise of unoccupied GPIO.
2. **Electrical topology:** actual board/device supply domains, ground, bus pull-up rail,
   level shifting and loading. VIN and E5V are board supply inputs, not MCU I/O levels.
   Use the MCU datasheet's normal operating conditions and pin-specific tolerance rules;
   absolute maximum ratings do not define a usable working voltage. Follow UM1974's
   source-selection/sequencing instructions, current budget and regulator thermal limits;
   do not tie competing USB/external sources together.
3. **Bus binding:** initialized handle, peripheral/kernel clock, AF pins, bus mode/rate,
   finite deadlines, and each device's unshifted I2C address or SPI CS pin/polarity.
   Resolve address/CS conflicts and shared resets/IRQs only from a supplied topology.
4. **Debug binding:** probe serial/firmware, board ID, actual target voltage/reference,
   SWD/reset wiring, selected adapter and reset/connect strategy. External-target use of
   the embedded probe requires UM1974's isolation/wiring configuration; do not assume it
   supplies target power or select an arbitrary attached probe.

## Toolchain and firmware boundary

The appropriate vendor family is [STM32CubeF7](https://github.com/STMicroelectronics/STM32CubeF7),
not CubeF1 or CubeG0. Its
[component inventory](https://github.com/STMicroelectronics/STM32CubeF7/blob/master/.gitmodules)
identifies F7 HAL, CMSIS device support and `STM32F7xx_Nucleo_144` BSP.
Pin the actual release/commits/hashes. Use STM32F767xx startup/vector/system support and
a linker script respecting the fitted F767ZI's actual Flash and RAM-bank layout.
Record compiler version, Cortex-M7/Thumb flags, selected FPU and float ABI consistently
across objects/libraries, vector placement, linker script and generated configuration.
F103/G071 startup, interrupt handlers, memory maps and HAL handles cannot be reused as
binary-compatible substitutes.

Supply F7-specific HAL configuration, clock/power setup, GPIO/AF/MSP code, IRQ/DMA
handlers and a working time base before binding portable driver callbacks. When DMA is
used, document buffer placement, DMA-accessible memory and cache-coherency ownership;
a cache-enabled Cortex-M7 needs an explicit policy, not an F1-style buffer assumption.
Read the selected CubeF7 examples and MCU reference manual for the actual peripheral.
The existing [F103 HAL](../libraries/f103_hal.md) and [G071 HAL](../libraries/g071_hal.md)
guides describe **different families**. There is no F767 HAL adapter implementation or
validated F767 firmware support implied by this profile; an F7-specific binding must be
supplied and verified for a requested target.

See [GCC](../tools/gcc.md), [ST-LINK](../tools/stlink.md) and
[STM32CubeProgrammer](../tools/stm32cubeprogrammer.md) for tool boundaries. Builds,
execution and programming need explicit authorization; destructive erase/unlock/option-byte
recovery requires separate informed permission.

Host MCP code cannot invoke target HAL merely because the board exposes ST-LINK, USB or
Ethernet. An implemented host-to-MCU bridge needs an identified firmware image, protocol
version, framing/routing, endpoint/probe identity, timeouts and error semantics. A virtual
COM port plus `pyserial` is only a UART transport, not an implicit sensor-bus bridge.
Do not infer such firmware from the board's connectors; see [UART](../interfaces/uart.md).

## Shared resources and evidence lifecycle

For two devices retain separate models, addresses/CS and calibration, but serialize shared
bus/HAL handles through whole transactions, GPIO ownership, probe access and shared firmware
files. Board reset, flash or power changes affect both devices and require a board-wide
reservation. Single-MCP namespacing in [aggregation](../../aggregation.md) does not
provide electrical isolation or automatically arbitrate these resources.

Hardware records bind
`{device_id, board_id, driver_sha256, hal_sha256, plan_sha256}`, model/calibration revisions,
actual PCB/wiring revision, firmware/build identity, probe serial/firmware, timestamp,
transcripts and instrument/reference identity. `hal_sha256` identifies the effective
vendor configuration plus board/MSP/clock/transport/time-base glue and declared build inputs,
not just a package label. Apply the [feedback contract](../../datasheet2mcp/references/feedback.md).
Refine before and after integration updates the **same canonical per-device records**;
effective-HAL, driver, board or plan changes require affected evidence/calibration to be
revalidated. Preserve historical bindings; a shared-firmware change can affect both devices.

Source/model/native/QEMU/hardware are separate
[evidence scopes](../../datasheet2mcp/references/runtime-verification.md).
Native fake HAL tests the actual portable driver, not F7 DMA/cache or real bus timing.
This physical profile certifies **neither QEMU support nor any hardware PASS**.
