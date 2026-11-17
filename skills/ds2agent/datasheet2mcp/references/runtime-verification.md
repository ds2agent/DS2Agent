# Runtime verification (acceptance contract)

Every delivered MCP tool carries saved acceptance calls independently derived from
documented examples, reset values or reference calculations. A tool without executable
acceptance evidence is not delivered. The helper checks the supplied evidence; it cannot
establish that an expected value or citation actually came from a datasheet.

## Environment and execution

`scripts/verify_mcp_server.py` requires **jsonschema** in `PROJECT_PYTHON`; it is not a
stdlib-only verifier. Declare `jsonschema` in the delivered runtime dependencies alongside
the generated server's `mcp` SDK dependency. Use the already selected project interpreter;
do not silently install dependencies or substitute another environment.

```text
PROJECT_PYTHON scripts/verify_mcp_server.py path/to/device_mcp.py --project-root PROJECT_ROOT
```

Replace `PROJECT_PYTHON` and `PROJECT_ROOT` with the actual interpreter and project paths.
`--models knowledge,driver,behavior` and
`--scenarios board-level,digital-twin,hardware-calibration,mcp-interface,trial-running,reference-circuit`
are the defaults. Restrict these lists only to the agreed scope; unknown tags fail.
An explicit empty scenario list (`--scenarios ""`) requests no scenario coverage.

Run from a fresh interpreter in the project and again after extracting the final delivery.
Imports, `build_server()`, hook calls and saved acceptance calls **execute generated code**;
obtain the workflow's code-execution authorization first. This helper is not a sandbox.
The generated acceptance environment must use deterministic fake transports, not silently
contact physical hardware or launch native/QEMU firmware.
Run state-changing acceptance, especially refinement, against isolated fixture copies of
models/artifacts. Never modify the delivered or active calibrated state merely to validate
an archive; preserve the independently pinned delivery bytes.

With `--project-root`, the JSON report is
`tests/summary/verify_mcp_server.json` under that root. Exit 0 means the required automatic
contract checks passed, not that every evidence scope ran. Explicit board target/hardware
`not_run` records may coexist with exit 0. Exit 1 means a contract, recorded evidence,
execution, comparison or report-writing failure. The console states the MCP inventory
status and, for each advertised board, metadata/target-build/hardware-init statuses. Without
`--project-root`, diagnostics remain on the console but no evidence file is saved.

## Server module contract

Expose a nonempty `MCP_TOOLS` dictionary keyed by tool name. Each entry contains:

```python
{
    "name": "read_chip_id",              # exactly equals the registry key
    "model": "driver",                  # knowledge | driver | behavior
    "scenarios": ["board-level", "mcp-interface"],
    "description": "Read the chip ID through the fake transport",
    "params": {"type": "object", "properties": {}},
    "source": "datasheet section 4.3.1, ID register reset value",
    "fn": read_chip_id,
    "acceptance": [
        {"args": {}, "expect": {"chip_id": 88}}
    ],
}
```

The snippet illustrates an entry, not a complete device implementation. `params` must be
a valid JSON Schema for the arguments object and structurally match the built MCP server's
input schema, ignoring only `title`, `description`, `$comment` and `examples` annotations
at schema nodes. Prefer the actual schema produced by the selected SDK over guessed fields.
`scenarios` may be omitted, but every supplied tag must be recognized and every requested
scenario must have a valid tagged tool. Names, descriptions and sources are nonempty
strings; `model` uses one recognized tag; `fn` is callable.

Every `acceptance` is a nonempty list of objects explicitly containing both `args` (an
object) and `expect`. Argument objects are validated with `jsonschema` before calls run;
malformed schemas, invalid arguments and unresolved references encountered during
validation fail. Expected values, arguments and entire actual results must be finite JSON
values: no NaN/infinity, non-string object keys, tuples or Python-only objects.
Synchronous and awaitable tool results are supported. Exceptions fail that case.

`MCP_RESOURCES` and `MCP_PROMPTS` may hold knowledge assets and workflow prompts as defined
by the runtime contract; this helper does not validate their runtime exposure.

## Comparison rules and evidence

- Integers and booleans are exact and type-distinct: `True`, `1` and `1.0` do not satisfy
  an integer assertion interchangeably. Large integer IDs are never rounded to floats.
- Floating expected values compare exactly by default, with no implicit epsilon,
  percentage or ULP allowance. An equal integer result may satisfy a floating assertion.
