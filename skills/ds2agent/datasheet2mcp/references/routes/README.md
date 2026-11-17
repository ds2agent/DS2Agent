# Interface routes

Route selection is by the device's digital interface, read from the datasheet. All routes
share selection, source binding, agent independence, and completion requirements; they differ
only in transport.

| Route | Interface | Transport adapter | Typical tools |
|---|---|---|---|
| `i2c` | I²C | `smbus2` (7/10-bit, clock) | `read_register`, `write_register`, `burst_read`, `read_chip_id` |
| `spi` | SPI (3/4-wire) | `spidev` (CS, mode, clock) | `transfer`, `read_register`, `write_register` |
| `uart` | UART | `pyserial` (baud/bits/parity/stop) | `send_command`, `read_response` |
| `onewire` | 1-Wire | `pyserial`/onewire driver | `reset_pulse`, `read_rom`, `read_scratchpad` |
| `none` | no bus / register-model only | fake transport | register + behavior tools only |

The adapter is the only module that imports the bus library. Register tools call the adapter
through typed `read_register`/`write_register`/`burst_read` helpers, so the same tool runs
against the fake transport in verification and the real bus at runtime.

Record the chosen route and its parameters (address, clock, CS, baud) in
`.pipeline/route.json` and in `manifest.json`.
