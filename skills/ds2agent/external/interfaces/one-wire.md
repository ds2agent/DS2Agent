# 1-Wire

Use this guide for genuine 1-Wire devices with an identified master implementation.
Conventional 1-Wire is an open-drain, half-duplex data bus **plus ground**, with one
master and one or more addressed devices. External device power may add another wire;
parasite power is device- and operation-dependent. It is not ordinary one-wire UART.

## Required project binding

Keep the following with the owning device's canonical project records under
[aggregation](../../aggregation.md):

- Exact part/family/package and datasheet revision; function-command and CRC definitions.
- Master/adapter model and revision, driver/API version, host route, and implemented
  features: reset/presence, read/write slots, ROM selection/search, speed, and power delivery.
- For an MCU master: board, GPIO/timer or peripheral, open-drain circuit and real timing
  implementation. For a bridge: upstream bus/address/port and firmware/protocol identity.
- Device ROM identity and byte order; expected family code and permitted discovery scope.
  A ROM is a 64-bit bus identity, not an I²C address or physical connector number.
- DQ/ground/power mapping, pull-up rail, external vs parasite power, existing pull-ups,
  topology/cable load, device count, and any controlled strong-pull-up circuit.
- Datasheet-derived timing windows, selected standard/overdrive mode, recovery times,
  conversion/programming limits, finite transport/poll deadlines and shared-bus owner.

Unresolved electrical or timing requirements block hardware access. See the
[circuit guide](../reference-circuit.md); there is no universal pull-up resistance,
reset duration, sample instant, or safe cable length for all devices and masters.

## Select a real master backend

These are **documented hardware approaches**, not claims that this repository implements
or has tested every adapter:

| Approach | What an implementation must supply |
| --- | --- |
| Dedicated USB 1-Wire adapter | Exact adapter identity, supported OS/vendor driver/API, ROM/slot operations and supported power modes; a USB connector alone proves none of these |
| DS2482-100 I²C-to-1-Wire bridge | A real upstream I²C controller plus a DS2482 command/status driver, configuration/read-pointer handling, finite busy polling and power-control support |
| DS2480B UART-to-1-Wire converter | Correct converter hardware and its device-specific command/data-mode driver, not raw target command bytes written to a serial port |
| MCU master | Implemented timer/peripheral or bounded real-time slot engine with open-drain hardware, sampling/recovery guarantees and required power control |
| MCU exposed through serial | All MCU-master requirements plus implemented versioned serial bridge framing, status/error replies, routing and finite deadlines |

Bare `pyserial` does **not** provide generic 1-Wire reset, presence detection, ROM
search, CRC, or strong pull-up. UART waveform techniques require a suitable electrical
front end and a specifically implemented/verified timing scheme; joining TX/RX to DQ
or sleeping between Python writes is not such an implementation. A virtual COM port
does not establish a 1-Wire bridge. If the matching backend/firmware is missing, mark
that route unsupported instead of advertising a proposed bridge as ready.

For DS2482-100 specifically, its timed engine provides reset, byte, single-bit and triplet
operations. Initialize and verify configuration, issue the applicable command, poll the
`1WB` busy flag to a finite deadline, then inspect presence (`PPD`), short detection (`SD`)
and returned data as appropriate. Its internal reset is distinct from a downstream
1-Wire reset. Active pull-up improves edges; strong pull-up supplies sustained power:
they are not interchangeable settings. Follow the datasheet's command ordering and
SPU behavior; leaving strong pull-up enabled for reset can corrupt presence detection
and can violate device ratings.

## Real transaction sequence

1. **Idle and reset:** verify that the master can release DQ high. Pull DQ low for the
   selected device/master reset window, release it, then sample within the specified
   presence window. Observe reset-high/recovery time before sending a command. Read
   the actual timing table and diagrams for every family on the bus; standard and
   overdrive windows differ. Host scheduling delays are not a timing guarantee.
2. **Presence:** distinguish a valid presence pulse from no presence and a line stuck
   low. Presence means at least one responder, not identification or correct data.
3. **ROM phase:** choose a documented ROM command:
   - `Search ROM` enumerates a multidrop bus using each bit, its complement and a chosen
     search direction; implement and retain discrepancy traversal state. Bound device
     count, search passes and total time; report an incomplete search rather than
     claiming all devices were found.
   - `Read ROM` is only appropriate for a bus known to contain one responding device.
     Multiple responders collide.
   - `Match ROM` plus the complete discovered/configured identity selects one device.
   - `Skip ROM` addresses all devices. Use only when the specific command and population
     make broadcast safe; a broadcast read can combine conflicting replies.
