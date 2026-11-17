# Tool selection and minimal wrappers

A datasheet MCP tool is a reusable operation a user can run on a device, tagged with the
device model it serves (`knowledge`, `driver`, `behavior`). Selection decides which
operations are worth exposing; wrapping decides how they bind to documented content and how
little generated code stands between the caller and that content.

## Selection by model

Choose a tool when it is independently useful on new inputs, not merely an incidental step
in one example flow.

**knowledge** — cited retrieval over facts:
- `retrieve(query)` → cited fact list; `ask(question)` → cited answer or deterministic
  refusal; `tutorial(topic)` → cited step-by-step procedure.
- Facts are organized by the six categories (communication, power/supply, functional,
  timing, electrical/interference, reliability/environment) and merge only same-category,
  same-claim facts.

**driver** — device operations and the derived C driver:
1. Identity and lifecycle — chip-ID read, soft reset, status polling, power-mode switch.
2. Register access — typed read/write of a documented control/status register, with named
   bit fields and documented value ranges.
3. Configuration — a documented setting group (oversampling, filter, standby, address) with
   validated enum values and the exact register bits it writes.
4. Measurement — raw ADC readout (burst) and each documented compensation/transfer formula
   producing physical units.
5. Driver export — `export_driver` renders the portable C driver (header + source) from the
   register map and verified formulas.

**behavior** — the finite, parameterized device:
- `get_parameter(name, condition)` → `{min, typ, max, unit, condition, source}`;
  `evaluate_transfer(name, input)` → result plus applicability domain;
  `get_register_model()` → register map; `list_states()` → declared state transitions;
  `refine(targets, report)` → versioned, hash-bound refinement of the mutable layer
  (see feedback.md).

**reference-circuit (cross-cutting)** — `recommend_reference_circuit(requirements)` and
`recommend_wiring(device, board)` produce a datasheet-grounded net list (supply decoupling,
bus pull-ups/pull-downs, address/mode strapping, reset/enable); see
`external/reference-circuit.md`.

Merge duplicates (e.g. two "read temperature" paths), keep incidental arithmetic internal,
and do not let register names dictate tool boundaries: one tool may span several registers
when the datasheet defines a combined operation (a burst read + compensation). A register
that only appears as an implementation detail of another operation stays internal.

## Binding

Every tool must bind to a concrete, citable source:

- a register address and its bit fields (with the datasheet section),
- a documented formula (compensation, transfer function, conversion),
- a documented init/measurement sequence, or
- an interface procedure (I2C read/write, SPI transfer) with its documented timing **and
  transaction structure** (single vs split transaction, STOP / chip-select placement).

For devices with a status/ready byte or command/reply framing, the wrapper must encode the
documented polling and atomicity semantics (not-ready → STOP and retry; ready → continue the
same transaction; early STOP → lost frame), each bound to its datasheet section. A generic
"poll status then read" idiom is not a substitute for the sourced framing rule.

Prefer the datasheet's own algorithm. If the datasheet ships a reference API/example code
(Bosch Sensortec `bmp280_*`, a vendor SDK), bind to that code rather than re-deriving it.
Do not invent algorithms, coefficients, or register addresses to fill gaps; mark such an
operation `blocked`/`excluded` with a reason instead.

## Minimal wrappers

Generated wrappers contain only:

1. input validation (types, enum membership, documented value ranges, address width),
2. the bound register/interface call or formula, and
3. useful output serialization (typed return, named fields, units).

They do not contain benchmark recomputation, logging frameworks, retry policies beyond what
the datasheet documents, or simulation scaffolding. Hard-coded values (register addresses,
masks, defaults, coefficients) must be parameterized or derived from the documented source,
never copied in as unexplained magic numbers: every such literal carries a source comment
(`# datasheet §4.3.4 ctrl_meas, bits [1:0] mode`).

Parameter schema comes from the documented semantics: an enum parameter lists the datasheet's
valid encodings; a numeric parameter states its range and unit; an address parameter states
its width and byte order. Return values state units and resolution (e.g. `temperature_c` with
resolution `0.01 °C`, `pressure_pa` in `Q24.8` or converted `Pa`/`hPa`).

## Reference execution

Before implementation, run the bound reference computation with documented inputs and record
the output. For a compensation formula, feed the datasheet's example coefficients and ADC
values (when given) and record the result; otherwise derive coefficients from a documented
register reset/default set and record the result as the reference. For a register read,
record the documented reset value. These records become the verifier's ground truth.
