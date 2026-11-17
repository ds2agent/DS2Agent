# STM32F1 HAL: F103RB transport binding

Use this guide to bind an exported portable C device driver to **STM32CubeF1 HAL**
(`stm32f1xx_hal_*`) in a real F103RB project. It does not supply the project, wire a bus,
or make an F1 driver compatible with G0/F7. The old Standard Peripheral Library
(`stm32f10x_*`) is a different API; do not mix its initialization or handle assumptions
into HAL glue.

## Pin the vendor and project inputs

Start from an explicitly selected [STM32CubeF1](https://github.com/STMicroelectronics/STM32CubeF1)
release; its [component manifest](https://github.com/STMicroelectronics/STM32CubeF1/blob/master/.gitmodules)
identifies HAL, CMSIS device and BSP dependencies. Record release/tag, exact component
commits, actual file hashes and licenses. The moving upstream links below are API
references, not a reproducible version selection.

Inventory every selected vendor source/header and configuration in the BSP manifest:
`stm32f1xx_hal.h`, project `stm32f1xx_hal_conf.h`, enabled module sources/headers
(`i2c`, `spi`, `uart`, `gpio`, `rcc`, plus required core/extension/DMA modules),
CMSIS core/device headers, system/startup/vector support, linker script, MSP/IRQ/tick
implementations, compiler definitions and flags. Select the **STM32F103xB** device
definition, Cortex-M3/Thumb compilation with a non-FPU ABI, and a linker script for the
fitted RB memory map. Pin the board BSP only if actually used; its optional
shield support is not project wiring. Keep vendor HAL sources unchanged and place
application adapters in project-owned files.

Use the [NUCLEO-F103RB profile](../boards/nucleo-f103.md) for PCB revision, actual
connector/pin map, power and probe binding. A generated `hi2c` name alone does not prove
which peripheral/pins or connected device it controls.

## Initialization is board glue, not portable driver logic

1. Bring up the selected startup/vector/system code, call `HAL_Init()` and establish a
   working HAL time base. Configure the verified oscillator/PLL/bus clocks and Flash
   latency for the actual project; do not infer the board clock from the CPU maximum.
2. Enable GPIO and peripheral clocks and configure actual F1 GPIO modes, pulls and
   **AFIO remaps**. F1 does not use G0/F7's generic GPIO AF-number field. Keep SWD
   available unless a separately authorized pin/debug plan explicitly changes it.
3. Implement `HAL_I2C_MspInit`, `HAL_SPI_MspInit` and/or `HAL_UART_MspInit` for the
   selected handles; supply NVIC/DMA setup and correct IRQ handlers when using those
   modes. For I2C use alternate-function open-drain and topology-appropriate external
   pull-ups. F1 `I2C_InitTypeDef` uses **`ClockSpeed` and `DutyCycle`**, not G0 `Timing`.
   **Interrupt completeness:** if any interrupt is used, enumerate every enabled
   interrupt and check each one in a single pass — peripheral interrupt enable, NVIC
   enable (`HAL_NVIC_EnableIRQ(<IRQn>)`), and the ISR wired in the vector table that
   calls `HAL_<PERIPH>_IRQHandler` (SysTick → `SysTick_Handler`/`HAL_IncTick`; USART2 RX
   → `USART2_IRQHandler`/`HAL_UART_IRQHandler` + re-arm `HAL_UART_Receive_IT`). Missing
   any one lands in the weak `Default_Handler` (hang) or silently drops the IRQ.
4. Set all required handle `Instance`/`Init` fields and check every HAL initialization
   result before binding the driver. Keep SPI CS inactive before enabling transfers.
   Surface initialization failure as a failure; an infinite `Error_Handler` loop is
   not a bounded MCP operation.

The official [I2C header](https://github.com/STMicroelectronics/stm32f1xx-hal-driver/blob/master/Inc/stm32f1xx_hal_i2c.h)
and [implementation/how-to](https://github.com/STMicroelectronics/stm32f1xx-hal-driver/blob/master/Src/stm32f1xx_hal_i2c.c)
define the required resources and peripheral-specific behavior. Consult the selected MCU's
errata as well as the pinned HAL release before choosing a recovery policy.

## Relevant blocking API shapes

These are current upstream shapes; use the **pinned header** as authority for qualifiers
and available features in an older Cube release. All functions below except GPIO/tick/delay
return `HAL_StatusTypeDef`.

```c
HAL_StatusTypeDef HAL_I2C_Master_Transmit(I2C_HandleTypeDef *h, uint16_t dev,
    uint8_t *data, uint16_t size, uint32_t timeout);
HAL_StatusTypeDef HAL_I2C_Master_Receive(I2C_HandleTypeDef *h, uint16_t dev,
    uint8_t *data, uint16_t size, uint32_t timeout);
HAL_StatusTypeDef HAL_I2C_Mem_Read(I2C_HandleTypeDef *h, uint16_t dev,
    uint16_t reg, uint16_t reg_size, uint8_t *data, uint16_t size, uint32_t timeout);
HAL_StatusTypeDef HAL_I2C_Mem_Write(I2C_HandleTypeDef *h, uint16_t dev,
    uint16_t reg, uint16_t reg_size, uint8_t *data, uint16_t size, uint32_t timeout);
HAL_StatusTypeDef HAL_SPI_TransmitReceive(SPI_HandleTypeDef *h, const uint8_t *tx,
    uint8_t *rx, uint16_t size, uint32_t timeout);
HAL_StatusTypeDef HAL_UART_Transmit(UART_HandleTypeDef *h, const uint8_t *data,
    uint16_t size, uint32_t timeout);
HAL_StatusTypeDef HAL_UART_Receive(UART_HandleTypeDef *h, uint8_t *data,
    uint16_t size, uint32_t timeout);
void HAL_GPIO_WritePin(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state);
GPIO_PinState HAL_GPIO_ReadPin(GPIO_TypeDef *port, uint16_t pin);
uint32_t HAL_GetTick(void);
void HAL_Delay(uint32_t milliseconds);
```

Additional verified declarations:
[SPI](https://github.com/STMicroelectronics/stm32f1xx-hal-driver/blob/master/Inc/stm32f1xx_hal_spi.h),
[UART](https://github.com/STMicroelectronics/stm32f1xx-hal-driver/blob/master/Inc/stm32f1xx_hal_uart.h),
[GPIO](https://github.com/STMicroelectronics/stm32f1xx-hal-driver/blob/master/Inc/stm32f1xx_hal_gpio.h),
[HAL core](https://github.com/STMicroelectronics/stm32f1xx-hal-driver/blob/master/Inc/stm32f1xx_hal.h).

- **I2C addressing:** the driver/model stores an unshifted 7-bit address; this HAL's
  `DevAddress` requires **`(uint16_t)(address7 << 1)`**. Shift once in the adapter;
  do not add the read bit manually, shift register addresses, or shift again in callers.
  Ten-bit addressing needs an explicitly different contract, not this conversion.
- **Register transfers:** `reg_size` is `I2C_MEMADD_SIZE_8BIT` or
  `I2C_MEMADD_SIZE_16BIT`, the width of the register-address phase, not payload width.
  Use `Mem_Read` only when its address-write/repeated-START/read transaction matches the
  device datasheet. A command stream, no-register device or different framing needs its
  actual transaction, not an invented register. Separate blocking transmit/receive calls
  introduce a STOP and are not a substitute for required repeated START.
- **SPI:** bind CPOL/CPHA, prescaler, bit order, data width and CS ownership explicitly.
  `Size` counts configured data units; it is not always bytes in 16-bit mode.
  Match the pinned HAL's buffer layout/alignment. Keep CS asserted across the full
  device frame and deassert on failure as well as success. Do not invent dummy-byte,
  register-read-bit or CS timing values. See [SPI](../interfaces/spi.md).
- **UART/GPIO:** UART framing/baud and expected response length come from the project
  and device protocol. GPIO pins are HAL masks (`GPIO_PIN_n`), not ordinal numbers.
  `HAL_GPIO_WritePin` is `void`, not an acknowledged physical measurement.
  HAL does not turn UART into I2C/SPI/1-Wire; see [UART](../interfaces/uart.md).

Keep device-specific command bits, dummy bytes, byte order, response length and timing in
the portable driver/protocol, not guessed from a HAL function name. See
[I2C](../interfaces/iic.md), [SPI](../interfaces/spi.md) and [UART](../interfaces/uart.md).

## TIM2 (timer peripheral)

TIM2 is a **16-bit** general-purpose timer on APB1 with four capture/compare channels
(TIM2–TIM5 are all 16-bit on F1; there is no 32-bit timer). At 72 MHz SYSCLK with APB1
prescaler 2, the timer kernel clock is 2 × PCLK1 = **72 MHz**; prescaler/period derive from
that clock, never a guessed constant.

Verified HAL API (pinned `stm32f1xx_hal_tim.h`):

```c
HAL_StatusTypeDef HAL_TIM_Base_Init(TIM_HandleTypeDef *htim);
HAL_StatusTypeDef HAL_TIM_IC_Init(TIM_HandleTypeDef *htim);
HAL_StatusTypeDef HAL_TIM_IC_ConfigChannel(TIM_HandleTypeDef *htim,
    const TIM_IC_InitTypeDef *sConfig, uint32_t Channel);
HAL_StatusTypeDef HAL_TIM_IC_Start(TIM_HandleTypeDef *htim, uint32_t Channel);
HAL_StatusTypeDef HAL_TIM_IC_Start_IT(TIM_HandleTypeDef *htim, uint32_t Channel);
uint32_t HAL_TIM_ReadCapturedValue(const TIM_HandleTypeDef *htim, uint32_t Channel);
void HAL_TIM_IC_CaptureCallback(TIM_HandleTypeDef *htim);
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim);
```

- `TIM_Base_InitTypeDef`: `Prescaler`, `CounterMode` (`TIM_COUNTERMODE_UP`), `Period`,
  `ClockDivision`, `RepetitionCounter`, `AutoReloadPreload`.
- `TIM_IC_InitTypeDef`: `ICPolarity` (`TIM_ICPOLARITY_RISING`/`FALLING`/`BOTHEDGE`),
  `ICSelection` (`TIM_ICSELECTION_DIRECTTI`), `ICPrescaler` (`TIM_ICPSC_DIV1`),
  `ICFilter` (0..15).

Pins (default mapping, no remap): PA0 = TIM2_CH1, PA1 = TIM2_CH2, PA2 = TIM2_CH3,
PA3 = TIM2_CH4. Configure `GPIO_MODE_AF_PP` + `GPIO_NOPULL`. F1 has no AF-number field:
CH1/CH2 are on PA0/PA1 by default; the full remap moves them to PA15/PB3. The timer samples
the AF input; software drives no push-pull level on these pins while the channel is active.

Tick resolution example (72 MHz kernel): `Prescaler = 71` → 72 MHz / (71+1) = 1 MHz = 1 µs
per tick. **The counter is 16-bit**, so `Period` maxes at 0xFFFF (65535 ticks ≈ 65 ms at
1 µs/tick); for longer intervals raise the prescaler, then
`period_us = (ccr_after - ccr_before) / tick_MHz` (wrap-safe).

Interrupt path: enable TIM2 (`__HAL_RCC_TIM2_CLK_ENABLE()`), configure NVIC `TIM2_IRQn`,
`HAL_TIM_IC_Start_IT(&htim2, TIM_CHANNEL_1)`, read the value in `HAL_TIM_IC_CaptureCallback`,
and handle wrap with `HAL_TIM_PeriodElapsedCallback`.

Build prerequisite: add `stm32f1xx_hal_tim.c` (and `_ex` when needed) to the firmware project
and enable `HAL_TIM_MODULE_ENABLED` in `stm32f1xx_hal_conf.h`. Keep timer initialization in
the target adapter/board scope, never in portable device code: capture is board-level
measurement, not a device register operation. Serialize the timer handle like a shared
peripheral and validate capture timing on real hardware.

### Output compare / square wave (PWM or toggle)

Verified HAL API (pinned `stm32f1xx_hal_tim.h`):

```c
HAL_StatusTypeDef HAL_TIM_OC_Init(TIM_HandleTypeDef *htim);
HAL_StatusTypeDef HAL_TIM_OC_ConfigChannel(TIM_HandleTypeDef *htim,
    TIM_OC_InitTypeDef *sConfig, uint32_t Channel);
HAL_StatusTypeDef HAL_TIM_OC_Start(TIM_HandleTypeDef *htim, uint32_t Channel);
HAL_StatusTypeDef HAL_TIM_OC_Start_IT(TIM_HandleTypeDef *htim, uint32_t Channel);
HAL_StatusTypeDef HAL_TIM_OC_Stop(TIM_HandleTypeDef *htim, uint32_t Channel);
/* PWM flavor: HAL_TIM_PWM_Init / HAL_TIM_PWM_ConfigChannel / HAL_TIM_PWM_Start / _Stop */
__HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, ccr);   /* runtime duty/phase update */
```

- `TIM_OC_InitTypeDef`: `OCMode` (`TIM_OCMODE_TOGGLE` for an exact 50 % square wave, or
  `TIM_OCMODE_PWM1`), `Pulse` (CCR), `OCPolarity` (`TIM_OCPOLARITY_HIGH`/`LOW`),
  `OCFastMode`. `CounterMode`, `Prescaler`, `Period` come from `TIM_Base_InitTypeDef`.
- GPIO: alternate-function push-pull (`GPIO_MODE_AF_PP`) with `GPIO_NOPULL`, no AF-number
  field. Default (no remap) pins are PA0/PA1/PA2/PA3 = CH1/CH2/CH3/CH4. Any remap needs the
  AFIO clock (`__HAL_RCC_AFIO_CLK_ENABLE()`) plus one of
  `__HAL_AFIO_REMAP_TIM2_PARTIAL_1()`, `__HAL_AFIO_REMAP_TIM2_PARTIAL_2()`,
  `__HAL_AFIO_REMAP_TIM2_FULL()` (or `__HAL_AFIO_REMAP_TIM2_DISABLE()` to clear) before GPIO
  init — see the [board profile](../boards/nucleo-f103.md) for the remap table and the
  PA2/PA3 VCP conflict.
- Frequency (16-bit `PSC`/`ARR`, timer clock `f_TIM2` = 72 MHz at 72 MHz SYSCLK):
  PWM `f_out = f_TIM2 / ((PSC+1) × (ARR+1))` with duty `CCR / (ARR+1)`; toggle
  `f_out = f_TIM2 / (2 × (PSC+1) × (ARR+1))` with exactly 50 % duty. At 72 MHz:
  `PSC=71, ARR=999, CCR=500` (PWM) or `PSC=71, ARR=499` (toggle) → 1 kHz.
- Interrupt (optional): `HAL_TIM_OC_Start_IT(..., TIM_CHANNEL_1)` + NVIC `TIM2_IRQn` +
  `HAL_TIM_OC_DelayElapsedCallback` / `HAL_TIM_PWM_PulseFinishedCallback` in the vector-wired
  handler path, with the same completeness rule as input capture.

## ADC1 / ADC2 (analog input)

ADC1 and ADC2 are 12-bit SAR ADCs. ADC1 has 16 external channels IN0–IN15 plus the internal
temperature sensor (ADC1_IN16) and VREFINT (ADC1_IN17). **The F103RB (medium-density) has no
DAC.** These are board-level peripherals: the portable device driver never initializes them;
the adapter owns clock, GPIO analog mode, conversion and value hand-off.

Verified HAL API (pinned `stm32f1xx_hal_adc.h`):

```c
HAL_StatusTypeDef HAL_ADC_Init(ADC_HandleTypeDef *hadc);
HAL_StatusTypeDef HAL_ADC_ConfigChannel(ADC_HandleTypeDef *hadc,
    const ADC_ChannelConfTypeDef *pConfig);
HAL_StatusTypeDef HAL_ADC_Start(ADC_HandleTypeDef *hadc);
HAL_StatusTypeDef HAL_ADC_PollForConversion(ADC_HandleTypeDef *hadc, uint32_t Timeout);
uint32_t HAL_ADC_GetValue(const ADC_HandleTypeDef *hadc);
HAL_StatusTypeDef HAL_ADC_Start_IT(ADC_HandleTypeDef *hadc);
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *hadc);
```

- Configure the ADC pins `GPIO_MODE_ANALOG` + `GPIO_NOPULL` (no alternate function).
- ADC reference is VREF+ (or VDDA); keep the measured voltage within that range. For the
  internal channels use the calibration values: temperature `TS_CAL1`/`TS_CAL2`, reference
  `VREFINT_CAL`.
- Polling: `HAL_ADC_Start` → `HAL_ADC_PollForConversion(…, finite timeout)` →
  `HAL_ADC_GetValue`. Interrupt: `HAL_ADC_Start_IT` + `HAL_ADC_ConvCpltCallback`. Use finite
  timeouts, never `HAL_MAX_DELAY`.
- Build prerequisite: add `stm32f1xx_hal_adc.c` and enable `HAL_ADC_MODULE_ENABLED` in
  `stm32f1xx_hal_conf.h`. Serialize the ADC handle and validate conversion/voltage on real
  hardware.

## Finite time, errors and ownership

HAL blocking timeout arguments use the HAL millisecond time base. Pass finite,
operation-specific timeouts, never routine `HAL_MAX_DELAY`; bound ready-poll trials,
retries and total multi-call duration separately. Check the exact pinned implementation:
a per-call timeout is not a guarantee that the whole higher-level operation meets one
deadline. Use wrap-safe unsigned elapsed-tick arithmetic and a remaining-budget policy.

Map `HAL_OK`, `HAL_ERROR`, `HAL_BUSY` and `HAL_TIMEOUT` distinctly to the driver's
transport status and retain `HAL_I2C_GetError`, `HAL_SPI_GetError` or
`HAL_UART_GetError` diagnostics when relevant. Do not parse an incomplete receive buffer,
turn a NACK into valid zero data, or retry an uncertain write as if it were idempotent.
Any retry/recovery must be explicit, bounded and compatible with the device and shared bus.
Do not reset/reinitialize a shared peripheral behind another device's transaction.

The [HAL tick implementation](https://github.com/STMicroelectronics/stm32f1xx-hal-driver/blob/master/Src/stm32f1xx_hal.c)
uses SysTick by default; `HAL_Delay` is a blocking minimum **millisecond** delay.
Tick suspension, disabled interrupts or an ISR that prevents the tick from running can
make delays/timeouts stop progressing. Use task context for blocking calls. Sensor
microsecond timing and [1-Wire](../interfaces/one-wire.md) slots need a separately
validated timer/protocol implementation, not rounded `HAL_Delay` calls.

HAL handle locking is not project-level bus arbitration. Serialize complete transactions
on one shared handle; keep device address/CS and state per device. With IT/DMA variants,
`HAL_OK` means accepted/start, not completed: buffers, locks and CS remain owned until
completion/error/abort handling establishes a terminal state with a finite deadline.

## Portable boundary, native evidence and refinement

Keep device register/protocol logic in the exported driver C/header. Put HAL handles,
MCU headers, address shifting, CS, timeouts, locks and tick/delay adaptation in the
project transport context; do not embed globals for “the one sensor” in portable code.
Two instances must not share mutable calibration, address or response buffers.

For native verification, compile the **actual exported portable driver C** with the
fake transport/HAL boundary described in
[runtime verification](../../datasheet2mcp/references/runtime-verification.md) and
[QEMU/native scopes](../tools/qemu.md). Exercise exact transmit bytes, address convention,
register width, read decoding, timeout/busy/NACK/error paths and instance isolation;
if testing the adapter too, fake the selected HAL signatures and assert the single shift.
A Python reimplementation or an always-success HAL stub is not compiled-driver evidence.
Fake time must progress deterministically. Native results do not establish F1 startup,
real peripheral behavior, electrical timing or hardware calibration.

Use [aggregation](../../aggregation.md) and [feedback identities](../../datasheet2mcp/references/feedback.md):
before and after integration, refine updates the **same canonical per-device records**.
Retain effective `hal_sha256` separately from `driver_sha256`, including vendor inputs,
enabled configuration, MSP/pin/clock, transport/time-base glue and declared build inputs.
Changed effective HAL requires revalidation of affected native/target/hardware evidence
and calibration bindings; a package version string or successful recompilation does not
revalidate a physical observation. Serialize shared-board/probe/file changes and preserve
other devices' facts. Building, executing or flashing generated code requires explicit
authorization; this guide claims no tests or hardware runs.
