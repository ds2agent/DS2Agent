# I²C (IIC / TWI)

Use this guide to bind a datasheet's I²C transactions to a real controller, MCU HAL,
or explicitly implemented bridge. SDA and SCL normally use open-drain outputs and
pull-ups; a ground reference is also required. SMBus is a related protocol with
additional conventions and limits, not a synonym for arbitrary I²C transfers.
The device datasheet determines its supported commands and electrical limits.

## Record the project binding first

Keep these choices in the owning device's canonical project records, following
[aggregation](../../aggregation.md), rather than hard-coding a second runtime configuration:

| Binding | Required information |
| --- | --- |
| Identity | Device ID, exact part/package and datasheet revision/sections; board or adapter identity and revision |
| Route | Host adapter and stable bus identity, or MCU peripheral/pins/HAL version, or identified bridge firmware/protocol version |
| Address | Canonical unshifted address, address width, strap states, mux/channel route if present |
| Electrical | VDD/VDDIO and pull-up rail, pin voltage tolerance, existing/effective pull-ups, capacitance estimate and selected clock |
| Transactions | Pointer width/byte order, command bytes, data length/order, START/STOP rules, conversion-ready conditions |
| Ownership | Shared board/bus/mux lock identity, other owners, permitted operations, finite transport and operation deadlines |

An unresolved pin map, supply, address strap, or transport capability blocks hardware
binding. See the [circuit guide](../reference-circuit.md) for electrical checks.

## Addresses and transaction boundaries

- Store a 7-bit address as `A`, without the direction bit. The on-wire address byte is
  `(A << 1) | direction`; a datasheet's separate write/read address bytes may therefore
  describe one target. Distinguish these representations explicitly; never shift twice.
  Linux I²C/smbus2 uses the unshifted address. Some MCU HAL APIs expect a shifted argument:
  verify the selected HAL documentation and convert only at that boundary. Do not infer
  the convention from the argument's integer type.
- Ten-bit addressing requires explicit controller, backend, and target support; it is
  not an extended 7-bit literal. Reserved addresses and general call are not ordinary
  device choices.
- A common register-read sequence is
  `START → A+W → pointer bytes → repeated START → A+R → N data bytes → STOP`.
  This is a template, not a universal register protocol. Some targets require STOP,
  a delay, command framing, or a different pointer width. Cite their transaction diagram.
- The **receiver** supplies ACK after a byte. During a read, the controller normally
  ACKs intermediate data bytes and NACKs the final byte before ending the transfer.
  Address ACK shows a responder, not correct identity, a valid register, or fresh data.
  Address/data NACK can mean absence, busy state, an unsupported command, or electrical
  failure; interpret it with the target's documented state.
- STOP between pointer write and read is not equivalent to repeated START. Keep a
  required combined transfer indivisible. Also protect multi-transfer device sequences
  whose pointer, page, mux route, or conversion state could be changed by another caller.

## Choose an implemented backend

**Native host controller:** on Linux, smbus2 wraps `/dev/i2c-*` and kernel I²C/SMBus
operations. A bus number is not a portable physical identity. Verify the adapter's
capabilities and permissions without taking over a device already owned by a kernel driver.
For a documented combined transfer, the API pattern is
`i2c_msg.write(address7, pointer_bytes)`, `i2c_msg.read(address7, count)`, then
`bus.i2c_rdwr(write_msg, read_msg)` in **one call**. These are API templates, not executed
examples. `I2C_RDWR` requires the adapter's plain-I²C capability; SMBus convenience
methods are valid only when their exact wire framing, length, and byte order match.
Do not add PEC unless the target protocol requires it.

**MCU HAL:** generate portable driver operations through the chosen board/HAL binding.
Check that the memory-read or sequential-transfer API actually produces the required
pointer width and repeated START. Two unrelated transmit/receive calls may insert STOP.
Use finite HAL timeouts and map NACK, arbitration loss, bus error, and timeout distinctly.

**USB adapter or serial bridge:** identify the exact hardware, vendor API, and supported
combined-transfer/clock-stretch behavior. A USB UART, ST-LINK virtual COM port, or
`pyserial` object is not an I²C controller. PC-to-MCU access requires implemented
firmware and a versioned command/reply protocol with lengths, status, and deadlines;
otherwise report that hardware route as unsupported, not ready.

## Pull-ups, speed, and bounded access

1. Check that the pull-up rail satisfies every participant's input-high threshold and
   operating pin-voltage limits, including unpowered participants. Level translation
   must support open-drain bidirectionality and any required clock stretching.
2. Inventory pull-ups already fitted to the board, sensor modules, and adapter.
   Parallel resistors form one effective pull-up; adding another can exceed sink current.
3. NXP UM10204 §7.1 gives the resistor design window. For its lumped RC/30–70% threshold
   assumptions, `Rp(max) = tr(max) / (0.8473 × Cb)` and
   `Rp(min) = (Vpullup - VOL(max)) / IOL`. Use the limiting participant's guaranteed
   sink capability and applicable mode specifications, supply/component tolerances,
   leakage, and total wiring/pin capacitance. A fixed resistor value is not universal.
   If the windows do not overlap, change the electrical design or supported speed.
4. Select a clock supported by the complete bus, not merely the controller. Standard,
   Fast, Fast-mode Plus, and High-speed modes have different requirements:
   Fast-mode Plus reaches 1 Mbit/s; 3.4 Mbit/s belongs to High-speed mode, with its
   additional protocol requirements. Lowering the requested clock alone does not
   establish electrical compliance.
5. Set a total operation deadline and bounded poll count from documented startup,
   stretching, conversion, and transport limits. An application deadline does not
   interrupt a blocked kernel ioctl: establish a backend/driver timeout or cancellable
   worker boundary before advertising a hard deadline.
6. Do not probe by indiscriminate address scans or blindly retry writes: probe traffic,
   general call, and repeated side-effecting commands can alter devices. Bus-clear
   clocks, controller resets, and power cycling require an agreed recovery procedure
   and exclusive ownership of all affected devices.

Serialize shared controller configuration, mux selection, and complete transactions
across device tools behind the single MCP entry. A process-local lock does not exclude
other host processes or firmware controllers; document that ownership boundary.

## Evidence and limits

A deterministic model may check addresses, register-pointer state, lengths, byte order,
and modeled ready/NACK conditions. Explicitly reject unmodeled commands; do not invent
successful replies. A model cannot demonstrate pull-up adequacy, clock stretching on a
particular adapter, rise time, signal integrity, or physical sensor calibration.

Retain source citations, binding/model/driver revisions, requested transfer bytes,
returned bytes/status, deadline and timing observations, and backend identity. Physical
verification requires an authorized connected assembly: confirm supply and idle levels,
then capture START/repeated START/STOP, ACK/NACK, actual SCL and edge timing with suitable
instruments. Separate a valid bus transaction from device identity, data freshness, and
measurement accuracy. Source/model/native/QEMU results are not hardware evidence.

## Primary references

- [NXP UM10204, Rev. 7.0](https://www.nxp.com/docs/en/user-guide/UM10204.pdf):
  §3.1 protocol/addressing, §6 timing/electrical limits, §7 pull-up design.
- [Linux I²C userspace interface](https://docs.kernel.org/i2c/dev-interface.html):
  address conventions, adapter capabilities, and combined `I2C_RDWR` operations.
- [smbus2 upstream documentation and examples](https://github.com/kplindegaard/smbus2):
  `i2c_msg`, `i2c_rdwr`, and SMBus API distinctions. Pin the actual project version.
