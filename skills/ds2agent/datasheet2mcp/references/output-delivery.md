# Output delivery

[Aggregation](../../aggregation.md) owns the layout for MCP/full conversions:
`dist/<scope>-agent/` and `dist/<scope>-agent.zip`. The ZIP contains the scope directory:

```text
<scope>-agent/
├── SKILL.md                      # rendered project consumer entry, not generator instructions
├── USAGE.md
├── agent_mcp.py                   # single public entry point
├── manifest.json                  # routes and final expected inventory
├── requirements.txt              # unified runtime dependencies
├── capabilities/                 # seven scope-wide markdown projections, including board.md
├── boards/<board_id>/            # only for requested, supported board bindings
│   ├── board.json                # canonical multi-device binding, artifacts and evidence
│   ├── board_tools.py            # internal module if used; never another public endpoint
│   ├── firmware/                 # real init, HAL adapter, bootstrap/control, startup/linker/build
│   └── artifacts/firmware.elf    # actual firmware when built
└── devices/<device>/
    ├── models/
    │   ├── knowledge.json
    │   ├── driver.json
    │   └── behavior.json
    ├── mcp/<device>-mcp/
    │   ├── <device>_mcp.py
    │   ├── manifest.json
    │   ├── USAGE.md
    │   ├── requirements.txt      # or documented dependency installation instructions
    │   ├── driver/               # exported .h and .c when produced
    │   ├── register_map.json     # projection of canonical behavior model
    │   ├── resources/            # knowledge assets
    │   └── simulation/           # runtime harness/model/build recipes when exposed
    └── skill/<device>-datasheet/ # combined output only
```

`<scope>` is the device identifier for one device, a stable project identifier otherwise.
Repeat the device subtree for every device and the board subtree for every selected board;
do not make per-device copies of the seven capability files, duplicate shared board init,
or nest MCP ZIPs. The original six projections retain per-device sections; `board.md`
groups by board ID and lists bound devices. Without requested board scope it states
out-of-scope/no binding, with no fabricated firmware. Knowledge-only datasheet2skill keeps
its standalone package and does not require this root project skill, seven projections or a board package.

## Contract

- Require a concrete root `SKILL.md` generated under the [project skill guide](project-skill.md)
  from [the source template](templates/project-SKILL.md). Stage 4 supplies final device/board
  bindings and independently selected inventory; Stage 6 renders every token. Valid unique
  host-compatible frontmatter and seven honest routes are required, not seven invented tools.
  Unsupported/unimplemented routes have no callable entry. Implemented but blocked tools
  may be listed only as discoverable and currently unusable, with exact missing prerequisites.
- Project and fresh-extraction environments must start the one public `agent_mcp.py`
  service and call tools for every device through it. Component-only checks are insufficient.
- Each `manifest.json` records device/interface, model and calibration revisions, model and
  artifact content hashes, tools with model/scenario tags, resources and prompts. References
  to canonical models resolve relative to the delivered component, independent of CWD.
  No model, runtime harness or required build recipe may depend on an undeclared work path.
- Root `USAGE.md` provides one client configuration, unified dependency installation and
  device/tool routing. Component documentation records internal interfaces, platforms,
  backend permissions and build/run instructions without requiring extra client services.
  Explain retaining/copying the whole delivered package into a host-compatible skill directory,
  enabling it per that host's rules, and separately configuring/authorizing one MCP connection.
  Choose one active root/canonical store; do not split installed and development state.
  Reading/installing the skill performs no registration, dependency installation, code execution,
  flashing or physical action. Local capability files are not automatically MCP resources.
- Every tool passes [runtime verification](runtime-verification.md). The SDK inventory check
  supplements real initialize/list/call acceptance against the independently expected final
  names. Check device/resource/prompt routing and shared-hardware access ownership.
- Refinement must work before and after integration using the same canonical store; include
  acceptance for committed-version visibility, device isolation, immutable facts and failed
  candidate rollback. Pure integration does not invalidate calibration; changed effective
  hardware/driver/HAL/plan bindings require revalidation.
- Record source, model, native, QEMU and hardware evidence independently with artifact
  identities and limitations. Requested but unexecuted work stays blocked/partial. No
  physical board is required for an explicitly source/simulation-only delivery.
- Exposed native/QEMU backends ship the source, harness, model and reproducible build/target
  records they need. Do not advertise unimplemented backends. QEMU itself/toolchains remain
  declared external requirements, never bundled or installed implicitly.
- Keep scratch examples, development reports, source-review evidence and run logs outside
  the ZIP. Capability feedback records are delivered audit data, not scratch evidence.
