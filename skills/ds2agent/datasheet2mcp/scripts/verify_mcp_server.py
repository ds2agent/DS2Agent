#!/usr/bin/env python3
"""Execute a generated MCP server's saved acceptance contract.

Requires jsonschema. The optional mcp SDK enables actual build/list_tools checks.
Only run this helper on trusted generated code: imports and saved calls execute code.
"""
from __future__ import annotations

import argparse
import asyncio
from collections.abc import Mapping
from copy import deepcopy
import importlib.util
import inspect
import json
import math
import sys
from pathlib import Path

from verify_board_capabilities import verify_board_capabilities

try:
    from jsonschema import validators
except ImportError:
    validators = None

ALL_MODELS = ("knowledge", "driver", "behavior")
ALL_SCENARIOS = (
    "board-level",
    "digital-twin",
    "hardware-calibration",
    "mcp-interface",
    "trial-running",
    "reference-circuit",
)
REQUIRED_TOOL_KEYS = {"name", "model", "description", "params", "source", "fn", "acceptance"}


def _load(path: str):
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("_ds2a_server_under_test", path)
    if spec is None or spec.loader is None:
        raise ValueError("server must be an importable Python module")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)
    return mod


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _json_value(value, path="$"):
    """Reject Python-only values, non-string object keys, NaN and infinity."""
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{path}: non-finite float")
        return
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path}: object keys must be strings")
            _json_value(child, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _json_value(child, f"{path}[{index}]")
        return
    raise ValueError(f"{path}: not a JSON value ({type(value).__name__})")


def _tolerance(record):
    if "tolerance" not in record:
        return None
    value = record["tolerance"]
    if not isinstance(value, dict):
        raise ValueError("tolerance must be an object")
    if set(value) - {"abs", "rel", "source"}:
        raise ValueError("tolerance accepts only abs, rel and source")
    if not _text(value.get("source")) or not ({"abs", "rel"} & set(value)):
        raise ValueError("tolerance needs abs and/or rel plus a nonempty source")
    for key in ("abs", "rel"):
        if key in value:
            number = value[key]
            if type(number) not in (int, float) or number < 0:
                raise ValueError(f"tolerance.{key} must be finite and nonnegative")
            if isinstance(number, float) and not math.isfinite(number):
                raise ValueError(f"tolerance.{key} must be finite and nonnegative")
    return value


def _integer_scope(record):
    mask = record.get("mask")
    valid = record.get("valid")
    if mask is not None and valid is not None:
        raise ValueError("integer scope accepts either mask or valid, not both")
    if mask is not None and (type(mask) is not int or mask < 0):
        raise ValueError("mask must be a nonnegative integer")
    if valid is not None:
        if not isinstance(valid, list) or not valid:
            raise ValueError("valid must be a nonempty list of integers")
        if any(type(value) is not int for value in valid):
            raise ValueError("valid must contain only integers")
    return mask, valid


def _match(actual, expected, path="$", tolerance=None, applied=None, partial=True,
           mask=None, valid=None):
    errors = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected object, got {type(actual).__name__}"]
        if not partial and set(actual) != set(expected):
            errors.append(f"{path}: object keys differ")
        for key, value in expected.items():
            if key not in actual:
                errors.append(f"{path}.{key}: missing key")
            else:
                errors.extend(_match(actual[key], value, f"{path}.{key}",
                                     tolerance, applied, partial, mask, valid))
        return errors
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return [f"{path}: expected list, got {type(actual).__name__}"]
        if len(actual) != len(expected):
            return [f"{path}: length {len(actual)} != {len(expected)}"]
        for index, (a, e) in enumerate(zip(actual, expected)):
            errors.extend(_match(a, e, f"{path}[{index}]", tolerance, applied, partial,
                                 mask, valid))
        return errors
    if type(expected) is bool:
        matches = type(actual) is bool and actual is expected
    elif type(expected) is int:
        matches = type(actual) is int
        if matches and valid is not None:
            matches = actual in valid
            if applied is not None:
                applied.append({"path": path, "valid": valid})
        elif matches and mask is not None:
            matches = (actual & mask) == (expected & mask)
            if applied is not None:
                applied.append({"path": path, "mask": mask})
        else:
            matches = matches and actual == expected
    elif type(expected) is float:
        matches = type(actual) in (int, float)
        if matches and tolerance is not None:
            absolute, relative = tolerance.get("abs", 0), tolerance.get("rel", 0)
            # Use only the stated bound; never invent an epsilon or round large ints.
            matches = abs(actual - expected) <= max(absolute, relative * abs(expected))
            if applied is not None:
                applied.append({"path": path, **tolerance})
        else:
            matches = matches and actual == expected
    else:
        matches = type(actual) is type(expected) and actual == expected
    return [] if matches else [f"{path}: {actual!r} != {expected!r}"]


async def _await_value(value):
    return await value


def _resolve(value):
    return asyncio.run(_await_value(value)) if inspect.isawaitable(value) else value


def _validator(schema):
    if validators is None:
        raise ValueError("jsonschema is required; install it in PROJECT_PYTHON")
    if not isinstance(schema, dict):
        raise ValueError("params must be a JSON Schema object")
    _json_value(schema)
    if "$schema" in schema and validators.validator_for(schema, default=None) is None:
        raise ValueError("params uses an unsupported JSON Schema dialect")
    cls = validators.validator_for(schema)
    cls.check_schema(schema)
    return cls(schema)


def _snapshot(mod):
    value = getattr(mod, "IMMUTABLE_DATASHEET", None)
    if not isinstance(value, Mapping) or not value:
        raise ValueError("IMMUTABLE_DATASHEET must be a nonempty canonical facts mapping")
    facts = dict(value)
    _json_value(facts)
    return value, json.dumps(facts, sort_keys=True, allow_nan=False)


def _is_refine(name, entry):
    names = (name, getattr(entry.get("fn"), "__name__", ""))
    return any(isinstance(value, str) and "refine" in value.split("_") for value in names)


def _run_case(mod, name, index, entry, case, validator, refine):
    result = {"tool": name, "index": index, "source": entry["source"],
              "status": "failed", "errors": [], "tolerances": []}
    errors = result["errors"]
    before = None
    try:
        if not isinstance(case, dict) or not {"args", "expect"} <= set(case):
            raise ValueError("acceptance case must explicitly contain args and expect")
        if not isinstance(case["args"], dict):
            raise ValueError("args must be an object")
        if "source" in case and not _text(case["source"]):
            raise ValueError("case source must be nonempty")
        result["source"] = case.get("source", entry["source"])
        _json_value(case["args"])
        _json_value(case["expect"])
        tolerance = _tolerance(case)
        mask, valid = _integer_scope(case)
        validator.validate(case["args"])
        result["args"], result["expected"] = deepcopy(case["args"]), deepcopy(case["expect"])
        if refine:
            before = _snapshot(mod)
        try:
            actual = _resolve(entry["fn"](**deepcopy(case["args"])))
            _json_value(actual)
            result["actual"] = deepcopy(actual)
            errors.extend(_match(actual, case["expect"], tolerance=tolerance,
                                 applied=result["tolerances"], mask=mask, valid=valid))
        finally:
            if before is not None:
                immutable = {"tool": name, "index": index, "status": "failed", "errors": []}
                result["immutable"] = immutable
                try:
                    after = _snapshot(mod)
                    # Also inspect the old mapping if a function rebound the module name.
                    old_facts = dict(before[0])
                    _json_value(old_facts)
                    old_content = json.dumps(old_facts, sort_keys=True, allow_nan=False)
                    if after[0] is not before[0]:
                        immutable["errors"].append("IMMUTABLE_DATASHEET was rebound")
                    if after[1] != before[1] or old_content != before[1]:
                        immutable["errors"].append("IMMUTABLE_DATASHEET contents changed")
                except Exception as exc:
                    immutable["errors"].append(f"immutable snapshot: {type(exc).__name__}: {exc}")
                if not immutable["errors"]:
                    immutable["status"] = "passed"
                errors.extend(immutable["errors"])
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
    if not errors:
        result["status"] = "passed"
    return result


def _cross_checks(mod, required):
    result = {"required": required, "status": "not-required", "checks": [], "errors": []}
    hook = getattr(mod, "CROSS_MODEL_CHECKS", None)
    if hook is None and not required:
        return result
    result["status"] = "failed"
    try:
        if not callable(hook):
            raise ValueError("CROSS_MODEL_CHECKS() is required and must be callable")
        checks = _resolve(hook())
        if not isinstance(checks, list) or not checks:
            raise ValueError("CROSS_MODEL_CHECKS must return a nonempty list of check records")
        names = set()
        for index, check in enumerate(checks):
            record = {"index": index, "status": "failed", "errors": [], "tolerances": []}
            result["checks"].append(record)
            try:
                if not isinstance(check, dict) or not {"name", "source", "expected", "actual"} <= set(check):
                    raise ValueError("check requires name, source, expected and actual")
                if not _text(check["name"]) or not _text(check["source"]):
                    raise ValueError("check name and source must be nonempty strings")
                if check["name"] in names:
                    raise ValueError("check names must be unique")
                names.add(check["name"])
                _json_value(check["expected"])
                _json_value(check["actual"])
                tolerance = _tolerance(check)
                mask, valid = _integer_scope(check)
                record.update({key: deepcopy(check[key])
                               for key in ("name", "source", "expected", "actual")})
                record["errors"].extend(_match(check["actual"], check["expected"],
                                              tolerance=tolerance, applied=record["tolerances"],
                                              partial=False, mask=mask, valid=valid))
            except Exception as exc:
                record["errors"].append(f"{type(exc).__name__}: {exc}")
            if not record["errors"]:
                record["status"] = "passed"
            result["errors"].extend(f"check[{index}]: {error}" for error in record["errors"])
    except Exception as exc:
        result["errors"].append(f"{type(exc).__name__}: {exc}")
    if not result["errors"]:
        result["status"] = "passed"
    return result


def _schema_structure(schema):
    """Remove cosmetic annotations only at known JSON Schema nodes.

    Property/definition names and instance payloads (const/default/enum) are data,
    not schemas. Unknown extension keywords remain opaque and compare unchanged.
    """
    if not isinstance(schema, dict):
        return schema
    schema_maps = {"properties", "patternProperties", "$defs", "definitions",
                   "dependentSchemas", "dependencies"}
    schema_values = {"additionalProperties", "unevaluatedProperties", "propertyNames",
                     "additionalItems", "unevaluatedItems", "contains", "not", "if",
                     "then", "else", "contentSchema"}
    schema_or_arrays = {"items", "prefixItems", "allOf", "anyOf", "oneOf",
                        "extends", "type", "disallow"}
    result = {}
    for key, value in schema.items():
        if key in {"title", "description", "$comment", "examples"}:
            continue
        if key in schema_maps and isinstance(value, dict):
            result[key] = {name: _schema_structure(child) for name, child in value.items()}
        elif key in schema_values:
            result[key] = _schema_structure(value)
        elif key in schema_or_arrays:
            result[key] = ([_schema_structure(child) for child in value]
                           if isinstance(value, list) else _schema_structure(value))
        else:
            result[key] = value
    return result


def _schema_identity(schema):
    # JSON encoding also keeps boolean const/default values distinct from integers.
    return json.dumps(_schema_structure(schema), sort_keys=True, allow_nan=False)


def _mcp_check(mod, entries):
    result = {"status": "failed", "errors": [], "tools": []}
    try:
        if importlib.util.find_spec("mcp") is None:
            result.update(status="not-checked", reason="mcp SDK is not installed")
            return result
        build = getattr(mod, "build_server", None)
        if not callable(build):
            raise ValueError("installed mcp SDK requires build_server()")
        server = _resolve(build())
        listing = getattr(server, "list_tools", None)
        if not callable(listing):
            raise ValueError("build_server() result must expose supported list_tools()")
        tools = _resolve(listing())
        if not isinstance(tools, list):
            raise ValueError("list_tools() must return a list of MCP Tool objects")
        exposed = {}
        for tool in tools:
            name = getattr(tool, "name", None)
            schema = getattr(tool, "inputSchema", None)
            if not _text(name) or name in exposed:
                raise ValueError("list_tools() contains a missing or duplicate tool name")
            _validator(schema)
            exposed[name] = schema
        result["tools"] = sorted(exposed)
        if set(exposed) != set(entries):
            result["errors"].append(
                f"tool inventory differs: missing={sorted(set(entries) - set(exposed))}, "
                f"extra={sorted(set(exposed) - set(entries))}")
        for name in sorted(set(exposed) & set(entries)):
            if _schema_identity(exposed[name]) != _schema_identity(entries[name].get("params")):
                result["errors"].append(f"{name}: exposed inputSchema differs from registry params")
    except Exception as exc:
        result["errors"].append(f"{type(exc).__name__}: {exc}")
    if not result["errors"]:
        result["status"] = "passed"
    return result


def verify(mod, models=ALL_MODELS, scenarios=ALL_SCENARIOS):
    """Return JSON evidence; malformed contracts fail rather than silently disappearing."""
    summary = {"pass": False, "errors": [], "tools": [], "models": list(models),
               "scenarios": list(scenarios), "acceptance": [], "refinement": {"checks": []}}
    errors = summary["errors"]
    for label, requested, allowed in (("model", models, ALL_MODELS),
                                      ("scenario", scenarios, ALL_SCENARIOS)):
        for value in requested:
            if value not in allowed:
                errors.append(f"unknown requested {label}: {value!r}")
    if validators is None:
        errors.append("jsonschema is required; install it in PROJECT_PYTHON")
    tools = getattr(mod, "MCP_TOOLS", None)
    if not isinstance(tools, dict) or not tools:
        errors.append("MCP_TOOLS must be a nonempty dictionary")
        tools = {}
    entries, valid, schema_validators = {}, {}, {}
    for name, entry in tools.items():
        prefix = f"tool {name!r}"
        start = len(errors)
        if not _text(name):
            errors.append(f"{prefix}: registry key must be a nonempty string")
            continue
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: entry must be an object")
            continue
        entries[name] = entry
        missing = REQUIRED_TOOL_KEYS - set(entry)
        if missing:
            errors.append(f"{prefix}: missing keys {sorted(missing)}")
        if entry.get("name") != name:
            errors.append(f"{prefix}: name must equal registry key")
        for key in ("description", "source"):
            if not _text(entry.get(key)):
                errors.append(f"{prefix}: {key} must be nonempty")
        if entry.get("model") not in ALL_MODELS:
            errors.append(f"{prefix}: model must be one of {ALL_MODELS}")
        tags = entry.get("scenarios", [])
        if not isinstance(tags, list) or any(tag not in ALL_SCENARIOS for tag in tags):
            errors.append(f"{prefix}: scenarios must be a list of known scenario tags")
        if not callable(entry.get("fn")):
            errors.append(f"{prefix}: fn must be callable")
        if not isinstance(entry.get("acceptance"), list) or not entry["acceptance"]:
            errors.append(f"{prefix}: acceptance must be a nonempty list")
        try:
            schema_validators[name] = _validator(entry.get("params"))
        except Exception as exc:
            errors.append(f"{prefix}: invalid params schema: {type(exc).__name__}: {exc}")
        if len(errors) == start:
            valid[name] = entry
    summary["tools"] = sorted(entries)
    for model in models:
        if not any(entry.get("model") == model for entry in valid.values()):
            errors.append(f"no valid tool for required model {model!r}")
    for scenario in scenarios:
        if not any(scenario in entry.get("scenarios", []) for entry in valid.values()):
            errors.append(f"no valid tool for required scenario {scenario!r}")
    refine_names = [name for name, entry in entries.items() if _is_refine(name, entry)]
    summary["refinement"]["required"] = bool(refine_names)
    for name, entry in entries.items():
        cases = entry.get("acceptance")
        if not isinstance(cases, list):
            continue
        for index, case in enumerate(cases):
            if name not in valid:
                result = {"tool": name, "index": index, "status": "not-run",
                          "errors": ["invalid tool metadata"], "tolerances": []}
            else:
                result = _run_case(mod, name, index, entry, case, schema_validators[name],
                                   name in refine_names)
            summary["acceptance"].append(result)
            errors.extend(f"{name}.acceptance[{index}]: {error}" for error in result["errors"])
            if "immutable" in result:
                summary["refinement"]["checks"].append(result["immutable"])
    for name in refine_names:
        if not any(check["tool"] == name for check in summary["refinement"]["checks"]):
            errors.append(f"{name}: at least one executed refine acceptance with immutable snapshots is required")
    refinement = summary["refinement"]
    refinement["status"] = "not-required"
    if refine_names:
        covered = all(any(check["tool"] == name for check in refinement["checks"])
                      for name in refine_names)
        cases_passed = all(case["status"] == "passed" for case in summary["acceptance"]
                           if case["tool"] in refine_names)
        snapshots_passed = all(check["status"] == "passed" for check in refinement["checks"])
        refinement["status"] = "passed" if covered and cases_passed and snapshots_passed else "failed"
    model_tags = [entry.get("model") for entry in entries.values()]
    summary["cross_model"] = _cross_checks(
        mod, "driver" in model_tags and "behavior" in model_tags)
    errors.extend(f"CROSS_MODEL_CHECKS: {error}" for error in summary["cross_model"]["errors"])
    summary["mcp"] = _mcp_check(mod, entries)
    errors.extend(f"MCP: {error}" for error in summary["mcp"]["errors"])
    # Saved specialization/refinement calls may change the delivered bytes or binding.
    summary["board"] = verify_board_capabilities(mod)
    errors.extend(f"BOARD: {error}" for error in summary["board"]["errors"])
    summary["pass"] = not errors
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("server", help="path to <device>_mcp.py")
    ap.add_argument("--project-root", default=None)
    ap.add_argument("--models", default=",".join(ALL_MODELS), help="comma-separated required models")
    ap.add_argument("--scenarios", default=",".join(ALL_SCENARIOS), help="comma-separated required scenarios")
    args = ap.parse_args(argv)
    models = [value.strip() for value in args.models.split(",") if value.strip()]
    scenarios = [value.strip() for value in args.scenarios.split(",") if value.strip()]
    try:
        summary = verify(_load(args.server), models, scenarios)
    except Exception as exc:
        summary = {"pass": False, "errors": [f"load/verification: {type(exc).__name__}: {exc}"],
                   "acceptance": [], "mcp": {"status": "not-checked"}}
    if args.project_root:
        try:
            out = Path(args.project_root) / "tests" / "summary" / "verify_mcp_server.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(summary, indent=2, allow_nan=False), encoding="utf-8")
        except Exception as exc:
            summary["pass"] = False
            summary["errors"].append(f"writing summary: {type(exc).__name__}: {exc}")
    for error in summary["errors"]:
        print(f"verify_mcp_server: FAIL: {error}")
    for board_id, board in summary.get("board", {}).get("boards", {}).items():
        print(f"verify_mcp_server: BOARD {board_id}: metadata={board['status']} "
              f"target_build={board['target_build']['status']} "
              f"hardware_init={board['hardware_init']['status']}")
    if not summary["pass"]:
        return 1
    print(f"verify_mcp_server: OK ({len(summary['tools'])} tools; MCP {summary['mcp']['status']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
