#!/usr/bin/env python3
"""Verify datasheet2mcp workflow state: phase order, agent separation, report hashes.

Usage:
  verify_workflow.py --project-root DIR --through {setup,execution,extraction,verification,complete}

Exit 0 when the gate passes, 1 otherwise. Stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

MARKERS = [
    "project_setup_done",
    "source_setup_done",
    "workspace_setup_done",
    "environment_and_selection_done",
    "reference_execution_done",
    "implementation_and_verification_done",
    "mcp_integration_done",
    "runtime_validation_done",
    "delivery_done",
]

PHASE_LAST = {
    "setup": "environment_and_selection_done",
    "execution": "reference_execution_done",
    "extraction": "implementation_and_verification_done",
    "verification": "mcp_integration_done",
    "complete": "delivery_done",
}

VERIFIER_ROLES = {"test-verifier-improver", "delivery-verifier"}
IMPLEMENTER_ROLE = "tool-extractor-implementor"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _fail(errors: list[str]) -> int:
    if not errors:
        print("workflow gate: OK")
        return 0
    for e in errors:
        print(f"workflow gate: FAIL: {e}")
    return 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--through", required=True, choices=list(PHASE_LAST))
    args = ap.parse_args(argv)

    root = Path(args.project_root)
    pipeline = root / ".pipeline"
    errors: list[str] = []

    last = PHASE_LAST[args.through]
    last_idx = MARKERS.index(last)

    for m in MARKERS[: last_idx + 1]:
        if not (pipeline / m).exists():
            errors.append(f"missing marker .pipeline/{m}")
    for m in MARKERS[last_idx + 1 :]:
        if (pipeline / m).exists():
            errors.append(f"unexpected future marker .pipeline/{m}")

    runs_path = root / "reports" / "agent-runs.json"
    if not runs_path.exists():
        errors.append("missing reports/agent-runs.json")
        return _fail(errors)

    try:
        data = json.loads(runs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        errors.append(f"agent-runs.json unreadable: {e}")
        return _fail(errors)

    if data.get("schema") != 1:
        errors.append("agent-runs.json schema must be 1")
    runs = data.get("runs", [])
    if not isinstance(runs, list):
        errors.append("agent-runs.json 'runs' must be a list")
        runs = []

    implementers = {r["agent_id"] for r in runs if r.get("role") == IMPLEMENTER_ROLE}
    seen_ids = set()
    for i, r in enumerate(runs):
        if not isinstance(r, dict):
            errors.append(f"run[{i}] not an object")
            continue
        aid = r.get("agent_id")
        role = r.get("role")
        if not aid or not role:
            errors.append(f"run[{i}] missing agent_id or role")
            continue
        if role in VERIFIER_ROLES and aid in implementers:
            errors.append(f"{role} agent {aid!r} also acted as implementer")
        if role == "test-verifier-improver":
            for v in r.get("verifies") or []:
                if v == aid:
                    errors.append(f"verifier {aid!r} lists itself in 'verifies'")
                if v not in implementers:
                    errors.append(f"verifier {aid!r} references unknown implementer {v!r}")
        seen_ids.add(aid)

        rp = r.get("report_path")
        if rp:
            p = root / rp
            if not p.exists():
                errors.append(f"run[{i}] report {rp!r} missing")
            elif r.get("report_hash") and r["report_hash"] != f"sha256:{_sha256(p)}":
                errors.append(f"run[{i}] report hash mismatch for {rp}")

    return _fail(errors)


if __name__ == "__main__":
    sys.exit(main())
