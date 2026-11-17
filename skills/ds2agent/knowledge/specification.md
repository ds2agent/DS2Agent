# Knowledge model — extraction specification

Read the datasheet (MinerU Markdown) and extract five fact groups. Every fact cites its
source block (section/page + verbatim substring). If the datasheet does not state a value,
mark it `not_stated` — never infer it, and never merge facts across devices.

## 1. Basic functionality

- What the device does (sensing, actuation, memory, interface, ...) in one or two sentences.
- The primary measured/controlled quantities and their units.

## 2. Operating conditions

- Recommended operating ranges: supply voltage(s), temperature, and any domain-specific
  condition (pressure, frequency, ...), with min/typ/max where the datasheet gives them.

## 3. Absolute maximum ratings

- The "absolute maximum ratings" table: max voltage at each pin group, storage temperature,
  ESD, maximum pressure/stress. These are the immutable limits the behavior model enforces.

## 4. Functionality-specific parameters

- Per function: measurement range, accuracy/resolution, current consumption, noise,
  response/update rate, and the digital interface (I2C/SPI/UART/1-Wire) with its max clock.

## 5. Package

- Package name (LGA/QFN/LQFP/...), footprint dimensions, pin count, and marking.

## Conditional and protocol rules

Interface procedures are usually conditional, and the datasheet states them as two halves of
one paragraph. Extract **both branches** as separate facts, never only the half that contains
an explicit keyword (`STOP`, `retry`, `NACK`):

- The ready/affirmative branch **and** the not-ready/negative branch (for example "RDY=1 →
  read the whole frame before STOP" **and** "RDY=0 → STOP before retrying").
- Success and failure paths, and `before`/`after` ordering constraints.

A protocol fact is incomplete if its complementary branch is not also recorded; a one-sided
polling/status rule is a gap, not a completed fact.

## Table, image-OCR and qualitative extraction

Three extraction classes cause silent fact loss; handle each explicitly.

1. **Interleaved / `rowspan` / `colspan` tables.** MinerU often flattens a table into
   wrapped lines whose columns no longer line up visually, or into HTML `rowspan`/`colspan`
   cells. Map values by *row semantics* (parameter name + condition), not by visual column
   position. An unnamed continuation row inside a `rowspan` (e.g. the `TA = -25 C to 85 C`
   drift row under `Offset voltage vs Temperature`) is still a fact: attach it to its owning
   parameter, do not drop it. When a row cannot be resolved with confidence, record it as
   `not_stated` with the reason — never as a wrong value and never silently omitted.

2. **Image-OCR blocks.** Values that MinerU places in `<details><summary>image content</summary>`
   are first-class source text, not decoration. Numeric rows inside a figure/table OCR block
   (e.g. `SDV 0.2 V`, `PINT 100 us`, a resistor value on a reference-circuit figure) must be
   extracted with the same citation rigor as prose/table rows. Cite the figure/table and page,
   and note that the value came from OCR.

3. **Qualitative facts.** A fact is not only a min/typ/max number. Feature bullets and
   relational sentences are facts too: "simultaneous 50/60 Hz rejection", "higher repeatability
   increases measurement duration and thus energy", "Schmitt-trigger filtered inputs". Extract
   them; do not keep only numeric parameters. Where a claim is qualitative only, record the
   claim verbatim and mark the numeric value `not_stated` rather than inventing a number.

## Output

Facts organized by the six categories in `datasheet2mcp/references/models.md`, plus the five
groups above recorded as `package` and `operating_conditions` records. Each fact carries
`{category, claim, source, section}`. Retrieval/`ask`/`tutorial` tools read from these facts;
an unanswered question is a deterministic refusal, never a generated answer.
