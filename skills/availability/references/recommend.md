# Availability — recommend (function → part)

Turn a free-text functional requirement into a ranked part list with purchase links.

## 1. Parse the requirement into structured specs

Extract, when stated: function/category, interface (I²C / SPI / UART / 1-Wire / analog),
supply voltage, package/footprint, precision / resolution / range, temperature grade,
compliance, quantity, region, budget. Record what was **not** stated as open — do not
invent it.

## 2. Map the function to a part category

| Requirement | Category / example families |
|---|---|
| temperature / humidity | environmental sensor — SHT3x, HDC20x, AHT2x |
| pressure | barometric sensor — BMP2xx/BMP3xx/BMP5xx |
| acceleration / gyro | IMU — MPU-6xxx, ADXL3xx, LSM6DSx |
| current / voltage / power | power monitor / ADC — INA2xx, ADC1xxx |
| load-cell bridge | 24-bit weigh-scale ADC — HX711-class |
| serial memory | EEPROM — AT24Cxx / 24LCxx |
| GPIO expansion | I²C I/O expander — PCF8574/PCF8575, MCP230xx |
| DAC output | 12-bit DAC — MCP4725-class |
| I²C channel mux | I²C mux — PCA9548A-class |
| real-time clock | RTC — DS3231-class |
| NFC reader | NFC controller — PN532-class |
| magnetometer | 3-axis mag — QMC5883L, LIS3MDL |

## 3. Candidate discovery (in order)

1. The project's own device knowledge (datasheet2agent device list) for known-good families.
2. Distributor parametric search (Digi-Key / Mouser category filters, LCSC category).
3. `web_search` for the function + interface + vendor.

## 4. Rank

Rank by, in order: spec match → availability in the target region → standards compliance →
price → lead time. State the ranking basis; never claim "best" without it.

## 5. Output

Emit the shared output contract with `kind: "recommend"`. For each candidate include:

- an LCSC **and** a Mouser link where the part is carried,
- one cited spec basis line per candidate (datasheet category / feature or a listing row),
- the standards the candidate actually satisfies.

If the requirement's standards cannot be satisfied by any candidate, say so explicitly
instead of dropping the filter.
