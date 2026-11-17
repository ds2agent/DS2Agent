# KiCad: source-grounded example schematics

Use KiCad to deliver an editable, reviewable example circuit and rendered schematic/BOM.
It does not validate a driver, replace the datasheet, or turn an example into a
production-ready electrical design. Start with the grounded
[reference-circuit workflow](../reference-circuit.md) and selected [board profile](../boards/).

## Fix inputs and version before drawing

Record KiCad major/minor version and symbol/footprint-library revisions. The CLI
templates below use the **KiCad 9.0 manual**; options, schematic formats and BOM
workflows differ in other versions. Do not rewrite a schematic's version token to
pretend compatibility. Open/save with the intended release and record an actual
validation result only when authorized and exercised.

Require the exact device/package, datasheet revision and pin table, MCU/connector pin
mapping, recommended operating supplies, logic thresholds, bus topology and cited
reference circuit. Keep a source binding for every connection and component choice.
Missing information is an explicit unresolved design input, not license to invent a
pin, resistor, capacitor, level shifter, regulator or footprint.

## Construct a real connected schematic

1. Match symbol pin **numbers** and functions to the selected package's pin table,
   including supply domains, exposed pad, reset/address/strap pins and documented NC/DNC
   distinctions. Library name similarity is insufficient; retain pin-map review.
2. Show MCU/board connector pin numbers, shared ground, supply source and all
   recommended decoupling/bias/strap networks with source-derived values and ratings.
   Same-domain supply pins must follow the documented rail arrangement; never collapse
   different supply domains just to match a behavioral model.
3. Review I/O thresholds and tolerance, power sequencing, back-power paths, bus pull-ups,
   open-drain versus push-pull behavior, loading and required level translation. Use
   recommended operating conditions, not absolute maximum ratings as normal supply limits.
4. Use actual wires/junctions/net labels attached at electrical pins. Graphical lines,
   nearby text and visually crossing wires are not reliable connectivity evidence.
   Give references and nets unambiguous names across hierarchical sheets.
5. Verify any footprint against an approved library revision or package/land-pattern
   drawing, including pad numbers, orientation and exposed-pad treatment. A schematic
   symbol or attractive 3D image does not establish a manufacturable footprint.

For generated `.kicad_sch`, follow the official s-expression format, valid UUIDs,
embedded library-symbol definitions and instance paths. Use a generator identifier
other than `eeschema`; do not misrepresent generated output as KiCad-authored.
There is no general `kicad-cli` command that invents a schematic from a datasheet.
Keep the editable source and local libraries with portable relative references.

## ERC, exports and review

These are **unexecuted KiCad 9 templates**, with project-owned inputs and writable
output paths. Record `kicad-cli version` and consult each subcommand's `--help` for
the installed release before execution.

```text
kicad-cli sch erc --format json --severity-all --exit-code-violations -o reports/erc.json example.kicad_sch
kicad-cli sch export pdf -o reports/schematic.pdf example.kicad_sch
kicad-cli sch export bom -o reports/bom.csv example.kicad_sch
```

In the documented 9.0 ERC contract, `--exit-code-violations` returns 5 for violations
and 0 when none are found; retain the report and distinguish violations from load/tool
errors. Review warnings and exclusions, not only exit status. Fix real connectivity
and pin-type problems instead of hiding them with blanket exclusions, changed pin types,
or indiscriminate `PWR_FLAG` symbols. Use power flags only for a reviewed real power
source that ERC cannot infer.

Visually inspect rendered pages for missing symbols, off-grid/disconnected wires,
clipped labels and ambiguous net names. Inspect BOM fields, quantity/grouping, DNP
status, selected part/package and footprint; default exports may omit project-specific
manufacturer fields. Exporting a PDF/BOM does not run ERC. A PCB, if separately requested,
also requires footprint/layout review and DRC; schematic ERC is not PCB DRC.

## Limits and evidence

ERC checks configured pin/net rules; it cannot prove resistor values, analog stability,
decoupling effectiveness, signal integrity, thermal margin, current consumption,
real voltage tolerance, timing or calibration. Even an ERC-clean circuit needs
datasheet-based engineering review and authorized physical validation.

Record source/pin/net review, KiCad/library versions, editable-artifact hashes,
actual export/ERC argument vectors, bounded subprocess exit/timeout status, reports,
reviewed exceptions and unresolved limitations. No automatic KiCad/library installation,
plugins or scripts. Tool execution requires `--allow-code-execution` or host-equivalent
approval; generated circuits are not permission to energize hardware.

## Primary references

- [KiCad 9.0 CLI reference](https://docs.kicad.org/9.0/en/cli/cli.html):
  schematic ERC, PDF/BOM export and version commands.
- [KiCad 9.0 Schematic Editor manual](https://docs.kicad.org/9.0/en/eeschema/eeschema.html):
  electrical connectivity, power symbols, ERC and BOM review.
- [Official schematic file format](https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/):
  version/generator, symbols, UUIDs and hierarchical instances.