4. **Function phase:** send the selected device's function command and required data
   using correctly timed write slots. A read slot is initiated by the master pulling
   low and releasing, then sampling within the documented read-valid window. Passive
   waiting for a UART-style response is not a 1-Wire read.
5. **Operation/power interval:** poll only when the device's power mode permits it;
   otherwise provide the required power and wait the documented bounded interval.
6. **Read and validate:** obtain the complete documented reply, verify CRC/status and
   decode it. Start another reset/ROM-selection sequence where the device requires it.

ROM and function-command support are family-specific. For example, the DS18B20
datasheet documents `Search ROM` (`0xF0`), `Read ROM` (`0x33`), `Match ROM` (`0x55`),
and `Skip ROM` (`0xCC`). A selected DS18B20 temperature operation can use `Convert T`
(`0x44`), the required ready/power interval, then a new reset/ROM selection and
`Read Scratchpad` (`0xBE`), reading all nine bytes to include CRC. This is a
**DS18B20 example**, not a generic command set for every 1-Wire device.

## CRC and power are part of correctness

For DS18B20, bytes are transferred least-significant-bit first. Its ROM contains a
family byte, serial number and CRC; its scratchpad has a separate CRC byte. The cited
datasheet defines polynomial `x^8 + x^5 + x^4 + 1`, zero initialization, bit order and
coverage: the first seven ROM bytes or the first eight scratchpad bytes, respectively.
Verify both the returned ROM identity and the requested data's CRC. Other devices may
use a different CRC/coverage; “CRC-8” alone is not a complete algorithm specification.
CRC failure must not become a successful reading or a silently substituted model value.
CRC integrity does not establish conversion freshness or physical measurement accuracy.

The normal pull-up must meet logic thresholds, sink-current and rise/recovery constraints
over the actual bus capacitance and device population. Inventory built-in adapter and
module pull-ups before adding components. Parasite-powered conversions, EEPROM writes
or other high-current operations may need a controlled strong pull-up initiated within
a device-specific deadline and held for a specified duration. Verify voltage at the
load, current budget and switching losses; a nominal adapter “power” capability is
not sufficient.

For parasite-powered DS18B20 conversion/copy operations, the datasheet requires strong
pull-up and prohibits other bus activity during that interval. Do not poll ready bits
while that power hold is required. Other families may need different supplies or
programming facilities; never apply elevated programming voltages merely because an
adapter offers them. External-power pin wiring is also device-specific.

Serialize reset, ROM selection, function command, data slots and required power holds
across every device on that physical bus. Reset affects all devices' bus protocol
state. A shared bridge also requires ownership of its upstream controller/address and
configuration. Release power control safely on failures according to the hardware's
documented procedure; do not recover by arbitrary resets during a power-critical write.

## Evidence and limits

Deterministic models may cover ROM search/selection, bit/byte order, CRC, scratchpad
state, modeled conversion delay and explicit faults. State which layers are modeled:
a byte-level emulator does not validate slot timing or analog power delivery. Native
fake-HAL and QEMU results likewise do not prove adapter or electrical behavior.

Retain ROM inventory, raw bytes/CRC outcomes, reset/presence/short results, master and
driver versions, binding/model revisions, speed/power mode, timing/deadline records
and supported/excluded operations. Authorized hardware checks must measure DQ levels,
reset/presence and read/write timing, recovery/rise time and voltage during the
highest-current power interval on the real topology. A CRC-valid sample is not physical
calibration; source/model evidence must never be reported as a connected-device pass.

## Primary references

- [ADI: Reading and Writing 1-Wire Devices Through Serial Interfaces](https://www.analog.com/en/resources/app-notes/reading-and-writing-1wirereg-devices-through-serial-interfaces.html):
  timing styles, bus electrical behavior, and UART/I²C/USB master distinctions.
- [DS2482-100 datasheet, Rev. 11](https://www.analog.com/media/en/technical-documentation/data-sheets/DS2482-100.pdf):
  command/status sequencing, active/strong pull-up, timing and electrical limits.
- [DS18B20 datasheet, Rev. 6](https://www.analog.com/media/en/technical-documentation/data-sheets/DS18B20.pdf):
  ROM commands, scratchpad, CRC, reset/slots and external/parasite-power requirements.
  These device-specific examples do not confer support for other families.
