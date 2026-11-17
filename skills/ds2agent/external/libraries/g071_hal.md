# STM32G0 HAL: G071RB transport binding

Use this guide for **STM32G071RB + STM32CubeG0 HAL** (`stm32g0xx_hal_*`).
G071 is not an F103 with renamed includes: clocking, GPIO alternate functions, interrupt
grouping, I2C timing and startup/device support differ. This guide does not supply an F7
binding or declare hardware/QEMU support.

## Reproducible inputs and project boundary

Select a [STM32CubeG0](https://github.com/STMicroelectronics/STM32CubeG0) release and
record the exact HAL/CMSIS/BSP component commits, source hashes and licenses from its
[component manifest](https://github.com/STMicroelectronics/STM32CubeG0/blob/master/.gitmodules).
The upstream API links below move over time; they are references, not version pins.
Inventory all used sources/headers in the BSP manifest: `stm32g0xx_hal.h`, project
`stm32g0xx_hal_conf.h`, enabled I2C/SPI/UART/GPIO/RCC/core/extension/DMA modules,
CMSIS core/device support, startup/system/vector files, linker script, MSP/IRQ/time-base
glue, compiler definitions and flags. Do not edit vendor HAL sources.

Choose **STM32G071xx** device support, Cortex-M0+/Thumb compilation with a non-FPU ABI,
and a linker script for the fitted G071RB memory map. A G070/G0B1 board example or F103
linker/startup file is not interchangeable. Record the actual
[NUCLEO-G071RB](../boards/nucleo-g071.md) PCB revision and project connector/AF pin map.
The vendor `STM32G0xx_Nucleo` BSP's LED/shield constants do not prove external wiring.

## Initialize the G071, not a copied F1 setup

1. Supply correct startup/vector/system code, initialize HAL and the time base, then
   configure the verified oscillator/PLL, bus and peripheral kernel clocks with appropriate
   Flash/power settings. Record generated project inputs and actual clock sources.
2. Enable peripheral/GPIO clocks; configure the **G071 AF number** for each pin and
   board-specific direction/pull/idle state. I2C needs alternate-function open-drain and
   topology-appropriate pull-ups. F1 AFIO remap code is not a G0 pin configuration.
3. Implement selected `HAL_I2C_MspInit`, `HAL_SPI_MspInit` and/or `HAL_UART_MspInit`
   resources. Add matching NVIC/IRQ handlers and linked DMA handles/routing when those
   modes are used. Use the G071 vector table rather than copying F1 interrupt names.
   **Interrupt completeness:** if any interrupt is used, enumerate every enabled
   interrupt and check each one in a single pass — peripheral interrupt enable, NVIC
   enable (`HAL_NVIC_EnableIRQ(<IRQn>)`), and the ISR wired in the vector table that
   calls `HAL_<PERIPH>_IRQHandler` (SysTick → `SysTick_Handler`/`HAL_IncTick`; USART2 RX
   → `USART2_IRQHandler`/`HAL_UART_IRQHandler` + re-arm `HAL_UART_Receive_IT`). Missing
   any one lands in the weak `Default_Handler` (hang) or silently drops the IRQ.
4. Set handle `Instance` and every required `Init` field, check each initialization
   result, and expose no working transport on failure. Put SPI CS into its inactive state
   before transfers. Initialization errors must reach a bounded caller, not hang forever.

G0 `I2C_InitTypeDef` has **`Timing`** (I2C_TIMINGR), not F1 `ClockSpeed`/`DutyCycle`.
Derive the timing value from the selected I2C kernel clock, required rate, rise/fall-time
assumptions and configured filters using the selected Cube tooling/reference manual.
Record those inputs; a hexadecimal value from another clock/board is not a portable
default. If used, configure analog/digital filtering through the pinned extended-I2C API
and check the result. See the official
[I2C header](https://github.com/STMicroelectronics/stm32g0xx-hal-driver/blob/master/Inc/stm32g0xx_hal_i2c.h)
and [I2C source/how-to](https://github.com/STMicroelectronics/stm32g0xx-hal-driver/blob/master/Src/stm32g0xx_hal_i2c.c).
Use the [G071 product documentation/errata](https://www.st.com/en/microcontrollers-microprocessors/stm32g071rb.html)
for device-specific restrictions.

## Relevant blocking APIs and framing

The following are current upstream shapes. Use the pinned headers for the selected
release's qualifiers and available features; do not compile against mixed HAL versions.

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
GPIO_PinState HAL_GPIO_ReadPin(GPIO_TypeDef const *port, uint16_t pin);
uint32_t HAL_GetTick(void);
void HAL_Delay(uint32_t milliseconds);
```

Official declarations:
[SPI](https://github.com/STMicroelectronics/stm32g0xx-hal-driver/blob/master/Inc/stm32g0xx_hal_spi.h),
[UART](https://github.com/STMicroelectronics/stm32g0xx-hal-driver/blob/master/Inc/stm32g0xx_hal_uart.h),
[GPIO](https://github.com/STMicroelectronics/stm32g0xx-hal-driver/blob/master/Inc/stm32g0xx_hal_gpio.h),
[HAL core](https://github.com/STMicroelectronics/stm32g0xx-hal-driver/blob/master/Inc/stm32g0xx_hal.h).

| Binding | Required adapter behavior |
|---|---|
| 7-bit I2C target | Keep the canonical address unshifted; pass `(uint16_t)(address7 << 1)` as HAL `DevAddress`, exactly once at this boundary. HAL supplies the direction bit. Ten-bit addressing needs a separate explicit binding. |
| Register read/write | `reg_size` is `I2C_MEMADD_SIZE_8BIT` or `I2C_MEMADD_SIZE_16BIT`, not payload width. Select `Mem_Read`/`Mem_Write` only if their register-address framing matches the device protocol. Do not shift `reg`. |
| Combined I2C transaction | `Mem_Read` provides the register-address/repeated-START/read shape. Separate blocking master transmit/receive calls have a STOP between them; use the pinned sequential APIs when a different repeated-START sequence is required. |
| SPI | Bind CPOL/CPHA, prescaler, bit order, configured word width and software/hardware NSS policy. Hold the device's CS through the whole frame and release it on failure. `Size` counts configured data units, not invariably bytes; obey pinned buffer layout/alignment for wider transfers. |
| UART | Bind baud/framing and protocol-defined response length; keep partial/failed reads distinct from valid frames. UART is not an automatic sensor-bus bridge. |
| GPIO | Pass `GPIO_PIN_n` bit masks and explicit port/polarity. A `void` write does not verify a physical level; determine device reset/CS timing from its datasheet. |

Keep device-specific command bits, dummy bytes, byte order, response length and timing in
the portable driver/protocol, not guessed from a HAL function name. See
[I2C](../interfaces/iic.md), [SPI](../interfaces/spi.md) and [UART](../interfaces/uart.md).

## TIM2 input capture (timer peripheral)

TIM2 is a 32-bit general-purpose timer on APB1 with four capture/compare channels. In the
documented 56 MHz profile (APB1 prescaler = 1) its kernel clock is PCLK1 = 56 MHz; the
prescaler/period derive from that clock, not a guessed constant.

Verified HAL API (pinned `stm32g0xx_hal_tim.h`):

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

Pins: PA0 = TIM2_CH1, PA1 = TIM2_CH2, both `GPIO_AF2_TIM2`. Configure
`GPIO_MODE_AF_PP` + `GPIO_NOPULL` + AF2. For input capture the timer samples the AF input;
software drives no push-pull level on these pins while the channel is active.

Tick resolution example (56 MHz kernel): `Prescaler = 55` → 56 MHz / (55+1) = 1 MHz = 1 µs per
tick. For period/pulse measurement set `Period = 0xFFFFFFFF` (32-bit) to avoid overflow on long
intervals, then `period_us = (ccr_after - ccr_before) / tick_MHz`.

Interrupt path: enable TIM2 (`__HAL_RCC_TIM2_CLK_ENABLE()`), configure NVIC `TIM2_IRQn`,
`HAL_TIM_IC_Start_IT(&htim2, TIM_CHANNEL_1)`, read the value in `HAL_TIM_IC_CaptureCallback`,
and handle wrap with `HAL_TIM_PeriodElapsedCallback`.

Build prerequisite: the bundled SDK ships `stm32g0xx_hal_tim.h` but **not**
`stm32g0xx_hal_tim.c`; add that source (and `_ex` when needed) to the firmware project and
enable `HAL_TIM_MODULE_ENABLED` in `stm32g0xx_hal_conf.h`. Keep timer initialization in the
target adapter/board scope, never in portable device code: capture is board-level measurement,
not a device register operation. Serialize the timer handle like a shared peripheral and
validate capture timing on real hardware.

## ADC1 / DAC1 (analog peripherals)

ADC1 is a 12-bit SAR ADC (resolution selectable 6/8/10/12 bits) with channels IN0…IN18 plus
internal temperature / VREFINT / VBAT. DAC1 is 12-bit dual-channel (DAC_OUT1 = PA4,
DAC_OUT2 = PA5). These are board-level peripherals: the portable device driver never
initializes them; the adapter owns clock, GPIO analog mode, conversion and value hand-off.

Verified HAL API (pinned headers):

```c
/* ADC1 */
HAL_StatusTypeDef HAL_ADC_Init(ADC_HandleTypeDef *hadc);
HAL_StatusTypeDef HAL_ADC_ConfigChannel(ADC_HandleTypeDef *hadc, const ADC_ChannelConfTypeDef *pConfig);
HAL_StatusTypeDef HAL_ADC_Start(ADC_HandleTypeDef *hadc);
HAL_StatusTypeDef HAL_ADC_PollForConversion(ADC_HandleTypeDef *hadc, uint32_t Timeout);
uint32_t HAL_ADC_GetValue(const ADC_HandleTypeDef *hadc);
HAL_StatusTypeDef HAL_ADC_Start_IT(ADC_HandleTypeDef *hadc);
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *hadc);
/* DAC1 */
HAL_StatusTypeDef HAL_DAC_Init(DAC_HandleTypeDef *hdac);
HAL_StatusTypeDef HAL_DAC_Start(DAC_HandleTypeDef *hdac, uint32_t Channel);
HAL_StatusTypeDef HAL_DAC_SetValue(DAC_HandleTypeDef *hdac, uint32_t Channel, uint32_t Alignment, uint32_t Data);
HAL_StatusTypeDef HAL_DAC_Stop(DAC_HandleTypeDef *hdac, uint32_t Channel);
```

- Configure ADC/DAC pins `GPIO_MODE_ANALOG` + `GPIO_NOPULL` (no alternate function).
- ADC reference is VREF+ (or VDDA); keep the measured voltage within that range. For internal
  channels use the calibration values: temperature `TS_CAL1`/`TS_CAL2`, reference `VREFINT_CAL`.
- Polling: `HAL_ADC_Start` → `HAL_ADC_PollForConversion(…, finite timeout)` → `HAL_ADC_GetValue`.
  Interrupt: `HAL_ADC_Start_IT` + `HAL_ADC_ConvCpltCallback`. Use finite timeouts, never
  `HAL_MAX_DELAY`.
- Build prerequisite: the bundled SDK ships the headers but not the HAL `.c` sources; add
  `stm32g0xx_hal_adc.c` / `stm32g0xx_hal_dac.c` (and `_ex`) and enable `HAL_ADC_MODULE_ENABLED`
  / `HAL_DAC_MODULE_ENABLED` in `stm32g0xx_hal_conf.h`. ADC/DAC are shared peripherals:
  serialize the handle and validate conversion/voltage on real hardware.

## Deadline, error and concurrency contracts

Blocking timeouts use the HAL millisecond time base. Supply finite per-call values and
an overall operation budget, including any explicit bounded retries/ready-poll trials;
do not routinely pass `HAL_MAX_DELAY`. Inspect the pinned implementation's internal
waits: a timeout argument does not establish a universal end-to-end wall-clock deadline.
Use wrap-safe unsigned tick subtraction and a remaining-budget policy across phases.

Propagate `HAL_OK`, `HAL_BUSY`, `HAL_TIMEOUT` and `HAL_ERROR` distinctly; retain
`HAL_I2C_GetError`, `HAL_SPI_GetError` or `HAL_UART_GetError` diagnostics as applicable.
NACK, arbitration loss, partial data and timeout are not valid zero measurements.
Do not retry an uncertain non-idempotent write automatically. Recovery must be explicit
and bounded and must not reset/reconfigure a shared peripheral while another device owns it.

The [HAL core implementation](https://github.com/STMicroelectronics/stm32g0xx-hal-driver/blob/master/Src/stm32g0xx_hal.c)
uses SysTick by default; `HAL_GetTick` reports milliseconds and `HAL_Delay` is a blocking
minimum millisecond delay, not a microsecond timer. A suspended/unserviced tick can make
timeouts and delays stop progressing. Keep blocking calls in task context rather than an
ISR that prevents the tick interrupt from running. Sub-millisecond sensor timing and
[1-Wire slots](../interfaces/one-wire.md) need an explicitly validated timing backend.

For two devices, serialize each shared bus/HAL handle across complete transactions, not
each byte/call independently. HAL's handle lock is not sufficient project arbitration.
IT/DMA `HAL_OK` is acceptance/start, not completion: preserve buffers, transaction locks
and CS ownership until completion/error/abort establishes a terminal state under a finite
deadline. Configure the actual G071 interrupt/DMA topology and callback ownership.

## Portable C, fake-HAL checks and evidence

Keep protocol/register/decoding logic in the exported portable C/header. The target
adapter owns MCU includes, handles, AF/clock setup, address conversion, CS, locks,
timeout mapping and delays. Store context, address/CS, calibration and buffers per device;
do not hardcode one global sensor or let refine overwrite another device's binding.

For native evidence compile the **actual exported portable driver C** with deterministic
fake transport/HAL, following
[runtime verification](../../datasheet2mcp/references/runtime-verification.md) and
[native/QEMU guidance](../tools/qemu.md). Check exact command bytes, register/address
widths, returned-value decoding, finite fake-time progression, busy/NACK/timeout/error
paths and two-instance isolation. When exercising the target adapter, fake the pinned
HAL signatures and assert that the 7-bit address is shifted once. An always-success
stub or independent Python model is not a substitute for executing the exported C.
Native fake HAL cannot establish G071 peripheral, real electrical timing or calibration.

Use the **same canonical per-device records** for refine before and after
[single-MCP integration](../../aggregation.md). Follow
[feedback bindings](../../datasheet2mcp/references/feedback.md):
retain `{device_id, board_id, driver_sha256, hal_sha256, plan_sha256}` and model/calibration
revisions. Effective HAL hashing includes selected vendor inputs/configuration and
MSP/pin/clock, transport/time-base glue and declared build inputs. A changed effective
HAL requires revalidation of affected evidence/calibration, not a version-string update
or silent reassignment of old observations. Serialize shared-board/probe/file changes;
shared firmware may affect both devices. Generated execution/build/flash needs explicit
authorization. No test run, hardware result or QEMU support is claimed by this guide.
