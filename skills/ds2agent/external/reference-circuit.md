# Reference-circuit recommendation

Use this guide to turn source-verified device requirements into a reviewable circuit,
not to infer wiring from a bus name or a behavior-model default. The output is a
pin-complete JSON net list and BOM with traceable design decisions, plus a rendered
schematic through the [KiCad workflow](tools/kicad.md) when requested. A schematic
render is not evidence that a board has been assembled, powered or measured.

## Establish the assembly scope

Follow [aggregation](../aggregation.md): co-locating several devices in one MCP package
does not connect their pins or merge their electrical requirements.

- **Standalone recommendation:** describe one device's required supplies, ground
  references, interface connector, strapping, reset/enable and passives. A named target
  board requires its verified board revision, schematic and pin capabilities. If no
  board binding exists, expose interface requirements at a connector without inventing
  MCU pins, regulator capability or shared nets.
- **Topology-provided assembly:** use the supplied net ownership, board/module revisions,
  power sources, connectors, other devices and adapter connections. Only then combine
  rails/buses, assess address/CS conflicts and account for already-fitted components.
  Do not silently invent a shared bus, common rail or common ground across isolation.
- **Incomplete inputs:** identify each unresolved requirement and withhold the affected
  wiring or component decision. A conditional proposal is not an assembly-ready net
  list. Never choose a convenient pin/address/resistor to conceal missing evidence.

Required inputs are the exact orderable part/package, current applicable datasheet and
errata, selected operating modes and environment, board/module schematics where used,
interface/backend requirements, and the intended power and physical topology. Retain
source identity/revision and section/page for every extracted requirement.

## Derive the operating envelope before wiring

Separate three kinds of information in the canonical device/project records:

1. **Source facts:** recommended operating ranges, electrical/timing guarantees and
   their test conditions, pin definitions and required application circuits.
2. **Project choices:** nominal rails, tolerances, bus speed, pin assignments, selected
   components and engineering calculations. Cite the facts used to justify each choice.
3. **Observations:** actual component/board identity and measured results, available
   only after authorized physical work. An assumed rail is not a measured rail.

Normal operation must stay within the applicable **recommended operating conditions**
and the conditions under which the required behavior is specified. Absolute maximum
ratings are separate damage/stress constraints, not a wider usable operating range.
Also check them for startup, shutdown, overshoot, undershoot and fault scenarios;
remaining below an absolute maximum does not imply correct operation.

Intersect the source-derived device envelope with the MCU/adapter, regulator, level
translator and passive limits. Include supply tolerance/ripple, load transients,
temperature, current budget and power sequencing. A behavior model may support a
narrower range, but it must not extend the physical operating range or invent missing
limits. An incompatible binding is refused; an unknown limit is evidence-missing,
not assumed safe.

## Build a pin-complete connection plan

| Area | Required decisions and checks |
| --- | --- |
| Supplies and returns | Assign every supply pin to its documented domain; include analog/digital/IO/reference supplies and exposed-pad requirements. Account for current and sequencing. Do not merge domains because their nominal voltages match. |
| Grounds | Connect returns as required by the actual device/layout guidance; document intentional analog/digital bonds or isolation barriers. Ground is a reference/return, not an interchangeable positive supply domain. |
| Decoupling | Provide the required capacitors for each relevant pin/domain, their return endpoints and placement constraints. Record capacitance, effective value, tolerance, voltage rating and technology constraints; copy neither a universal capacitance nor a convenient example layout. |
| Address/mode straps | Cite the truth table, sampled time, allowed levels and internal pulls. Select an explicit state; check combined address uniqueness only for a supplied shared topology. Do not leave required straps floating. |
| Reset/enable/boot | Record polarity, default state, voltage domain, pull requirements and timing relative to power/clock. An RC delay is not a proven reset generator without thresholds/tolerance analysis. |
| Bus/control lines | Verify direction, output type, pin mux, inactive state, logic thresholds, clock/timing limits, pull-ups, CS/interrupt ownership and startup behavior. Identify a real host controller/HAL/bridge implementation. |
| Unused/reserved pins | Follow the exact package's NC, DNC, reserved and unused-input instructions; they are not synonyms. Do not connect an NC or exposed pad by convention alone. |
| Connectors/protection | Record connector orientation/pin numbering, cable/reference connections and any source-required protection or translation. An adapter's power pin is not automatically a permitted power source. |

Pin numbering must come from the selected package drawing, not a different package's
diagram or an unverified symbol. Cross-check symbol pin numbers, footprint pad numbers,
package orientation and exposed pads. A verified library footprint still does not
determine a circuit's required passive values.

## Bus compatibility and passive selection

Use the matching protocol guide:
[I²C](interfaces/iic.md), [SPI](interfaces/spi.md),
[UART](interfaces/uart.md), or [1-Wire](interfaces/one-wire.md).
Check output-high/low guarantees against receiver thresholds under the relevant load,
pin operating-voltage and power-off limits, and whether the selected translator handles
the directionality and speed. “Same nominal voltage” does not complete that analysis.

- **Open-drain pull-ups:** inventory board/module/adapter pull-ups and calculate their
  parallel effective resistance. For I²C, NXP UM10204 §7.1 bounds pull-ups by sink
  capability and rise time/bus capacitance; account for the weakest participant,
  voltage and resistor tolerances, leakage and the actual bus mode. For 1-Wire, also
  analyze recovery and operation-specific strong-pull-up power requirements using
  the selected device/master datasheets. There is no universal resistor value.