- A case may supply `tolerance: {"abs": 0.01, "rel": 0.001, "source": "documented rounding bound"}`.
  At least one of `abs`/`rel` and a nonempty source are required. Bounds must be finite,
  nonnegative numbers, not booleans; unknown tolerance fields fail. For floating expected
  leaves only, the allowed difference is `max(abs, rel * abs(expected))`, with omitted
  bounds zero. The report records every path where this explicit tolerance was used.
  A tolerance never relaxes an integer or boolean assertion.
- An integer assertion (chip ID, register readback, status, configuration) may instead be
  scoped by a datasheet-sourced `mask` or `valid`, because the datasheet marks some bits
  reserved/don't-care or documents more than one valid value. `mask` is a nonnegative integer
  and the assertion becomes `(actual & mask) == (expected & mask)`. `valid` is a nonempty list
  of integers and the assertion becomes `actual in valid`. Supplying both fails; neither relaxes
  a float or boolean assertion. The record's `source` must cite the bitfield/reserved-bit/
  valid-value section: this is a sourced scope, not arbitrary numeric slack — a differing
  defined bit, or a value outside the documented set, still fails. The report records each
  path where a `mask`/`valid` was applied.
- Acceptance objects intentionally support partial expected dictionaries, recursively:
  assert the sourced measurement/reset fields while permitting diagnostic fields such as
  traces in actual output. Lists have exact lengths and ordered comparisons; absent
  expected keys fail. The *whole* actual output must still be finite JSON. This convenience
  is not permission to omit the behavior the case is meant to establish.

Each case records its tool/index, source, status, errors, arguments, expected and actual
values when available, and applied tolerances. Invalid metadata prevents the affected
calls from running and records them as `not-run`, never passing them silently. Missing or
malformed entries/cases fail even if other tools pass. Required model and scenario
coverage counts only entries with valid metadata and schemas.

## Live cross-model checks

When both driver and behavior model tools are present, `CROSS_MODEL_CHECKS()` is mandatory.
If supplied in another scope it is still checked. It returns a **nonempty list** of records
with unique nonempty names, nonempty sources, and explicit `expected` and `actual` values:

```python
def CROSS_MODEL_CHECKS():
    return [
        {
            "name": "ID register address and reset",
            "source": "datasheet register table, ID row",
            "expected": BEHAVIOR_MODEL["registers"]["ID"],
            "actual": DRIVER_MODEL["registers"]["ID"],
        },
        {
            "name": "conversion coefficient",
            "source": "datasheet transfer-function coefficient",
            "expected": BEHAVIOR_MODEL["coefficients"]["scale"],
            "actual": DRIVER_MODEL["coefficients"]["scale"],
        },
    ]
```

These names illustrate accesses to the generated server's **live canonical models**.
Check the relevant register addresses/defaults and coefficient/min/typ/max records, using
portable paths to delivered canonical models. Do not return caller-supplied PASS strings,
precomputed success flags or duplicated expected literals detached from those models.
The runner evaluates values itself; empty/malformed lists fail. Cross-model records use
exact object key sets (unlike partial acceptance dictionaries), exact lists and the same
numeric rules; optional sourced `tolerance` has the same format as acceptance.

The helper enforces record shape and compares the returned data. Independent review must
confirm the hook reads canonical data, covers the relevant records, and binds them to real
datasheet evidence. Passing spot checks cannot establish exhaustive semantic equivalence.

## Refinement immutability

Refinement tools must include the underscore-delimited segment `refine` in the registry
name or callable name (for example `refine`, `refine_model`, `device_refine`). Such a tool
requires `IMMUTABLE_DATASHEET`: a nonempty mapping of the canonical immutable facts actually
used by the models, with finite JSON content. Do not provide a disconnected sentinel copy.
Accepted calibration belongs in the mutable calibration layer, never in reset values or
documented min/typ/max facts.

Every executed refinement acceptance snapshots that mapping's identity and complete
content before and after the call. Nested changes, removal/rebinding (even to equal
content), invalid post-call contents, and mutations followed by exceptions fail. The old
mapping is checked as well as the current binding. At least one refinement acceptance per
refine tool must execute with snapshots; invalid/missing evidence cannot pass the check.
The report includes per-case immutable-check outcomes and an aggregate refinement status.
Independent review must confirm this mapping is genuinely canonical; the helper cannot
detect changes that a function makes and restores entirely within a call.

## MCP SDK checks and delivery limits

