# SPI

Use this guide when a device's datasheet defines an SPI command interface. Conventional
four-signal SPI uses SCLK, controller output/peripheral input (MOSI/COPI), controller
input/peripheral output (MISO/CIPO), and chip select (CS), plus a ground reference.
Three-wire shared-data and dual/quad interfaces are different capabilities, not automatic
features of a four-wire backend. SPI specifies no universal register-command format.

## Bind the device, not just a bus number

Record the following in the owning device's canonical project binding under
[aggregation](../../aggregation.md):

- Exact part/package, datasheet revision and command/timing sections.
- Board/adapter identity; MCU peripheral, alternate-function pins and HAL version, or
  stable native-host device path and controller driver, or implemented bridge version.
- SCLK/MOSI/MISO/CS pin mapping, CS polarity and controller/GPIO ownership; voltage
  domains, reset/enable states, and other participants sharing the wires.
- CPOL/CPHA mode, bit order, bits per word, supported clock range, and CS setup/hold,
  inactive interval, inter-word gaps, and any maximum transaction duration.
- Command/address framing, dummy **clocks** or bytes, expected RX length and payload
  offset, auto-increment/page behavior, transaction boundaries and ready/busy rules.
- Shared board/bus/CS lock identities, finite transfer/operation deadlines and supported
  transfer lengths. A numeric CS index does not establish a connector pin mapping.

Unknown mode, voltage, CS behavior, or packet framing blocks physical access. Validate
the [reference circuit](../reference-circuit.md) before choosing pins.

## Clock and chip-select contract

| Mode | CPOL: idle SCLK | CPHA: sample edge |
| --- | --- | --- |
| 0 | Low | First/leading edge |
| 1 | Low | Second/trailing edge |
| 2 | High | First/leading edge |
| 3 | High | Second/trailing edge |

The other edge is normally used to change data. Select the mode from the device's
timing diagram, not from a successful-looking byte. Establish the correct idle clock
before asserting CS. Bit order and word size are independent of mode.

CS often frames one complete command but may have device-specific latching behavior;
deassertion does not universally mean “burst read complete.” Some commands latch on
CS release, some require a subsequent busy wait, and some interfaces use other framing.
Honor the selected device's polarity and all setup/hold/inactive times. Keep unrelated
devices deselected, including during controller startup and reconfiguration.

On a shared bus, each conventional target needs an independently controlled CS and must
release MISO when not selected. Verify that property for the actual target/module;
do not assume all boards tri-state MISO. Daisy chains, shared-CS designs, and three-wire
turnaround require an explicitly documented topology. Check MISO release timing before
selecting the next device. Multiple active push-pull outputs are a contention fault.

## Full-duplex transfers and command boundaries

For every clocked word, conventional four-wire SPI simultaneously transmits and receives.
A “read” must therefore transmit something to generate clocks. Construct the complete
wire image from the device protocol:

1. Assert CS and satisfy its setup time.
2. Clock command/address words. Retain RX for diagnostics but treat those positions as
   undefined unless the datasheet assigns them meaning.
3. Clock the required dummy interval and payload interval using documented safe TX
   contents. A dummy interval may be a non-byte number of clocks; do not round it or
   assume the adapter can express it.
4. Extract only the documented payload slice; verify status/CRC/identity if available.
5. Satisfy final clock/CS hold time, release CS, then observe required inactive or busy time.

This is a sequence template, not an invented register protocol. Read/write flag bits,
address byte order, dummy content and allowed pause lengths all come from the device.
A generic `transfer(write_buf, read_len)` abstraction is insufficient unless it defines
the exact clock count, transmitted fill, RX offset and CS behavior.

**Native host:** Linux spidev's separate `write()` and `read()` calls deactivate CS
between operations. Use a correctly constructed `SPI_IOC_MESSAGE` for a composite
transaction that must keep CS asserted. With upstream Python spidev, `xfer2(tx_words)`
is the documented held-CS transfer API; record the installed version and controller
support. `writebytes2`/`xfer3` may split large data into multiple operations: do not
assume they preserve a device's required uninterrupted transaction. Reject oversize
commands or use an explicitly verified backend strategy.

**MCU HAL:** a transmit/receive or segmented transfer must preserve the same wire image
and CS interval. Check hardware NSS behavior; it may pulse between words rather than
provide the required command-level CS. If software-controlled CS is used, one owner
must control it and release it safely on all exit paths. Bound DMA/interrupt completion
and retain transfer errors instead of treating a completed callback as valid device data.

**Bridge:** pyserial or a debugger's virtual COM port does not generate SPI by itself.
A PC-to-MCU route needs implemented, identified firmware and a versioned protocol that
can carry mode, framing, complete transaction, status, and finite deadlines. Without
that implementation, document the route as unavailable. Linux spidev is not a generic
Windows COM-port API.

## Ownership, failures, and evidence

Serialize controller settings and the whole CS-framed operation across all devices
using that controller. A longer command/busy/readback sequence may also need a device
lock. Do not hold CS during arbitrary host scheduling delays when the device bounds
gaps; host GPIO toggles are not a hard real-time guarantee. If the underlying synchronous
API has no cancellable timeout, require a bounded driver/worker strategy rather than
claiming a caller deadline cancels physical I/O.

SPI has no generic low-level ACK. All-zero/all-one RX, or successful host transfer
completion, does not prove presence or register validity. Check a documented identity,
status, CRC, or reversible readback where available; do not invent a universal probe.
Retries can repeat side effects. Apply only a documented, bounded recovery policy.

Deterministic models can evaluate command decoding, RX alignment, register state,
CS boundaries and modeled busy/error behavior. They cannot verify MISO tri-state,
voltage compatibility, actual clock rate, setup/hold margin, or ringing. Native fake-HAL
execution and QEMU are also not physical verification.

Retain binding/driver/model revisions, backend/version, mode/clock requests, TX/RX bytes,
payload offsets, CS segments, timeouts and interpreted status. Authorized hardware
checks should capture CS/SCLK/MOSI/MISO and measure actual levels, clock and boundary
timings; a logic-analyzer decode alone does not establish analog signal integrity.
Do not claim sensor accuracy or calibration from a valid SPI exchange.

## Primary references

- [Linux SPI userspace API](https://docs.kernel.org/spi/spidev.html): mode flags,
  full duplex, CS continuity, transfer limits, lack of low-level ACK and clock reporting.
- [Python spidev upstream](https://github.com/doceme/py-spidev): `xfer`/`xfer2`/`xfer3`,
  version-dependent configuration and controller support.
- [TI SCEA065B, §2.2 SPI](https://www.ti.com/document-viewer/lit/html/SCEA065B/GUID-10A34DDF-5227-4165-954A-A91D2F1D7F3E):
  signal directions and voltage-translation context. Device timing remains datasheet-specific.
