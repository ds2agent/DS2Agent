# Device co-simulation models (F103 + I2C + runtime CLI)

A device model generated from a datasheet/driver must also run inside the F103 firmware
emulator, not only against an in-memory register dictionary. This reference specifies the
co-simulation model contract, the runtime CLI tuning contract, and the generation rules
that make a datasheet-derived model usable by `local_sim/f103_emu.py`.

The emulator (`F103`) runs real Cortex-M3 firmware (FreeRTOS/HAL) over Unicorn and drives
device models through an I2C bus. A model is a `Device` subclass attached to `I2CBus`; its
parameters are mutable at runtime through `set/get/list` commands. This is the "behavior"
model made live: the firmware reads/writes the device, the operator perturbs parameters, and
the firmware reacts (fan duty, motor PWM, relay trip). Use it to establish firmware behavior
within the emulator's modeled scope — not physical bus timing or sensor accuracy.

## Model contract (`Device` subclass)

Each model MUST implement, with no other machinery:

| Member | Meaning | Requirement |
|---|---|---|
| `addr7` | 7-bit I2C address | exact datasheet address for the wiring (SDO/ALT pulled low, etc.) |
| `name` | CLI device key (lowercase) | stable, unique on the bus |
| `params` | dict of runtime-adjustable physical quantities | one key per observable the firmware consumes |
| `on_write(data: bytes)` | one I2C write transaction (register address, or command frame) | record state; set the register pointer / pending flag |
| `on_read() -> list[int]` | one I2C read transaction's reply bytes | return the register(s) the firmware will read next |

`params` hold physical quantities (`temp_c`, `roll_deg`, `current_a`, `bus_v`), never raw
register words. `on_read` derives raw register bytes from `params` using the datasheet's
documented conversion (scale/offset/format), so the firmware's own interpretation code runs
unchanged. Unmodeled registers MUST return an explicit value (a documented reset default or
zero), never a guessed plausible reading; a read the datasheet does not define is out of
scope for that model.

Transaction shapes the bus delivers (see `I2C1Periph`):

- Register-write (`HAL_I2C_Mem_Write`): `on_write([reg, hi, lo, ...])` — first byte is the
  register address, remaining bytes the big-endian value.
- Register-read (`HAL_I2C_Mem_Read`): `on_write([reg])` is flushed on the repeated START,
  then `on_read()` returns the register's bytes (big-endian for 16-bit registers, little-endian
  for ADXL345-style multi-byte data as the datasheet defines).
- Command/response (PN532-style): `on_write(frame)` parses a command and stages a response;
  `on_read()` returns the staged ACK/response bytes across successive read transactions.

Keep the model stateful and minimal: store the register pointer, pending flags, and staged
responses; compute reply bytes from `params` at read time. Do not duplicate firmware logic.

## CLI tuning contract

`F103.handle_command(line)` implements the runtime contract. Every generated model works with
it without extra code:

- `set <dev> <param> <value>` — update a physical parameter. Parameter aliases map to the
  canonical key: `temp`/`temperature`/`temp_c` → `temp_c`, `rh`/`humidity` → `rh_pct`,
  `roll`/`angle` → `roll_deg`, `pitch` → `pitch_deg`, `current`/`amps` → `current_a`,
  `bus`/`voltage` → `bus_v`, `uid` → `tag_uid` (byte list), `present` → `tag_present` (bool).
- `get <dev>` — dump `params`.
- `list` — `name@0xADDR` for every attached device.

The canonical `params` key is the source of truth; aliases are convenience only and MUST
map to an existing key, never create a second key (`temp` must not coexist with `temp_c`).
Numeric values are parsed with `float()`; the model clamps to its documented range. The
closed loop the contract must support: `set` a parameter, run the firmware, observe the
firmware's reaction (UART text, TIMx CCR duty, GPIO/relay state).

## Generation rules

1. From the datasheet register map + the firmware's driver (`ina219.c`, `adxl345.c`, ...),
   list exactly the registers the firmware writes and reads at boot and in its loop.
2. Boot probes first: chip-ID/DEVID and configuration read-back MUST return the documented
   values, or the firmware reports "not found" and the model is useless. Implement the ID
   register and every config register the driver writes then reads back.
3. Map each runtime observable to one physical `params` key, and encode it with the
   datasheet's conversion. Examples (all verified against the three projects):
   - SHT31: `temp_c`/`rh_pct` → raw 16-bit = value/(full-scale) × 65535, CRC8 per byte pair.
   - ADXL345: `roll_deg`/`pitch_deg` → `ax=sin(roll)`, `az=cos(roll)cos(pitch)` × 256
     counts/1 g; DEVID `0xE5`; scale cancels in the firmware's `atan2`.
   - INA219: `current_a` → Current register = `current_a × 1e4` (100 µA/LSB, CAL=4096);
     `bus_v` → Bus register = `((bus_v×1000)/4) << 3` (4 mV/LSB); CONFIG `0x399F` read-back.
4. Add the model to `local_sim/devices.py` and its CLI aliases in `local_sim/f103_emu.py`;
   verify the closed loop against the actual firmware ELF before declaring the model usable.

## Verification scope

A co-simulated model establishes firmware behavior within the modeled register/command scope.
It does NOT establish electrical compatibility, physical I2C timing, or sensor accuracy.
Report co-simulation results separately from native-driver and hardware checks; a model that
matches the firmware's expected boot IDs and reacts correctly to a `set` perturbation is the
deliverable evidence, not a substitute for hardware. The F103 emulator is functional (Unicorn
M-class), not cycle-accurate: modeled peripherals are I2C1, USART2 TX, RCC, GPIO/bit-band,
SysTick, NVIC exception entry/return (SVC/PendSV), and a store-through TIM2; anything the
firmware touches beyond that is unmodeled and must not be claimed as verified.
