# Workflow state

The coordinator records every host agent run in `reports/agent-runs.json`, schema 1.
`scripts/verify_workflow.py` reads this file and enforces phase order, agent separation, and
artifact hashes.

## Schema 1

```json
{
  "schema": 1,
  "project": "<PROJECT_ROOT>",
  "device": "<device>",
  "runs": [
    {
      "agent_id": "<host agent id>",
      "role": "environment-manager | datasheet-scanner | reference-executor | tool-extractor-implementor | test-verifier-improver | delivery-verifier | coordinator",
      "phase": "setup | execution | extraction | verification | integration | runtime | delivery",
      "model": "pro | flash | low | <other>",
      "started_utc": "2026-11-13T00:00:00Z",
      "ended_utc": "2026-11-13T00:00:30Z",
      "status": "completed | failed | blocked",
      "report_path": "reports/<role>-<module>.json",
      "report_hash": "sha256:<hex>",
      "owned_modules": ["<module>"],
      "produced_files": ["src/tools/<module>.py"],
      "verifies": ["<implementer agent_id>"],
      "verified_by": ["<verifier agent_id>"]
    }
  ]
}
```

`agent_id` must be the host's actual agent identifier, not a role name. `report_hash` is the
SHA-256 of the report file at the time it was archived. `produced_files` are hashed for
selected artifacts (tool modules, server file, manifest); a file whose hash is recorded must
still match, or the phase gate fails.

## Phase order

Markers are written to `.pipeline/` only after their evidence and workflow gate pass:

```
project_setup_done → source_setup_done → workspace_setup_done →
environment_and_selection_done → reference_execution_done →
implementation_and_verification_done → mcp_integration_done →
runtime_validation_done → delivery_done
```

`verify_workflow.py --through PHASE` checks that every marker up to and including `PHASE`
exists and that no later marker is present (a marker for a phase you have not completed must
not exist). `--through complete` requires all markers.

## Agent separation

A `test-verifier-improver` run must not share an `agent_id` with any
`tool-extractor-implementor` run it lists in `verifies`, and must not be the same agent as
any implementer in the same phase, including retries. A `delivery-verifier` must be distinct
from every implementer. `verify_workflow.py` fails the `verification` (respectively
`complete`) gate if any such collision exists.

## Retry limits

At most three environment/scanner/implementation review attempts, five execution attempts
per source, six verification repair attempts per tool. Retained failed attempts keep their
report and hash; do not rewrite old report hashes.
