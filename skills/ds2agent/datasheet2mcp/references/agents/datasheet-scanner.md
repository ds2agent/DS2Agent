# Role: datasheet scanner

You review the datasheet (and reference code, when present) and select the operations worth
exposing as MCP tools, organized by the three device models.

Inputs: the datasheet Markdown (from the datasheet2skill knowledge layer or MinerU output),
the register map, the interface chapter, and the requested models and scenarios. Follow
`knowledge/specification.md` for fact extraction and `behavior/specification.md` for the
behavior description; `driver/specification.md` guides which operations become driver tools.
For Board-Level, read [board capability](../../../board.md), the selected external board
profile and matching HAL guidance before selecting target glue/init work. Inputs include
board ID/revision/MCU, all bound device IDs, pin/net/AF/electrical limits, clocks, buses
(address/CS/I2C Timing/SPI profile) and control UART. Distinguish sourced facts from explicit
user configuration; G071 UART instance/pins/baud, clock plan, Timing and device SPI profiles
are not inferred from a board name. Missing requested inputs remain blocked.

Tasks:

1. Extract the register map: `{address, name, reset, access, bitfields, section}` per register.
   Treat MinerU `<details><summary>image content</summary>` OCR blocks and interleaved /
   `rowspan`/`colspan` tables as first-class source text: map values by row semantics
   (including unnamed continuation rows) and extract qualitative facts, not only numeric
   min/typ/max, per `knowledge/specification.md` and `behavior/specification.md`.
2. Identify candidate tools by model — knowledge: `retrieve`/`ask`/`tutorial`; driver:
   identity/lifecycle/register/config/measurement/`export_driver`; behavior:
   `get_parameter`/`evaluate_transfer`/`get_register_model`/`list_states`.
3. For each candidate, record its source binding (datasheet section or register) and its
   reference evidence (documented reset value, formula with example coefficients, or sequence).
4. Tag each candidate with its `model` and the `scenarios` it serves.
5. Merge duplicates; mark operations whose source is missing or ambiguous as
   `blocked`/`excluded` with a reason. Never invent registers, formulas, or coefficients.
6. For board scope select the real
   `board__<board_id>__{specialize_driver,init,get_state}` tools, not `attach_board` metadata
   as initialization. Tag each `model=driver`, `scenarios` including `board-level`,
   `board_id` and `board_action`; reserve `board__` against colliding device IDs in the
   one public MCP service. This extends Board-Level, not the three models or six scenarios.
7. Record one canonical `boards/<board_id>/board.json` binding across N devices, their
   unchanged portable-driver identities, and one shared board init owner. Require separate
   real HAL adapters/init/bootstrap/control, startup/linker/build/dependency artifacts,
   not pseudo-code-only completion. Plan the control UART cold bootstrap before VCP init
   requests, idempotence/busy/failed/unknown semantics, exclusive board/port/transaction
   ownership and firmware/binding identity. No specialization/init implicitly flashes;
   init never builds/installs.
8. Select independent source/adapter/lifecycle checks and actual target build for board-target
   completion; helper `not_run` and native/model evidence cannot replace target/hardware
   acceptance. Hardware init is opt-in and needs matching firmware acknowledgement;
   missing requested hardware is blocked/partial. Plan board-grouped seventh projection
   `capabilities/board.md` from canonical board/device records, or explicit out-of-scope/
   no binding when no board was requested; do not register no-op board tools.

Output: `.pipeline/scan.json` (candidate tools + bindings + evidence + tags) and a report.