When `importlib.util.find_spec("mcp")` finds the SDK, `build_server()` is required and is
called. The returned server must expose the supported `list_tools()` interface, including
FastMCP's asynchronous interface. The helper compares the actual exposed names and JSON
input schemas with `MCP_TOOLS`, rejects duplicates, and reports mismatches. Schema comparison
removes only `title`, `description`, `$comment` and `examples` annotations at known schema
nodes, including nested properties, definitions and composition branches. Property and
definition names are preserved even when named `title` or `description`; constraints and
instance payloads such as `default`, `const` and `enum` are not stripped. Unknown extension
keywords remain unchanged. The remaining JSON structure must match; this is **not full
logical schema equivalence** (for example, alternate equivalent compositions need not
compare equal). Build, import discovery or listing errors are failures, not an excuse to
label the SDK absent.

When the SDK is genuinely absent, `mcp.status` is `not-checked`, **not PASS on protocol
coverage**. Other helper checks can still pass in that environment. An MCP delivery still
requires execution in an environment with the SDK plus real client initialize/list/call
integration evidence. Even `mcp.status: passed` proves only actual server construction and
inventory/schema listing, not successful transport negotiation or every client call.

Keep source review, deterministic model simulation, actual native compiled-driver
execution, optional QEMU firmware execution, and physical observations as distinct scopes.
Saved tool calls and model agreement do not establish native/QEMU execution, electrical
compatibility, bus timing, physical accuracy or hardware calibration. No physical hardware
is required to honestly deliver source/model evidence; a requested unavailable hardware
scope remains explicitly blocked/partial. See [scenarios](scenarios.md) and the canonical
[QEMU/backend guidance](../../external/tools/qemu.md) for backend-specific evidence.

## Unified entry and refinement across integration

Component verification is necessary but final acceptance targets the one scope-level
`agent_mcp.py` entry defined by [aggregation](../../aggregation.md). Its combined registry
uses `<device_id>__<tool_name>` keys and matching entry names, retains each original model,
source, callable and typed schema, and records device/original-tool provenance. Root
`build_server()` must expose those exact names through a single client connection.

Root `CROSS_MODEL_CHECKS()` delegates to live component checks with unique device-prefixed
check names; do not drop one device's checks merely because another device provides the
same model tags. Root `IMMUTABLE_DATASHEET` references all canonical device facts. Review
delegated refinement guards too: a disconnected aggregate snapshot cannot establish that a
component did not rebind its own store or mutate another device's mutable records.

The helper validates the combined registry, saved calls, hooks and SDK listing; it does not
infer completeness from source selection, prove device routing/isolation, or test the wire
protocol. Keep an independently selected final inventory in the root manifest and run real
MCP initialize/list/call checks against it. Namespace and exercise resources/prompts as well.
Registration-only success is insufficient.

Include acceptance for a component refinement before integration, visibility through the
unified service, a second refinement through `<device_id>__refine`, and visibility of that
commit through the same component store. Verify other-device records stay unchanged,
misbound reports are refused, and failed candidates leave active records/artifacts intact.
Pure integration must preserve driver hashes and applicable calibration; changed effective
bindings or firmware still require the affected revalidation in [feedback](feedback.md).

## Generated root consumer skill acceptance

Every MCP/full delivery also follows [project skill generation](project-skill.md) using
[the source template](templates/project-SKILL.md). These checks belong to the coordinator
and independent extraction acceptance: `verify_mcp_server.py` does **not** implement a new
skill-frontmatter, template-rendering, link or host-installation verifier.

- Parse the rendered root `SKILL.md` frontmatter: require a valid unique host-compatible
  project name and concrete description; reject every unresolved template token.
- Resolve all local references within the delivered root, including `USAGE.md`,
  `manifest.json` and seven capability files. Reject development-only paths, missing files
  and escaping links. The original six projections remain device-grouped; board is board-grouped.
- Check all seven routes against the independently selected final inventory and actual MCP
  discovery names/schemas. One route may require several tools; seven docs do not establish
  seven implemented tools. Blocked/out-of-scope routes have no callable entry and name limits.
  Preserve device/board bindings and canonical model ownership.
- After fresh extraction, relocate the **entire package** into a host-like skill directory,
  choose that active root/store and repeat link/runtime resolution from another CWD. Verify
  documented enablement and separate one-connection instructions; do not copy just `SKILL.md`.
- With explicit execution permissions, initialize/list/call the real relocated `agent_mcp.py`
  through one MCP connection, comparing the final inventory. Discover resources/prompts when
  supported; do not assume local Markdown has resource URIs. Exercise safe supported routes
  and device/refinement isolation using disposable canonical-model/artifact fixture copies,
  not pinned delivery state or active hardware. Unavailable routes remain unavailable.

