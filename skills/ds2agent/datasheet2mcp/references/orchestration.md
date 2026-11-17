# Multi-agent orchestration

The host provides agent spawning, execution tools, concurrency limits, and lifecycle
events. Role instructions live in `references/agents/`. A role description alone is not a
running agent.

Use [selection and wrapping](tool-selection-and-wrapping.md) for tool decisions and source
binding, [runtime requirements](runtime.md) for execution and packaging, and the chosen
interface route for transport.

## Inputs and workspace

Bind template values before passing work to specialists:

| Value | Meaning |
|---|---|
| `PROJECT_ROOT` | Absolute output project directory |
| `DEVICE_NAME` | Device identifier without extension, lowercase (e.g. `bmp280`) |
| `DEVICE_ID` | Orderable part or chip family as printed on the datasheet (e.g. `BMP280`) |
| `SKILL_ROOT` | Absolute datasheet2mcp skill directory; helpers are under `scripts/` |
| `PROJECT_ENV`, `PROJECT_PYTHON` | Absolute project environment directory and its interpreter |
| `BOARD_ID`, `BOARD_PROFILE`, `BOARD_REVISION` | Stable selected board identity/profile/revision; absent when out of scope |
| `BOARD_CONFIG`, `BOARD_DEVICES` | Verified pins/clocks/buses/control settings and all bound device IDs/driver identities |

Pass the actual source path, stable device/interface IDs, selected route, and user filter
directly in each assignment. In documentation, `<device>`, `<module>`, and similar
angle-bracket terms stand for task-specific values; replace them before running commands.

For Trial-Running, include the selected backend (`model`, `native`, optional `qemu`), owned
scenario/artifact IDs and evidence scope in each assignment. Follow
[simulation backends](../../external/tools/qemu.md); board profiles do not certify QEMU
support. Required but unavailable hardware or target support stays blocked, never replaced
by a lower-scope simulation pass.

For board specialization/init requests, read [board capability](../../board.md), the
[APP firmware specification](../../app/specification.md), the selected external board
profile and matching HAL guidance before assigning glue or hardware work.
Pass their actual paths, source references, required user configuration, execution/hardware
authorization and missing-input list. Do not guess G071 UART instance/pins/baud, clock plan,
I2C Timing or device SPI profiles. Missing requested inputs block board scope, not a substitute
metadata-only backend. There remain three device models and six scenarios.

Create the requested project and `.pipeline/`; write `project_setup_done` after successful
creation/reuse. Place the source at `sources/<device>/`. Clone a code repository with
submodules when required; inspect incomplete clones before retrying. A local copy/clone must
retain its source identity. Verify the requested identity before reusing an existing
checkout. Write `source_setup_done` after successful source setup.

Record route/hardware evidence in `.pipeline/route.json`. Create `registers/`,
`src/tools/`, `tests/{code,data,results,logs,summary}/`, `reports/`, and
`tmp/{inputs,outputs}/`; write `workspace_setup_done` when prepared. Run commands from the
project root with explicit project interpreters. Generated environments and results stay
outside the scientific source tree.

Pass credentials through process environment or a secret mechanism. Do not embed keys in
source, register maps, reports, test cases, or generated tools. Quote command arguments as
data rather than interpolating user input as shell code.

## Assignments and phase barriers

1. Run the environment manager and datasheet scanner concurrently. Review the scanner's
   selected tools, source bindings, evidence feasibility, and deferred work against the
   environment result.
2. Launch one reference executor per selected example/register-block/formula with exclusive
   output paths. Queue excess work within host and machine limits. Wait for all execution
   results before implementation.
3. Launch one implementer per owning source module in parallel. Assign selected tools,
   completed reference evidence, and concrete source bindings. Wait for all implementation
   handoffs.
   For Board-Level, assign one exclusive board owner for `boards/<board_id>/board.json`,
   real separate HAL contexts/adapters, init/bootstrap/control, startup/linker/build files,
   pinned dependency records and any internal board-tools module. Device implementers own
   portable sources; board specialization must leave those bytes unchanged. Share init and
   board/probe/COM/bus ownership across all N devices instead of per-device board copies.
4. Launch fresh verifier agents for the completed modules. Their agent IDs must differ from
   every implementer's ID, including retries and other modules. Verifiers work in parallel on
   separate modules and process dependent tools in a deliberate order within each module.
   They may repair code within their exclusive ownership and bounded retry policy.
   Assign fresh board verification source/behavior coverage for bootstrap-before-VCP,
   safe CS and complete bus transactions, identity rejection, ready-binding idempotence,
   changed/active-binding busy rejection, failure safety and timeout-to-unknown handling.
   Actual target build is required for board-target completion; native/model execution or
   helper `not_run` acceptance cannot substitute. Missing requested hardware stays partial.
