# Example: SHT30 formula-only transfer evaluator

This example illustrates raw-word conversion, **not** a stateful sensor emulator. The formula
excerpt is attributed to the Sensirion SHT3x-DIS datasheet, but this example does not establish
its revision/page citation or report source verification. A generated delivery must bind
these equations and their applicability conditions to the actual ingested source before
claiming source-verified evidence.

## Formula excerpt and arithmetic domain

- T[°C] = −45 + 175 · S_T / 65535.
- RH[%] = 100 · S_RH / 65535.
- S_T and S_RH are unsigned 16-bit raw words for these illustrated conversions.

These happen to be affine formulas. Other devices' documented nonlinear, piecewise, or
fixed-point compensation must not be forced into this form.

The arithmetic endpoint S_T = 65535 maps to 130 °C. This is a mathematical result, not a
claim about physical operating range, accuracy, or sensor saturation.

## C temperature transfer evaluator

```c
#include <stdint.h>

float SHT30_Temperature_From_Raw(uint16_t raw_t) {
    return raw_t * (175.0f / 65535.0f) - 45.0f;
}
```

This function evaluates temperature only. It does not produce a six-byte sensor reply,
generate/validate CRC, decode humidity bytes, accept commands, reset state, or model time.
It is not native compiled-driver evidence. Floating-point checks require independently
derived reference values and an explicit sourced tolerance where exact comparison is
inappropriate; no test result is asserted here.

## Formula-only evaluation sequence

```json
[
  {"op": "evaluate_transfer", "name": "temperature", "input": 0, "expect": -45},
  {"op": "evaluate_transfer", "name": "temperature", "input": 65535, "expect": 130}
]
```

## Explicitly unmodeled scope

No address selection, measurement command, reply layout/CRC algorithm, ready/stale-data
behavior, reset behavior, or conversion delay is specified or verified by this example.
Requests for those operations must be refused as unmodeled, not answered by this formula.
A stateful emulator requires separately sourced command/reply/state/timing definitions;
native and optional QEMU execution require their own driver/harness/target evidence under
[../../external/tools/qemu.md](../../external/tools/qemu.md).

Evidence here is limited to the illustrated arithmetic. Source/model/native/qemu/hardware
verification has not been exercised by this document; no physical calibration is implied.
