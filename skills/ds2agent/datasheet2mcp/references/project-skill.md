# Generated project consumer skill

This guide owns generation of `<scope>-agent/SKILL.md` for every MCP/full delivery.
It is the consumer/operation entry for the delivered project, not the installed ds2agent
conversion skill and not seven separately installed capability skills. Knowledge-only
`datasheet2skill` keeps its independent contract. Layout is owned by
[aggregation](../../aggregation.md); the delivered entry must not link back to that source
tree. Use [project-SKILL.md](templates/project-SKILL.md) as the reusable source template.

## Inputs and rendering boundary

Stage 4 supplies the final independently selected inventory, exact scope/device/board
identities, supported backend/scope limits, canonical store bindings and actual evidence.
Stage 6 renders the template **after** those decisions are final and the seven capability
projections exist at their delivered paths. Do not deliver this source template, unresolved
markers or generic naming examples as an operational root skill. Seven Markdown files do
not establish seven implementations, nor imply exactly seven tools.

Use existing manifest/inventory and canonical models/board bindings; this entry needs no
mandatory manifest schema extension, new runtime helper or additional service. Actual APIs
are discovered, never inferred from route labels, example names or another device. Preserve
canonical device IDs and final namespaced tools/resources/prompts. Skill-name normalization
must not rename those identities.

The root skill is a small routing projection. It names supported scope and evidence limits,
not a cached owner of live readiness, observations or calibration. Current board readiness
comes from the actual discovered state-query action, and current models/evidence from the
chosen active canonical store. Re-render when inventory, supported scope or device/board
identities change. Unrelated measurement changes, no-op regeneration or relocation alone
need not churn this entry or invalidate otherwise applicable calibration.

## Complete token contract

Replace every occurrence of the following **16** literal `{{UPPER_CASE}}` tokens exactly
once in the template; no other render tokens are defined. No conditional template language
or recursive substitution is needed. Values must not introduce unresolved markers, unsafe
links, unsupported APIs or hidden workspace dependencies. Produce UTF-8 Markdown.

| Token | Required rendered value |
|---|---|
| `{{PROJECT_SKILL_NAME}}` | Unquoted YAML-safe scalar, 1–64 characters, lowercase ASCII letters/digits and single hyphen separators, beginning/ending alphanumeric; no consecutive hyphens. Use a concrete unique project consumer name, not `ds2agent` or a per-device datasheet skill name. Satisfy any stricter target host naming/folder rules. |
| `{{PROJECT_SKILL_DESCRIPTION}}` | A **JSON-quoted string**, also a valid YAML double-quoted scalar: concrete scope/device names and a useful when-to-use description for the delivered operations and important exclusions. Escape quotes, backslashes and newlines; do not emit an unquoted colon or YAML syntax. Keep within the target host's description limit (at most 1024 characters). |
| `{{PROJECT_TITLE}}` | One-line human-readable project title, Markdown-escaped as needed. |
| `{{SCOPE_BINDING}}` | Concrete stable scope ID, purpose, requested/supported mode and relevant exclusions. Distinguish explicitly source/simulation-only scope from requested but blocked hardware work. |
| `{{DEVICE_BINDINGS}}` | Every canonical device ID and concrete part/variant identity, with its supported role/scope. Where useful, link to existing local canonical model directories/files. Never silently merge two devices or normalize their IDs. |
| `{{BOARD_BINDINGS}}` | Each actual board ID, board/profile revision, MCU, bound device IDs and existing local `boards/<board_id>/board.json` reference; state missing binding inputs honestly. If none, explicitly say no board binding/out-of-scope (or requested but blocked, with reason). Do not invent MCU projects or link nonexistent board files. |
| `{{CONNECTION_PREREQUISITES}}` | Concrete supported transport/runtime and dependency/backend prerequisites, plus existing tested setup/configuration section in root USAGE when applicable. Name unavailable dependencies/connection support honestly. Explain required permissions without granting them. Do not guess host client commands, endpoint URIs, executable paths or another server registration. |
| `{{QA_ROUTE}}` | Q&A table cell: per-device availability, **exact actual** callable names and roles, or explicit no callable entry and reason. |
| `{{TUTORIAL_ROUTE}}` | Tutorial table cell with the same per-binding availability/name/role requirements. |
| `{{DRIVER_ROUTE}}` | Driver table cell: exact per-device operations, backend restrictions and relevant board binding/prerequisites; unavailable devices have no callable entry and reason. |
| `{{MOCK_ROUTE}}` | Simulation table cell: exact per-device callable entries, explicitly supported `model`/`native`/`qemu` backend choices and limitations; unsupported backends/routes are explicit. |
| `{{DESIGNER_ROUTE}}` | Designer table cell: exact entries and supported standalone/subset/combined design scope; if no designer API exists, no callable entry even when local source recommendations exist. |
| `{{FEEDBACK_ROUTE}}` | Feedback table cell: actual per-device observation/comparison/calibration/refinement entries and writable targets only where implemented; absent APIs explicitly have no callable entry. A readable audit document is not a refinement implementation. |
| `{{BOARD_ROUTE}}` | Board table cell: actual specialization/init/state entries per bound board and backend restrictions. No board binding or implementation means no callable entry, not a no-op tool. Do not manufacture reserved board names by string interpolation. |
| `{{EVIDENCE_LIMITS}}` | Concrete per-device/board/backend available evidence and missing/not-run/unsupported/blocked scopes, referring to existing local capability sections or USAGE for details. Separate source, model, native, target-build, QEMU and hardware. Never claim hardware readiness or calibration from the inventory, old artifacts, metadata, native/model results or this static entry. |
| `{{STATE_OWNERSHIP}}` | Concrete active-root/store policy: canonical device model locations, any canonical board binding locations, permitted mutable targets/tools (or none), and actual configurable external store behavior if any. Bind reads/writes to one chosen store and explain how USAGE selects it without assuming an undocumented runtime option. Do not create a new store/schema or make Markdown canonical. |