5. Integrate only verified tools and hand off the independently selected final inventory,
   supported/blocked routes, device/board bindings and backend/evidence limits from Stage 4.
   Validate runtime installation; in Stage 6 render root `<scope>-agent/SKILL.md` from
   [the template](templates/project-SKILL.md) under [project skill generation](project-skill.md),
   write whole-package install/enable and separate one-MCP connection instructions in `USAGE.md`,
   and complete [ZIP delivery](output-delivery.md). Assign extraction and host-like whole-package
   relocation acceptance to an independent verifier distinct from every implementer; a prior
   independent verifier may continue. Require portable links, parsed frontmatter, no unresolved
   tokens and route-to-real-inventory checks plus authorized safe isolated actual MCP calls.
   These are coordinator/delivery acceptance, not new automatic helper features.

Give each worker its stage prompt, role instructions, relevant selection/runtime sections,
bound inputs, ownership, and report path. Use the host's actual tools for reads, edits,
commands, agent launch, and lifecycle collection. Do not substitute a changed role prompt in
the same agent context for independent verification. If agent spawning is unavailable,
report the limitation and last completed phase; a different workflow requires an explicit
user request.

The environment manager owns dependency changes. A worker needing a package requests a
serialized installation through the coordinator before resuming. Shared production helpers
need an explicit owner and coordinated verification of every affected module. Workers must
not race installations or edit each other's artifacts.

Board tools share the one public MCP service and reserved
`board__<board_id>__{specialize_driver,init,get_state}` namespace; reject colliding device IDs.
Register `model=driver`, `scenarios` including `board-level`, `board_id` and `board_action`.
Specialization does not flash/init; init performs no implicit build/flash/install and needs
matching firmware/protocol/binding acknowledgement through the implemented control path.
Cold boot establishes the control UART before VCP init can arrive; do not reconfigure it
while replying. Hardware is opt-in; native/model state is explicitly nonphysical.

The coordinator owns seven scope-wide capability projections: original six device-grouped
files plus board-grouped `capabilities/board.md`. Project board manifests/device models,
never use Markdown as mutable state. Without board scope state out-of-scope/no binding.
Run board manifest/artifact/routing checks after saved calls. Effective driver/HAL/pin/clock/
firmware changes stale affected bindings/readiness; coordinate authorized rebuild/reflash/
reinit/revalidation. Merge/relocation/no-op regeneration does not invalidate calibration.
The coordinator also owns the generated root consumer skill as a routing projection, not
another model store or a new runtime schema. Bind all seven capability routes to actual
supported tools (or explicit unavailability), preserve device IDs/namespaced identities and
render only after final inventory/bindings are known. Reading/installing the skill does not
register clients, install dependencies, execute code or authorize physical work.

## Records, retries, and completion

Maintain `reports/agent-runs.json` from actual host events using
[workflow state](workflow-state.md), schema 1. Record agent IDs, UTC times, ownership,
terminal status, immutable report hashes, produced files, and implementation/verifier links.
Pin source identity and tested production files.

At handoffs run
`"$PROJECT_PYTHON" "$SKILL_ROOT/scripts/verify_workflow.py" --project-root "$PROJECT_ROOT" --through PHASE`
for `setup`, `execution`, `extraction`, and `verification`; run `complete` after
installation validation, documentation, and ZIP delivery acceptance. The helper checks
records and hashes. The coordinator still reviews substantive device and delivery results
and collects real lifecycle outcomes. Retain the final delivery verifier's identity and
outcomes in `reports/delivery-validation.json` alongside the existing phase records.

Use at most three environment/scanner/implementation review attempts, five execution
attempts per source, and six verification repair attempts per tool, unless task constraints
require stopping earlier. Do not retry an unchanged missing credential, datasheet, or
hardware condition indefinitely. Retain failed attempts and reasons. Archive a fixed-path
report before replacing it so historical run hashes still match; do not rewrite old report
hashes to conceal failures.

Wait for actual worker completion and inspect its assigned report and tests. A `.done_*`
file signals that work ended, not that it passed. Merge only the expected current per-source
reports; stale markers and other phases must not satisfy completion. Return short worker
summaries with paths to detailed artifacts.

Use the stage markers in `SKILL.md`. Before resuming a marked phase, check source identity,
selection, prerequisites, and artifact hashes. Changed inputs or code require affected
downstream execution/verification. Never refresh hashes alone to make stale evidence
current. Preserve successful history and explain any new selection or exclusion.

## Evidence handling

Expected values come from datasheet-documented examples or independent derivations, never
only agreement between a generated driver and mock. Integers/chip IDs/enums are exact on
their documented fields; an integer register/ID assertion may be scoped by a datasheet-sourced
`mask` (ignore reserved/don't-care bits) or `valid` value set (accept documented variants),
never by arbitrary numeric slack, per [runtime verification](runtime-verification.md).
Floating-point acceptance is exact unless the case supplies a finite nonnegative tolerance
with a source/rationale, following [runtime verification](runtime-verification.md); do not
apply an implicit percentage error to every output. Data preparation uses documented
register values and coefficients. Do not fabricate replacement data or provenance. Preserve
figures and tables belonging to
selected device operations; datasheet-wide benchmark tables can remain verification evidence
without becoming production outputs.

Extracted register maps must record `{address, name, reset, access, bitfields, section}`
per register. A read of a documented reset value is a deterministic acceptance check; a
compensation formula is checked against the datasheet's stated example coefficients and
outputs when present, otherwise against an independent re-derivation from the documented
formula.