- An independent delivery verifier distinct from every implementer records actual extraction
  acceptance in the working project's `reports/delivery-validation.json`.
- For board scope, first read [board capability](../../board.md), the selected external
  board profile and matching HAL guidance. Deliver real target adapters/init/bootstrap/
  control plus complete startup/linker/build project and pinned/restorable dependency
  locks/licenses. Keep portable device `.c`/`.h` unchanged. Missing clock/UART/bus/pin/
  electrical inputs block requested board scope; never guess G071 target settings.
- Advertise only implemented board backends, through the single public service's reserved
  `board__<board_id>__{specialize_driver,init,get_state}` names. Export `BOARD_CAPABILITIES`
  mapping to canonical root-relative board manifests; reject device-ID collisions.
  All three entries carry `model=driver`, `board-level`, board ID and board action.
- `capabilities/board.md` records per-board scope/missing inputs, profile/revision/MCU and
  sources versus user config, bound devices/driver identities, pin/net/bus/address/CS table,
  electrical/clock/Timing/SPI/VCP settings, bootstrap/init/lifecycle/ownership semantics,
  actual paths/build/dependencies, tools/authorized flash+serial usage, binding/HAL/plan/
  firmware identities, evidence/failures/limits and refinement effects. It projects
  `board.json` plus device models, never mutable state ownership.
- Actual reproducible target build and a hashed firmware artifact are required for
  board-target completion. A metadata helper may accept well-formed `not_run` evidence but
  must not label it target-build/hardware PASS. Model/native checks are nonphysical and
  cannot replace target/hardware acceptance. Physical init requires explicit permission
  and a matching firmware acknowledgement; no implicit build/flash/install in init.

## Build and verify

1. Stage canonical models, verified components and all seven scope-wide projections at
   their final relative paths. Build combined datasheet skills there and pass strict verification.
   Render root `SKILL.md` from the final Stage 4 inventory/bindings following
   [project skill generation](project-skill.md). Link portable delivered `USAGE.md`,
   `manifest.json` and all seven capability files; retain canonical model ownership.
2. Run component checks with evidence in separate working report directories. Verify
   `agent_mcp.py` with `--project-root <WORK_ROOT>/checks/unified` and the agreed model/scenario
   lists. Preserve component results separately; do not overwrite them with the unified run.
   For board scope, verify manifest binding/artifact/portable-driver hashes, safe portable
   paths and board tool routing after saved acceptance calls, so specialization-induced drift
   is caught. Independently review actual adapter/init/control sources for no-ops, safe CS,
   complete bus-transaction ownership, bootstrap before VCP, binding/firmware rejection,
   same-binding idempotence, busy conflicts, failed-safe and timeout-to-unknown behavior.
   Build the actual target with recorded toolchain/dependencies; retain real outcomes.
3. Build the scope ZIP, extract it elsewhere and install root `requirements.txt` in a fresh
   environment with `mcp` and verifier `jsonschema`. Do not restore hidden work-directory imports.
4. Re-run the helper against the extracted `agent_mcp.py`; use one real MCP connection to
   list the independently expected final inventory and call every delivered tool. Exercise
   device routing and refinement across integration, not just isolated component servers.
   Run advertised simulation backends with permission and retain actual checks/limitations.
   Missing requested dependencies are blockers, not another backend's pass.
   Use isolated model/artifact fixture copies for state-changing acceptance; do not mutate
   pinned delivery state or active calibration while checking the archive.
   Call board specialization/init only in isolated fixtures with explicit execution/hardware
   authorization. No automatic flash, live-board reconfiguration or physical test is implied
   by archive acceptance. Verify actual/model-labelled state queries do not initialize;
   check shared board init once across N devices and per-device isolation. Recheck board
   manifests after calls. Hardware readiness requires matching physical evidence; missing
   requested hardware/builds stay blocked/partial.
   As coordinator/extraction acceptance, parse root skill frontmatter, reject unresolved template
   tokens, and resolve every local link inside the delivered root. Match all seven routes
   against the independently expected inventory and actual discovered MCP names/schemas;
   unavailable routes must remain explicit. Repeat after relocating the entire extracted
   package into a host-like skill directory, using that chosen root/store and a different CWD.
   Exercise real discovery/calls through its one MCP connection with safe isolated fixtures
   and explicit permissions; list resources/prompts when supported, never invent resource URIs.
   These are acceptance responsibilities, not new features of `verify_mcp_server.py`.
   They prove neither automatic host skill selection nor unavailable hardware/backend support.
5. Confirm delivered model/artifact bytes match manifest hashes. Record actual outcome and
   limitations; only then mark delivery complete and lead the response with
   `dist/<scope>-agent.zip`.
