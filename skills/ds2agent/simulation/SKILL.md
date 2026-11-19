---
name: simulation
description: Run device simulation models inside an STM32F103 firmware emulator (Unicorn M-class, QEMU-class backend) with runtime CLI parameter tuning. Use to derive co-simulation device models — adjustable parameters plus CLI — from a datasheet and reference driver, and to verify FreeRTOS/HAL firmware behavior end-to-end against them.
---

# simulation

Co-simulates real Cortex-M3 firmware (FreeRTOS/HAL) against device models over I2C, and
tunes the models at runtime. This skill owns the device-model contract, the CLI tuning
contract, and the generation rules; the QEMU backend admission and observability rules stay
in [../external/tools/qemu.md](../external/tools/qemu.md).

## What is where

| Layer | Location | Versioned |
|---|---|---|
| Contract / spec (this skill) | `skills/ds2agent/simulation/` | yes |
| Reference implementation (MCU emulator + device models) | `local_sim/` at the repo root | no (gitignored) |

The implementation is an instance of this contract, not the contract itself. The emulator
(`F103`) depends only on the `Device` interface; concrete device models are injected at
runtime (`F103(elf, devices=[...])`), so the skill never imports a specific device class.

## Device model contract

A device model is a `Device` subclass exposing exactly:

| Member | Meaning |
|---|---|
| `addr7` | 7-bit I2C address from the datasheet wiring |
| `name` | CLI device key |
| `params` | dict of runtime-adjustable physical quantities (`temp_c`, `roll_deg`, `current_a`, …) |
| `on_write(data)` | one I2C write transaction (register address or command frame) |
| `on_read()` | one I2C read transaction's reply bytes |
| `set_param` / `get_params` | CLI parameter access |

`params` hold physical quantities, never raw register words; `on_read` derives register
bytes from `params` using the datasheet conversion so the firmware's own interpretation
runs unchanged.

## CLI tuning contract

`set <dev> <param> <value>` / `get <dev>` / `list`. Aliases map to canonical `params` keys
(`temp`→`temp_c`, `roll`→`roll_deg`, `current`→`current_a`, …); an alias never creates a
second key. The required closed loop: `set` a parameter, run the firmware, observe its
reaction (UART text, TIMx CCR duty, GPIO/relay state).

## Generation rules and verification scope

The full contract, transaction shapes, per-device conversion examples, and generation rules
are in [references/co-simulation.md](references/co-simulation.md). Co-simulation establishes
firmware behavior within the modeled register/command scope; it does not establish electrical
compatibility, physical bus timing, or sensor accuracy. Report co-simulation results
separately from native-driver and hardware checks.
