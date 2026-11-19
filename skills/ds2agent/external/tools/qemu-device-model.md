# Writing a QEMU device model (C QOM / bus slave)

A QEMU device model is not a Python class — it is a **C QOM object compiled into a QEMU
build**. The datasheet supplies the register map, formulas, timing, and reply layout; the C
code implements them behind QEMU's bus interface. This is a C development task, not a
"regenerate and run" step, and it is a separate artifact from the Unicorn co-simulation
models in [simulation](../simulation/SKILL.md).

## When this applies

Use this only when a caller explicitly requests the `qemu` backend and no verified QEMU
target yet models the required MCU controller + external device. Do not generate a port
implicitly to fill missing target support — see [qemu.md](qemu.md).

## Two distinct pieces of work

1. **The external device (sensor) model** — a QOM object implementing the bus slave
   interface.
2. **The MCU machine / SoC** — CPU, memory map, interrupt routing, and the on-chip controller
   (e.g. I2C) the device plugs into.

If the MCU is already in QEMU, only (1) is needed. There is no stock STM32F103 machine, so
for that target (2) must also be done before any firmware runs. Admit both through the
[target admission checklist](qemu.md) before advertising support.

## Device model anatomy (I2C slave)

A minimal I2C slave is one C file plus a build registration:

- **QOM object**: a struct holding device state (register pointer, register values, staged
  reply bytes, status flags), a `TypeInfo` with `.parent = TYPE_I2C_SLAVE`, `.instance_size`,
  `.class_init`, `.instance_init`, registered via `type_init`/`DEFINE_TYPES`.
- **`I2CSlaveClass` callbacks**:
  - `send(dev, byte)` — master→device write: the first byte of a transaction is the
    register/command pointer, following bytes are data; update state.
  - `recv(dev)` — device→master read: return the next reply byte for the current pointer.
  - `event(dev, event)` — bus events (`I2C_START_RECV`, `I2C_START_SEND`, `I2C_FINISH`,
    `I2C_NACK`) reset the per-transaction state.
- **Build**: add the object to the target's `meson.build` sources so it links into the
  machine.
- **Wiring**: instantiate the device and attach it to the controller's `I2CBus`
  (`i2c_realize_and_unref` or an `i2c` bus property) in the SoC/machine init.

The interface, constants, and registration macros are release-specific. Read the selected
QEMU tree, not this summary: `hw/i2c/` for existing slave devices, the I2C header for
`I2CSlaveClass` and event values, `hw/i2c/stm32f2xx_i2c.c` for the controller side, and the
machine's `*_soc.c` for wiring.

## What the datasheet provides vs what you write

| From datasheet / driver | You implement in C |
|---|---|
| register map, reset values, read/write semantics | struct fields + the `send`/`recv` state machine |
| conversion formulas (raw ↔ physical) | the arithmetic in register/recv handlers |
| command sequence, timing, reply layout | the `event`/state transitions |
| documented failure modes | explicit NACK/error behavior |

Unmodeled operations must fail explicitly, not return a plausible default — the same rule as
the Unicorn models and the native harness.

## Verification (independent, not self-referential)

Rebuild QEMU, run the same finite scenario used for admission, and check the observable
output against an independent derivation (datasheet reference vectors or a native harness) —
not just agreement between the C model and a mock generated from the same formula. Record
the QEMU version/build, machine, device list, firmware hash, exact command line, and known
omissions. A device listed by `-device help` that cannot attach to the chosen machine's bus
is not a supported device.

## Effort boundary

Writing and rebuilding a QEMU device is C development, gated on the same explicit
`--allow-code-execution` as building firmware. Do not auto-install QEMU or a toolchain.
Prefer the Unicorn co-simulation path ([simulation](../simulation/SKILL.md)) when the caller
only needs firmware behavior; escalate to QEMU only when the requested scope explicitly
requires the QEMU backend and a verified target is being added.