Record outcomes/limits in working `reports/delivery-validation.json`, outside the archive.
Reading/installing the skill must not register MCP, install dependencies, execute firmware,
flash or operate hardware. Actual hardware/backend acceptance still needs its own permissions,
implemented prerequisites and evidence; these checks prove neither automatic host-agent skill
selection nor physical readiness. Knowledge-only datasheet2skill retains its independent contract.

## Board deliveries and automatic identity checks

Board specialization extends the existing `driver` model and `board-level` scenario; it
does not create another device model or scenario. Follow [board capability instructions](../../board.md)
and the selected external board profile before generating or operating target glue.
Keep one public `agent_mcp.py`. For requested board scope it declares:

```python
BOARD_CAPABILITIES = {"lab_board": "boards/lab_board/board.json"}
```

The verifier runs `verify_board_capabilities.py` **after saved acceptance and hooks**,
including any specialization/refinement calls, so those calls cannot hide stale delivered
bytes behind a pre-call metadata pass. Board tools still undergo every ordinary saved-call,
JSON Schema, model/scenario and installed-SDK inventory check above.

Absent/empty `BOARD_CAPABILITIES` with no board tools reports `board.status: not-requested`;
existing non-board servers need no manifest. A supplied non-dictionary registry, advertised
`board__` tool without a manifest, orphan/unknown action, missing board tool, or action
metadata on a misrouted name fails. For unambiguous portable namespaces, board/device IDs
start with an ASCII letter/digit and contain only ASCII letters/digits, `_` or `-`, without
`__`. Device ID `board` is reserved. Each board has exactly these advertised action names:

- `board__<board_id>__specialize_driver`
- `board__<board_id>__init`
- `board__<board_id>__get_state`

Manifest `tools` maps the three action names (without prefixes) to these exact names.
Corresponding registry entries require `model: driver`, a `board-level` scenario,
the same `board_id`, and `board_action` equal to the unprefixed action.

All manifest/artifact paths resolve from the server module's `__file__` parent, **never
the invocation CWD or `--project-root`**. The latter controls only report output.
Paths use `/`, are nonempty and relative, and cannot contain empty/`.`/`..` components,
backslashes, colons, absolute paths or symlink escapes. Files must exist as regular files;
driver roots must exist as directories. Require `capabilities/board.md` for advertised
scope. Its prose is a projection, not a mutable state source or automatically verified
electrical design.

The schema-1 `boards/<board_id>/board.json` contract requires:

- Matching `board_id`, integer `schema: 1`, and nonempty `sources` reference strings.
- A `binding` with nonempty `profile_id`, `board_revision`, `mcu`; nonempty `pins`,
  `clocks`, `buses`, `control` objects; lowercase 64-hex `hal_sha256`, `plan_sha256`;
  and a nonempty `devices` list.
- Each device has a unique `device_id`, root-relative delivered-package `driver_root`,
  nonempty unique `driver_files` relative to that package (including C source/header),
  lowercase `driver_sha256`, and `bus_id` present in `binding.buses`. Additional actual
  address/CS/pin/electrical configuration belongs in the binding, not guessed defaults.
- `binding_sha256` is SHA-256 of UTF-8 `json.dumps(binding, sort_keys=True,
  ensure_ascii=False, separators=(',', ':'), allow_nan=False)` with no final newline.
  It excludes output hashes and reports, preventing a firmware self-hash cycle.
- `artifacts` contains unique root-relative `{role, path, sha256}` records for actual
  `init_source`, `init_header`, `hal_source`, `hal_header`, `build_recipe`, `startup`,
  `linker`, `app_source`, `control_source`, `control_header`, `binding_header` files, plus
  one unambiguous `firmware` artifact when built. Every recorded file's exact bytes must
  match its lowercase SHA-256.