The seven `*_ROUTE` values are single Markdown table cells: no literal newlines or unescaped
`|`; use `<br>` or semicolon-separated per-binding clauses. Escape Markdown syntax without
altering tool identities. Enumerate all bound devices for the original six routes and all
boards for the seventh, including mixed availability. Multiple tools per route are valid;
the same tool may support more than one route only if its real semantics do. A prompt or
resource may be listed as such when actually registered, but is not a callable tool.

Use status terms explicitly, for example `available`, `unsupported`, `out-of-scope` or
`blocked — missing …`. For each unavailable binding say **no callable entry** plus reason.
A blocked implementation that actually exposes a tool may list that name as discoverable
but not currently usable, with its exact missing prerequisite; never count it as ready.
Do not hide a requested incomplete implementation behind an out-of-scope label.

## Routing and portable delivery

Keep the template's fixed local links to `USAGE.md`, `manifest.json` and all seven files:
`capabilities/q_a.md`, `tutorial.md`, `driver.md`, `mock.md`, `designer.md`, `feedback.md`,
`board.md`. All seven files exist even when their content is an explicit unavailable scope.
Read the relevant device section for the original six; read the selected board section for
board tasks. Avoid requiring every manual/model to be loaded before each call.

Only add links that resolve inside the delivered root. Do not link the installed generator,
`external/` source references, work/reports directories, absolute development paths or files
not packaged. Deliver relevant source/procedure content in the capability docs/USAGE when
needed by a consumer. Local paths are not MCP resource URIs; only discovered registered
resources may be accessed as such. Remote-only MCP access does not grant local document
access; make the complete project package available to the host.

Startup resolves the active root from the rendered skill, reads root USAGE/manifest, then
uses host MCP discovery against **one** root `agent_mcp.py` connection. List tools and, when
supported, resources/prompts; compare final names, scopes and current schemas. Reconcile a
stale/missing entry before invoking the affected route. Never invent a client API, tool,
URI, argument or fallback, or separately register internal device MCP components.

Preserve every route's behavior/safety paragraphs in the consumer entry. In particular:

- Cited facts and procedures retain their own device identity; missing evidence is a refusal.
- Driver/board execution checks binding/backend/readiness and existing authorization. Board
  specialization does not flash/init; init does not build/install/flash. Shared board/probe/
  COM and bus ownership is serialized. Missing target inputs are blockers, not guessed MCU
  constants; uncertain init replies are unknown, never a fabricated ready state.
- Simulation explicitly selects implemented model/native/QEMU support and stays
  `physical: false`; an evaluator, stateful emulator, native driver run, target build and
  real hardware establish different evidence.
- Designer permits selected subsets, preserves standalone circuits, and requires supplied
  topology plus checks of all electrically present boundary participants for combined work.
- Refinement uses actual supported tools and permitted mutable canonical records only.
  Keep physical provenance, device/board/driver/HAL/plan identities and model/calibration
  revisions, including input/output bindings; qualitative room-temperature claims are not
  numeric references. Simulation is not calibration. No automatic arbitrary code edits or
  datasheet fact mutation. Firmware-affecting updates stale affected readiness/build evidence
  until authorized rebuild/reflash/reinit/revalidation; protect unrelated device state.

## Installation and state ownership

