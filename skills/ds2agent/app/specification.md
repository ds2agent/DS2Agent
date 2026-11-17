# Application (control) firmware — description specification

The APP layer is the board's application firmware: cold boot, the line-oriented
control protocol, and the command loop. It bridges the host (control UART) to
the board and device layers. The concrete verbs and operations follow the user's
stated requirements; this spec pins the structure and the invariants the APP
must hold, so a generated APP compiles, receives, dispatches, and is verified
correctly. Follow the selected board's control-path requirements in
[../board.md](../board.md).

## Files

- `main.c` — cold boot, banner, `READY`, command loop.
- `control.c/.h` — bounded line parser and verb dispatch, no stdio/heap in the
  parse path.
- `board_binding.h` — build/binding identity generated from `board.json`.

These files are required board artifacts under `boards/<board_id>/firmware/` and are
hash-recorded in `board.json` as `app_source` (`main.c`), `control_source` (`control.c`),
`control_header` (`control.h`) and `binding_header` (`board_binding.h`).

## Cold boot order

HAL → power/voltage scale → clock → time base → GPIO clocks → control UART →
banner → `READY`. Do not touch device buses or the sensor before the host init
verb. No command is accepted before `READY`.

## Control protocol

- Line-oriented, one request per line, CR/LF/CRLF terminated, case-insensitive
  verbs, with a hard line bound; an overlong line is drained then answered once
  with an error.
- RX is polled in the command loop: read the UART RXNE flag and feed each byte
  to the line reader (no interrupt, no ring buffer). Polling is the simple
  default for single-device firmware; interrupt-driven RX (IRQ handler + NVIC
  enable + RxCplt re-arm) is optional and only justified at higher throughput.
- Exactly one deterministic reply line per request; never reconfigure the live
  control UART while replying.

## State machine

`uninitialized → initializing → ready | failed | unknown`; the same ready
binding returns `already_ready`, a changed binding returns `busy`; a timeout is
`unknown` with no blind retry; a failure reports stage plus raw HAL status/error
and never spins inside an init path.

## Correctness invariants

- A value transform (for example uppercase a character) returns that value's
  type (`char`), never `bool`; a predicate returns `bool`.
- If any interrupt is used, enumerate every interrupt the code enables and
  check each one in a single pass for complete configuration: the peripheral
  interrupt enable, the NVIC enable (`HAL_NVIC_EnableIRQ(<IRQn>)` or
  equivalent), and the ISR handler wired in the vector table that calls the
  matching `HAL_<PERIPH>_IRQHandler`. For example SysTick (enabled by
  `HAL_InitTick`) needs `SysTick_Handler` → `HAL_IncTick`; USART2 RX needs
  `USART2_IRQHandler` → `HAL_UART_IRQHandler` plus the NVIC enable plus
  re-arming `HAL_UART_Receive_IT`. Missing any one → the IRQ lands in the weak
  `Default_Handler` (hang) or is silently dropped. Polled RX (no interrupt)
  only drains RXNE each pass (reading RDR clears the flag).
- Check wiring completeness: every generated setup function (`bind`, `init`,
  `configure`, `start`) must be called somewhere in the control flow, in the
  right order — for example the init verb must call the adapter's `bind` before
  its `init`. A setup function that is defined but never called is a wiring bug
  that compiles silently (an unused function emits no error).

## Behavioral acceptance

At minimum a per-verb round-trip (for example `PING` → the expected reply)
against the built firmware or a UART loopback. A passing build proves
compilation, not correct parsing or dispatch.
