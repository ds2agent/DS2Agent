# UART (serial)

Use this guide for a device with an asynchronous serial command or streaming protocol,
or for the serial **transport** of an implemented MCU bridge. UART supplies character
framing, not an application message protocol. A sensor need not reply to commands;
it may stream unsolicited records, echo bytes, or remain silent until enabled.

## Required project binding

Store the binding with the owning device's canonical records, following
[aggregation](../../aggregation.md):

| Area | Record before access |
| --- | --- |
| Identity/route | Exact device and datasheet revision; board/adapter identity; port identity or MCU UART/pins/HAL; bridge firmware/protocol version if applicable |
| Character format | Baud, data bits, parity, stop bits, inversion, flow control and supported host/MCU combinations |
| Electrical | Logic-level UART vs RS-232 vs RS-485, voltage domains, connector pinout/direction, grounding/isolation, transceiver and direction control if present |
| Message protocol | Binary/text encoding, sync/delimiter, length interpretation, byte order, escaping, checksum/CRC, command/reply matching and unsolicited-frame rules |
| Bounds | Maximum frame/buffer length, read/write/operation deadlines, inter-character gap rules, finite resynchronization and poll limits |
| Ownership | Shared physical port/board lock, device addressing if defined by the application protocol, and RTS/DTR startup behavior |

There is no default device baud or universal command terminator. Document the target's
actual settings; do not copy host-library defaults as datasheet facts.

## Wiring and character framing

- For a nonisolated, compatible logic-level link, connect one endpoint's TX to the
  other's RX with an agreed reference ground. Verify actual connector directions;
  labels may be from the adapter's or target's perspective. Do not connect two TX
  outputs together or assume an adapter's power pin is safe to connect.
- MCU UART logic pins are not RS-232 pins. RS-232 uses different electrical levels
  and normally requires a suitable transceiver. RS-485 is a differential physical
  interface requiring its own transceiver/topology/direction rules. A USB “serial”
  connector does not identify which electrical interface is exposed. Never connect
  an unknown or RS-232-level output directly to MCU GPIO.
- Compare guaranteed output levels, receiver thresholds, supply/pin limits and
  power-off behavior in both directions. “3.3 V board” or “5 V tolerant” is not
  sufficient evidence for a particular pin and operating state. Use a verified level
  translator or isolated interface where needed; see [circuit design](../reference-circuit.md).
- A conventional noninverted UART character has idle high, a low start bit, data
  bits, optional parity, and stop bit(s). Both ends must agree on format and baud.
  Some MCUs support 9-bit modes, but pyserial's documented data-bit choices are
  5–8; a 9-bit application cannot be advertised through ordinary pyserial bytes
  without an explicitly supported encoding/backend.
- Enable RTS/CTS or software flow control only when both ends and the wiring support
  it. XON/XOFF processing can consume bytes that a binary protocol intends as payload.
  Opening a port can glitch RTS/DTR and reset or boot-select some boards: review that
  connection and the adapter/driver behavior before opening it.

## Select the actual transport

**Host serial:** pyserial opens an OS serial endpoint such as a configured COM port or
device path. Identify the physical adapter, not merely the first enumerated port.
Record OS, driver and pyserial versions, and supported framing/baud. No installation,
port opening, or generated-code execution is implied by this guide.

**MCU UART:** bind transmit/receive, DMA or interrupt operations to the selected HAL
and board. Handle overrun, framing/parity errors, RX ring-buffer overflow and finite
completion deadlines. USB CDC on an MCU is a USB endpoint and does not automatically
prove that a hardware UART at the requested baud is configured behind it.

**Serial bridge for another bus:** distinguish the outer serial frame from the inner
I²C/SPI/1-Wire transaction. Identify implemented firmware, protocol version, operation
IDs, lengths, request/reply correlation, target routing and error codes. Bare pyserial
does not implement those buses. If bridge firmware/backend is absent, the route is
unsupported; do not present a proposed packet format as working hardware support.

## Parse a stream, not a read call

For a request/reply protocol, execute the following within the shared-port owner:

1. Encode the documented command exactly, including byte order, escaping, length and
   checksum. Text encoding and line endings must be explicit. Check the number of
   bytes written and distinguish a write timeout from a device response timeout.
2. Set finite pyserial `timeout` and `write_timeout`. `timeout=None` waits indefinitely;
   `read(n)` with a finite timeout may return fewer than `n` bytes. Bound the whole
   operation with a monotonic deadline; resetting the same timeout on every partial
   read must not extend it indefinitely. Inter-byte timeout alone is not that deadline.
3. Append received chunks to a bounded persistent buffer. One read may contain half
   a frame or several frames; keep incomplete tails and consume all complete records
   according to the application protocol.
4. For length-framed messages, validate the length against a maximum before collecting
   or allocating its body. For delimiters, honor escaping/quoting and maximum length.
   `read_until(expected, size)` can stop on timeout or size without finding the
   delimiter, so explicitly validate the terminator rather than accepting any return.
5. Validate framing, declared length, message type/address/correlation where defined,
   checksum/CRC and status before decoding a value. Route valid unsolicited frames
   separately; they are not automatically the reply to the current command.
6. On malformed data, use the protocol's finite resynchronization rule and bounded
   discarded-byte count. Preserve partial data/error context on timeout. A timeout
   means no complete valid matching response within the deadline, not proof of absence.

Do not clear the RX buffer before every command: it can discard a delayed valid reply
or unsolicited data. A deliberate parser reset belongs to an explicit recovery rule.
pyserial `flush()` waits for outgoing data; it does not mean “discard received noise.”
A successful write/flush is not an application-level acknowledgement.

For unsolicited streams, maintain the same bounded parser without inventing a command
phase. Record sequence numbers, timestamps and loss indicators only when supported;
do not manufacture them as device-originated fields. Retrying a command may repeat a
side effect, and a late reply may belong to the earlier request.

## Ownership and evidence boundaries

One reader/parser owns a physical stream. Multiple MCP device tools must not independently
consume the same COM port; serialize request/reply transactions and demultiplex only
when the documented protocol provides a safe way. A process-local mutex does not exclude
a terminal program or another service. Use the [single integrated runtime](../../aggregation.md)
and explicit external ownership; pyserial's exclusive-open option is platform-dependent,
not a universal lock.

Deterministic models can exercise fragmentation, combined frames, checksums, bounded
buffers, delayed responses and documented device states using a controlled clock/input.
They do not measure oscillator error, voltage levels, cable noise, physical baud, USB
latency, or sensor accuracy. Retain raw TX/RX with timestamps, parser outcomes, complete
format/binding, versions and deadlines; label injected input as model evidence.

Authorized physical checks should verify electrical levels first, then capture character
format/actual timing and complete command/reply or streaming behavior on the real
connection. A host loopback tests a different path from the target device. Native fake-HAL
and QEMU execution are not physical validation or calibration.

## Primary references

- [pyserial API](https://pyserial.readthedocs.io/en/latest/pyserial_api.html):
  supported framing, timeout/short-read semantics, `read_until`, write/flush,
  exclusive mode and RTS/DTR opening caveats. Pin the project's installed version.
- [TI SCEA065B, §2.3 UART](https://www.ti.com/document-viewer/lit/html/SCEA065B/GUID-C048AD3E-026C-41DB-A0F6-4784E2B39EEF):
  character framing, UART logic levels, and the distinction from RS-232/RS-485.
