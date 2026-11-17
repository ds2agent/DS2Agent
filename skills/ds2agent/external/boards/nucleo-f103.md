# NUCLEO-F103RB: physical board binding

Use this profile when assembling an STM32F103RB target project or planning an authorized
physical-board run. It is not a ready-made wiring diagram, tested firmware target, or QEMU
machine declaration.

## Identity and sourced defaults

| Item | Baseline; verify the fitted board |
|---|---|
| Order code / PCB family | **NUCLEO-F103RB / MB1136**; not a generic “F103” board |
| MCU / CPU | **STM32F103RBT6**, LQFP64, Arm Cortex-M3 |
| User I/O | Green **LD2 on PA5**; user button **B1 on PC13**; separate reset button drives NRST |
| Expansion | ARDUINO Uno V3-compatible headers and ST morpho headers |
| Debug | Embedded **ST-LINK/V2-1**, SWD; external-target use requires the manual's isolation/wiring configuration |
| Supply | Normally USB 5 V into the board's power path and a regulated **3.3 V target domain**; external VIN nominally **7–12 V**, subject to the manual's current/thermal limits |

These defaults come from [UM1724, STM32 Nucleo-64 boards (MB1136), Rev 17](https://www.st.com/resource/en/user_manual/um1724-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf),
the [board product page](https://www.st.com/en/evaluation-tools/nucleo-f103rb.html),
and ST's [F1 Nucleo BSP header](https://github.com/STMicroelectronics/stm32f1xx-nucleo-bsp/blob/main/stm32f1xx_nucleo.h).
The BSP confirms PA5/PC13, but also contains optional shield mappings: those are not
evidence that a shield or external device is fitted.

**Revision limit:** no actual PCB revision or jumper state has been supplied here.
Record the board silkscreen/assembly revision and fitted MCU marking; select its matching
schematic from ST's product resources. ST's
[MB1136 default C03 schematic](https://www.st.com/resource/en/schematic_pack/mb1136-default-c03_schematic.pdf)
is a revision-specific reference, not proof that the connected board is C03 or that every
variant/component is populated. Record solder bridges, jumpers, oscillator population and
any modifications. Do not assume a universal BOOT0 jumper; use that revision's boot-selection
wiring and MCU boot configuration.

## Default Arduino-header interfaces (verify against the fitted board)

| Bus | Pins | Note |
|---|---|---|
| I2C1 | PB8 (SCL) / PB9 (SDA) | AFIO remap required; default I2C1 is PB6/PB7 |
| SPI1 | PA5 (SCK) / PA6 (MISO) / PA7 (MOSI) | default pins, no remap; PA5 is also LD2 |

SPI1's Arduino-header chip-select is **D10 = PB6** (software CS; the F1 SPI1 hardware NSS is
PA4). Keep CS asserted across the whole frame. These are the BSP/Arduino defaults, not proof
of the fitted wiring — still record the actual connector/pin map for the selected revision.

## TIM2 square-wave output (general-purpose timer)

TIM2 is a 16-bit general-purpose timer on APB1 with four capture/compare channels. Its kernel
clock is 2 × PCLK1 = **72 MHz** when SYSCLK = 72 MHz and the APB1 prescaler is 2 (RM0008 clock
tree). Square-wave (50 % duty) output uses output-compare **toggle** mode for exact symmetry,
or **PWM** with an odd auto-reload period.

F1 has no GPIO AF-number field; channel pins are chosen by the AFIO remap (`AFIO_MAPR`
`TIM2_REMAP[1:0]`, RM0008):

| Remap | CH1/ETR | CH2 | CH3 | CH4 |
|---|---|---|---|---|
| 00 — no remap (default) | PA0 | PA1 | PA2 | PA3 |
| 01 — partial remap 1 | PA15 | PB3 | PA2 | PA3 |
| 10 — partial remap 2 | PA0 | PA1 | PB10 | PB11 |
| 11 — full remap | PA15 | PB3 | PB10 | PB11 |

Board-fit notes:

- PA0/PA1 (default CH1/CH2, Arduino A0/A1) are free in this profile for TIM2 output. PA0 also
  doubles as WKUP.
- PA2/PA3 (default CH3/CH4, Arduino A2/A3) are the ST-LINK Virtual COM port USART2 lines on
  this board (UM1724). Driving them from TIM2 takes VCP serial off the same pins; keep VCP
  live with CH1/CH2 only, or move CH3/CH4 to PB10/PB11 via partial remap 2 / full remap.
- Any remap requires the AFIO clock (RCC APB2 `AFIOEN`) enabled before writing `AFIO_MAPR`;
  channel GPIO must be alternate-function push-pull (`GPIO_Mode_AF_PP`), not the reset input.

Frequency (16-bit `PSC`/`ARR`, timer clock `f_TIM2`):

- PWM mode 1: `f_out = f_TIM2 / ((PSC+1) × (ARR+1))`, duty = `CCR / (ARR+1)`; exact 50 %
  needs an odd `ARR` with `CCR = (ARR+1)/2` — e.g. `PSC=71, ARR=999, CCR=500` → 1 kHz.
- Toggle mode (`TIM_OCMODE_TOGGLE`): toggles once per counter period, so
  `f_out = f_TIM2 / (2 × (PSC+1) × (ARR+1))` with exactly 50 % duty — e.g. `PSC=71, ARR=499`
  → 1 kHz. Ceiling is 36 MHz (`PSC=0, ARR=0`), bounded in practice by GPIO output speed/load.

Configure `TIM_OC_InitTypeDef`/`HAL_TIM_OC_*` or `HAL_TIM_PWM_*` per
[STM32F1 HAL](../libraries/f103_hal.md); the timer handle is serialized board-level glue,
never portable-driver code.

## Complete the project binding before generating glue

Keep this board binding alongside each owning device's canonical records; references to one
shared board must resolve to the same board/resource identity.

1. **Pin map:** for every signal, record connector designator/contact, schematic net,
   MCU port/pin, peripheral instance, F1 alternate-function/remap choice, direction,
   idle level and external-device contact. Confirm header orientation from the manual,
   not a photograph or another Nucleo's pin map. PA5 also serves the BSP's SPI1 SCK
   mapping: LED use and bus use are not independent resources.
2. **Electrical topology:** record actual target and device rails, grounds, pull-up rail,
   level translation, bus pull-ups and loading. Header “5V”/VIN are supply nets, not GPIO
   logic levels. A pin's documented 5 V tolerance is conditional and does not make analog
   inputs or all pins 5 V-compatible. Use the
   [STM32F103RB operating/electrical specifications](https://www.st.com/en/microcontrollers-microprocessors/stm32f103rb.html);
   absolute maximum ratings are never working-voltage instructions.
3. **Bus binding:** name the initialized HAL handle/peripheral, actual pins/remaps,
   clock/mode and finite operation budget. Store an I2C device's unshifted 7-bit address,
   or SPI CS port/pin/polarity, per device. Resolve address clashes, CS conflicts,
   shared reset/IRQ lines and aggregate pull-ups only against the supplied topology.
4. **Probe/power binding:** record probe serial/firmware, SWD wiring and reset strategy,
   target reference voltage, power-source selection, and board identity. Do not select
   “the first probe.” Avoid driving a target from competing USB/external sources; apply
   the manual's jumper and power-sequencing instructions. Regulator heating and USB
   enumeration/current budgets constrain external loads.

## Target project and host boundary

Use a pinned [STM32CubeF1](https://github.com/STMicroelectronics/STM32CubeF1) release,
its STM32F103xB CMSIS device/startup and system-clock implementation, and a linker script
for the **fitted MCU's Flash/RAM**, not an F103C8 or F1 high-density example. Record the
Arm toolchain version and Cortex-M3/Thumb flags (no hardware-FPU ABI), linker script,
vector table, interrupt handlers, HAL configuration and generated project configuration.
The Cube [component inventory](https://github.com/STMicroelectronics/STM32CubeF1/blob/master/.gitmodules)
identifies the F1 HAL, CMSIS and `STM32F1xx_Nucleo` BSP components; pin their actual
commits/hashes rather than tracking `master`/`main`.

Initialize HAL/time base, the verified clock tree, GPIO/remaps and selected peripherals;
implement MSP/IRQ glue and bind portable driver callbacks as described in
[STM32F1 HAL](../libraries/f103_hal.md). A BSP LED example does not supply a complete
sensor bus project. See [GCC](../tools/gcc.md) and [ST-LINK](../tools/stlink.md) for tool
selection; execution/flash requires explicit authorization, and destructive recovery is
not a routine setup step.

The host MCP process cannot call MCU HAL directly. ST-LINK debug and its virtual COM port
are not an I2C/SPI/1-Wire bridge. A host-to-target path needs identified, implemented bridge
firmware plus framing, firmware/protocol version, device/bus routing, error mapping and
finite host/MCU deadlines. Bind the correct serial endpoint to that firmware/probe instead
of treating `pyserial` as a bus adapter. See [UART](../interfaces/uart.md).

## Shared use, evidence and refinement

Two devices on this board need separate device models/addresses/CS and evidence records,
but one serialized owner for each shared HAL handle, bus transaction, pin, probe,
reset/power action and firmware image. Hold the bus lock across complete combined I2C
transactions or SPI CS assertion through deassertion. Flash/reset affects every resident
device: schedule it board-wide, not only under a device-prefixed tool.

Follow [aggregation](../../aggregation.md) and the
[feedback binding contract](../../datasheet2mcp/references/feedback.md):
retain `{device_id, board_id, driver_sha256, hal_sha256, plan_sha256}`, model/calibration
revisions, firmware/build identity, probe identity, wiring revision, operation transcript,
timestamp and instrument/reference identity. `board_id` includes the actual PCB/configuration,
not merely “NUCLEO-F103RB.” Effective HAL identity covers the selected vendor sources and
configuration plus MSP, clock/pin, transport/time-base glue and their declared build inputs.

Refine before or after single-MCP integration uses the **same per-device canonical records**.
Changing effective HAL, pins/clock, board, driver or plan requires affected evidence and
calibration to be revalidated; archive old bindings, never silently relabel them. Unrelated
devices' facts stay isolated, while shared-firmware changes may invalidate both devices'
hardware evidence. Source review, model simulation, compiled portable C under fake HAL,
optional exact QEMU pairing and real hardware runs remain distinct
[verification scopes](../../datasheet2mcp/references/runtime-verification.md).
This physical profile certifies **no QEMU support and no hardware PASS**.