- **Strap/bias resistors:** derive the required state against documented internal
  pulls, leakage, thresholds, sampling time, tolerances and power-off conditions.
  A direct rail connection is appropriate only where permitted; series resistance
  is not automatically a valid substitute for voltage translation.
- **Decoupling/bulk capacitors:** start with vendor-required value/range and layout,
  then check effective capacitance over bias/temperature/tolerance, voltage margin,
  ESR requirements and regulator stability/inrush constraints. Do not add capacitance
  indiscriminately to a regulator or timing node.
- **Series/termination/filter parts:** include only with a cited requirement or a
  recorded engineering calculation appropriate to driver, edge rate, line impedance
  and loading. Do not apply a fixed “SPI resistor” to every bus or load clocks/data
  with arbitrary capacitors.
- **BOM realization:** select actual component ratings, package, tolerance and assembly
  population. A datasheet value or calculation can justify a nominal choice, while
  the component vendor datasheet establishes that the chosen part satisfies it.
  Keep required, optional and not-populated alternatives explicit and nonconflicting.

For every value record either the exact source requirement or the inputs, equation,
assumptions and resulting acceptable range. If no defensible range or part can be
derived, leave the design explicitly unresolved rather than filling in a familiar value.

## Deliver the net list, BOM and validation record

Produce structured JSON with the following information; this is an output contract,
not a filled circuit for an unspecified chip:

| Record | Required content |
| --- | --- |
| Assembly | Scope (`standalone` or supplied topology identity), revision, selected modes, source/model/binding identities, assumptions and unresolved decisions |
| Components/BOM | Unique reference, manufacturer/part/package, value with units, ratings/tolerance, footprint/library provenance, fitted/DNP state and quantity |
| Pins | Component reference plus physical pin number and name, electrical role/domain, assigned net or explicit datasheet-justified no-connect |
| Nets | Unique net identity, complete endpoint list, intended domain/voltage and ownership; passives have both terminals assigned to nets, not merely a label “cap on VDD” |
| Requirements/decisions | Source URL/document/revision/section/page, extracted constraint, chosen implementation, calculation references and validation status |
| Constraints | Required placement/return-path, sequencing, bus/power limits and connector orientations not captured by connectivity alone |

The validation record must cover:

1. Every physical pin accounted for exactly as the datasheet requires; no missing
   power pins, shorts caused by aliases, unconnected required inputs or accidental
   junctions. All endpoints resolve to existing component pins.
2. No unintended multiple push-pull drivers, unsupported domain crossings or
   back-power paths. Reconcile rail/load budgets and source ownership; do not connect
   board USB power, external supplies and adapter rails together without a verified
   power-path design.
3. For a supplied topology, reconcile duplicate addresses, CS assignments, shared
   pull-ups, pin mux conflicts, boot/reset behavior and fitted module components.
   Standalone proposals must not claim these assembly checks passed.
4. BOM quantities agree with populated references, values/ratings meet the calculated
   requirements, and symbol-to-footprint/package mapping is verified. Schematic
   rendering and electrical-rule checks can reveal consistency errors but do not
   establish datasheet compliance, PCB layout quality or electrical performance.
5. State exactly which checks were source/manual reviews or executed tools, preserving
   their evidence. Generating/running tools or code requires explicit execution
   authorization (`--allow-code-execution` or host equivalent); do not silently install
   tools, generate firmware, power hardware or flash a target.

Keep the canonical device facts intact: topology-level choices belong in project
bindings, and observations must not overwrite source facts. Shared buses, GPIOs, power
controls and probes require serialized ownership across device tools in the
[single-MCP runtime](../aggregation.md).

## Physical verification boundary

A deterministic circuit/behavior model can check declared connectivity, values, limits
and modeled transactions. It cannot determine actual assembly, solder quality,
capacitor placement, parasitic coupling, ground bounce, thermal margin or calibration.
Native fake-HAL and QEMU do not close that gap.

After explicit hardware authorization, a measurement plan should identify the exact
assembly/BOM revision, instrument/probe/reference connection, test points, source-derived
acceptance limits, loading, uncertainty, environment and finite stop conditions. Review
the power/ground/isolation arrangement before connecting any supply, adapter or grounded
instrument; an unknown reference is not permission to attach a scope ground clip.
Check unpowered continuity and polarity appropriately before controlled power-up.

Measure actual supply/IO levels and startup/reset sequencing, then the relevant bus
edges, timing, contention and high-current intervals; capture thermal or analog behavior
only when that scope is requested and the setup supports it. A logic decode alone does
not establish voltage margins, and a clean schematic or ERC result is not a measurement.
Retain raw captures, instrument/setup details, measured conditions and deviations.
Mark unperformed physical checks `not-run`; never synthesize readings or label a
simulation as physical verification or calibration.

## Primary references

- [TI SZZA036C: Understanding and Interpreting Standard-Logic Data Sheets](https://www.ti.com/lit/an/szza036c/szza036c.pdf):
  §§3.2–3.6 and 4–5 distinguish package/pin facts, absolute maximum ratings,
  operating conditions and logic compatibility; §§8–9 discuss supply/layout context.
- [NXP UM10204, Rev. 7.0](https://www.nxp.com/docs/en/user-guide/UM10204.pdf):
  §§6–7 electrical/timing constraints and pull-up calculations for I²C.
- [ADI DS2482-100 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/DS2482-100.pdf):
  an example showing distinct upstream I²C and downstream 1-Wire electrical/power
  requirements. It is not a universal reference circuit for unrelated parts.

These general references explain the review method. Every concrete device, board,
regulator, translator and passive choice still needs its own applicable primary source.