- Portable-driver hashes are independently recomputed using the sorted relative-path/file
  SHA pairs algorithm in [feedback](feedback.md#stable-identities). Reordering the file
  list, relocation or board-glue changes do not themselves change portable-driver identity.
  Binding changes, portable-driver drift and recorded board/firmware artifact drift fail.
  HAL/plan hash format and inclusion in the binding digest are checked, but their actual
  input-set algorithms remain generator/source-review responsibilities: there is no
  universal HAL/plan artifact-set algorithm to invent here.

Malformed JSON (including duplicate keys and non-finite numbers), malformed contract
records, unsafe paths and inconsistent identities fail with diagnostics rather than
escaping as uncaught malformed-contract exceptions.

### Board evidence and report interpretation

`evidence.target_build` and `evidence.hardware_init` each require `status` of `passed`,
`failed` or `not_run`; non-passed records need a nonempty `reason`. Explicit failed
evidence fails verification. Well-formed `not_run` evidence can pass metadata verification,
but **never becomes a target-build or hardware pass**.

- A passed target-build record requires a firmware-role artifact and a nonempty `toolchain`
  string. An explicitly native/model/QEMU/simulation backend is not a target build.
- A passed hardware-init record requires a passed target build, `physical: true`,
  `state: ready`, matching `board_id`, `binding_sha256` and firmware artifact
  `firmware_sha256`, plus nonempty `observation` or `source` reference. An explicitly
  native/model/QEMU/simulation backend cannot satisfy physical initialization.
- `physical`, when supplied, must be a boolean. A non-passed hardware record cannot claim
  ready physical state; any `state: ready` there must explicitly be `physical: false`.
  Actual failed physical attempts may record `physical: true, state: failed`.

The JSON report adds `board.status` (`not-requested`, `passed`, `failed`), `board.errors`,
and `board.boards[board_id]` with metadata status/errors, validated device/binding
identities and separately reported `target_build`/`hardware_init` statuses. Incomplete
manifest validation leaves those evidence scopes `not_run` with an explicit reason;
invalid claimed passes are not promoted to validated evidence statuses.

These automatic checks verify the **consistency of supplied evidence records**, not the
truth of a toolchain/observation claim. A synthetic fixture with matched identities proves
the validator's boundary only. Review the independently retained logs/source references
before trusting any claimed target/hardware outcome.

### Separate acceptance scopes

| Scope | Required evidence beyond metadata |
|---|---|
| Source review | Actual adapter/init/bootstrap/control implementation, real startup/linker/target project, pinned/restorable dependencies; no stubs/no-ops; sourced AF/pin/clock/timing/electrical correctness; unchanged portable driver boundaries |
| Native/model | Labelled deterministic lifecycle/adapter behavior; idempotence, wrong-binding/busy rejection, serialization, failure-safe CS/ports and timeout-to-unknown behavior; the fake HAL must reproduce documented transport framing/transaction semantics (status-byte placement, STOP / chip-select position, lost-frame consequences); `physical: false` |
| Target build | Run the real reproducible selected-MCU project with the actual target toolchain; preserve logs/toolchain identity and matching firmware artifact; native compilation is insufficient |
| QEMU, when applicable | Actual supported target/backend execution, separately labelled; not physical readiness |
| Real MCP | SDK-backed initialize/list/call over the single public connection; verify board/device routing and multi-device isolation; registry/listing alone is insufficient |
| Physical init, when requested | Authorized explicit flash/install if needed, then actual matching firmware acknowledgement with board/binding/build/protocol identities and retained physical observation; no implicit flash/build/install in `init` |

Control bootstrap must establish HAL/timebase/verified clock and the control UART before
receiving a command. Board init must not reconfigure that live UART while replying.
Host metadata attachment is not MCU initialization. Verify same-binding already-ready
calls do not reset devices, changed/active bindings reject rather than silently reconfigure,
and lost responses yield `unknown`, never assumed success or blind retry.
Sensor-specific startup stays in portable drivers, and board readiness does not establish
sensor accuracy/calibration. Effective driver/HAL/pin/clock/plan/firmware changes require
affected rebuild/reflash/reinitialize/revalidation; stale observations are not relabelled.

A board-target completion requires an actual target build; a requested physical-init
completion requires actual hardware init. Missing target inputs/toolchain/hardware leave
that requested scope explicitly blocked/partial even if automatic metadata checks pass.
Source/native-only delivery must name its narrower scope honestly.

## Helper regression tests

The adjacent `scripts/test_verify_mcp_server.py` and `scripts/test_verify_board_capabilities.py`
use stdlib `unittest` for focused consumer-visible success/failure boundaries. From the
datasheet2mcp directory, the integration owner can run:

```text
PROJECT_PYTHON -m unittest discover -s scripts -p test_verify_mcp_server.py
PROJECT_PYTHON -m unittest discover -s scripts -p test_verify_board_capabilities.py
```

Contract tests isolate SDK absence; SDK integration tests use real FastMCP when `mcp` is
installed and skip only when it is absent. They cover actual inventory/schema mismatches;
neither these tests nor this helper claim that any QEMU target was exercised.
Board fixtures are explicitly synthetic records: they cover drift, identities, unsafe
paths, routing and false-readiness boundaries without claiming a target build or physical init.