Root USAGE must explain the target host's actual skill enabling and MCP configuration
separately. A generated skill installs by retaining/copying the **whole delivered root**
into a host-compatible skill directory, with its host-compatible skill/folder name, not by
copying only SKILL.md or capability docs. Preserve runtime/model/board relative references.
Do not invent universal host installation commands or imply all hosts auto-select the skill.

Choose one active installed/extracted root and canonical store. Update the host's single
MCP configuration to that root; stop/disconnect the old service before switching. Do not
read installed docs while a development server silently writes a second model/calibration
store. If the runtime intentionally uses an external store, document its actual supported
configuration and ownership rather than copying it accidentally or assuming package-local
writes. A relocation alone must not discard state history or invalidate unchanged bindings.

Keep three independent acts explicit: **skill discovery/enabling**, **MCP registration/
connection**, and **execution/hardware authorization**. Reading/installing a skill does not
start/register MCP, install dependencies, execute code, initialize hardware or flash firmware.
All of those require their appropriate explicit existing permission.

## Acceptance after rendering, extraction and skill relocation

The delivery coordinator performs these checks; this guide is not itself proof they ran:

1. Render all 16 tokens using actual final inputs. Parse frontmatter as YAML and check the
   unique host-valid name and concrete useful description. Reject any unresolved template
   markers, generic binding examples or unavailable routes disguised as implementations.
2. Check every local link resolves within the delivered root, including all seven capability
   documents and any token-added model/board links; reject absolute/traversal/symlink escapes.
   The skill needs no installed generator or original working directory to be understood.
3. Compare route names/roles/bindings with the independently selected final inventory and real
   MCP discovery, not an inventory copied from the rendered table. Check every device and
   board, partial availability, current schemas, resource/prompt distinctions and honest
   no-callable-entry reasons. Missing connection/dependency/permission is reported explicitly.
4. Extract the final archive elsewhere and repeat frontmatter/token/link checks. Then copy
   the **entire package** into a disposable host-compatible skill location, choose it as the
   sole active root/store, and repeat them with an unrelated working directory. Follow USAGE
   for enabling/connecting; ensure package-relative imports/models/artifacts still resolve.
5. Under explicit execution permission, use one **real** root MCP connection in each applicable
   extracted/relocated safe fixture: initialize, list tools/resources/prompts when supported,
   and exercise representative safe routes for every device. Isolate mutable models/artifacts
   from pinned delivery and live calibration. Check writes target only that fixture's chosen
   canonical store. Never run hardware/flash/init as an incidental installation smoke check.
6. Record observed results and unexercised scopes. These checks prove neither automatic host
   skill selection nor physical hardware correctness/authorization. Requested missing work
   remains partial/blocked even when static skill validation succeeds.

### Synthetic two-device routing exercise

For a disposable verifier fixture only, suppose its independently defined, implemented
inventory contains `chip_a__ask`, `chip_b__lookup`, `chip_a__tutorial`,
`chip_b__walkthrough`, `chip_a__read_raw`, `chip_b__read_raw`, `chip_a__simulate` and
`chip_b__simulate`. These are **synthetic fixture identities, not APIs to assume in a real
project**. Its schemas define a model-only simulation backend and nonphysical driver
fixtures, and it has no designer/refine/board tools or board binding. A valid rendering is:

| Route token | Fixture-only rendered cell |
|---|---|
| `QA_ROUTE` | `chip_a`: available — `chip_a__ask`; `chip_b`: available — `chip_b__lookup` |
| `TUTORIAL_ROUTE` | `chip_a`: available — `chip_a__tutorial`; `chip_b`: available — `chip_b__walkthrough` |
| `DRIVER_ROUTE` | `chip_a`: available — `chip_a__read_raw`; `chip_b`: available — `chip_b__read_raw`; fixture/nonphysical only, no hardware backend |
| `MOCK_ROUTE` | `chip_a`: available — `chip_a__simulate`; `chip_b`: available — `chip_b__simulate`; model only, physical: false; native/qemu unsupported |
| `DESIGNER_ROUTE` | `chip_a`, `chip_b`: unsupported — no callable entry; no designer implementation |
| `FEEDBACK_ROUTE` | `chip_a`, `chip_b`: unsupported — no callable entry; no refinement implementation or physical observations |
| `BOARD_ROUTE` | Out-of-scope — no board binding, no callable entry; no firmware/control backend |

Bind the fixture's real part identities and canonical paths, concrete name/description,
connection prerequisites, read-only state policy and source/model-only evidence in the other
tokens. Still provide seven local docs, with designer/feedback/board explaining their limits.
Acceptance discovers exactly the fixture inventory over one real MCP connection, follows
both devices' actual schemas, refuses nonexistent designer/refine/board calls, and records
that it has established no real MCU implementation, target build, hardware or calibration.
