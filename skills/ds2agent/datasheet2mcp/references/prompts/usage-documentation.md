# Stage 6: Documentation and ZIP delivery

Coordinator. Continue from `runtime_validation_done`.

Steps:

1. Write root `USAGE.md` with one public MCP entry/client configuration, unified dependency
   installation, namespaced device/tool routing, capability locations, platforms and tested
   commands. Component docs describe internal APIs and backend/build requirements.
   Explain refinement before/after integration, binding/isolation rules, actual evidence
   scopes and blocked/deferred work. Do not require separate per-device client connections.
   Explain installing/enabling the generated consumer skill by retaining/copying the **entire**
   delivered root into a host-compatible skill directory, respecting host name/folder rules,
   not copying only `SKILL.md` or seven docs. Choose one active root/store, avoiding installed
   versus development state splits. Separately explain authorized dependency setup and one
   MCP connection rooted there. Reading/installing the skill does not register clients,
   install dependencies, execute code, flash or authorize physical actions.
   Startup resolves this root, reads `USAGE.md`/`manifest.json`, and discovers actual MCP
   tools/resources/prompts when available; match current names/schemas, never invent names or
   URIs. Local Markdown is not automatically a resource; remote-only MCP access does not
   make local skill files readable. Missing connection/dependency/route is a named prerequisite.
   For board scope read [board capability](../../../board.md), the selected external board
   profile and matching HAL guidance. Document required versus sourced board/revision/MCU,
   pins/net/bus/address/CS, electrical limits, clock/I2C Timing/SPI/control UART settings,
   actual target project/startup/linker/build/dependencies and explicit authorization.
   Missing G071 UART/clock/Timing/SPI inputs remain blocked, never guessed.
   Show the reserved `board__<board_id>__{specialize_driver,init,get_state}` tools through
   the same MCP entry; explain real specialization without portable driver edits, no
   implicit flash/init, and init without implicit build/flash/install. Document cold-boot
   control bootstrap before VCP commands, init shared once across N devices, identity/
   ownership, idempotence/busy/failure/unknown behavior and state queries without reinit.
2. Stage seven capability projections and canonical device models, and render root
   `<scope>-agent/SKILL.md` following [project skill generation](../project-skill.md) from
   [the source template](../templates/project-SKILL.md). Bind every token using Stage 4's
   final inventory, concrete devices/boards, supported/blocked routes and evidence/backend
   limits. Require valid unique host-compatible frontmatter and portable links to delivered
   `USAGE.md`, `manifest.json` and all seven capability files. Read one relevant capability
   section per task, not every model/manual. Bind seven routes to actual supported tools,
   with no callable entry for unavailable routes, preserving canonical state ownership.
   Do not deliver the unrendered template. Build the single `dist/<scope>-agent.zip` per
   [aggregation](../../../aggregation.md) and [output delivery](../output-delivery.md).
   Do not deliver nested per-device MCP ZIPs.
   `capabilities/board.md` groups by board ID and lists bound devices; the original six
   retain per-device sections. Project canonical `boards/<board_id>/board.json` plus device
   models, never store mutable state in Markdown. Include real separate init/HAL/control/
   bootstrap/startup/linker/build/dependency files and actual built firmware identities.
   No requested board scope means out-of-scope/no binding, not fabricated firmware.
3. Assign fresh-extraction installation, real calls through the single MCP entry, device
   routing/refinement isolation and selected backend acceptance to an independent verifier.
   Keep `reports/delivery-validation.json` and scratch evidence in the working project, outside ZIP.
   Also assign parsed skill frontmatter, no unresolved tokens, portable in-root local links,
   and all seven routes matched to final inventory/real discovered names and schemas.
   Repeat after relocating the whole extraction into a host-like skill location, selecting
   that one active root/store and running from another CWD. Require safe isolated actual
   one-MCP discovery/calls, not registration-only evidence or mutations of pinned state.
   These are coordinator/extraction acceptance responsibilities, not already-implemented
   new verifier features, and do not prove automatic host skill selection or hardware support.
   Require actual target-build evidence for board-target completion; a metadata helper's
   well-formed `not_run` record is not build/hardware PASS. Verify board manifests after
   saved calls, portable-driver/artifact identities and multi-device ownership/isolation.
   Hardware operations remain opt-in; actual init requires matching firmware acknowledgement.
   Record source/model/native/target/QEMU/hardware evidence and physical limitations
   separately; native/model results are `physical:false`. Changed effective board inputs
   stale readiness; document required authorized rebuild/reflash/reinit/revalidation.
   Requested missing board inputs/build/hardware keep delivery partial/blocked.
4. Write `delivery_done` after actual scope acceptance and `verify_workflow.py --through complete`.

Lead the final response with `dist/<scope>-agent.zip`, then tools grouped by model,
install/startup directions, actual source/simulation/hardware scope and external requirements.
Missing requested work remains partial; a knowledge-only run retains its standalone skill.
