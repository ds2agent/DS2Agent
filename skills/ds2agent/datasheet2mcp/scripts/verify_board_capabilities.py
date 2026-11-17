"""Validate generated board delivery identities, not firmware or physical behavior.

Called after saved acceptance by verify_mcp_server. No board code is executed here.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re


ACTIONS = ("specialize_driver", "init", "get_state")
REQUIRED_ROLES = {
    "init_source", "init_header", "hal_source", "hal_header", "build_recipe",
    "startup", "linker", "app_source", "control_source", "control_header",
    "binding_header",
}
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _identifier(value, label):
    _require(isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None
             and "__" not in value, f"{label}: invalid namespace identifier")


def _digest(value, label):
    _require(isinstance(value, str) and SHA256.fullmatch(value) is not None,
             f"{label}: expected lowercase SHA-256")


def _object(value, label):
    _require(isinstance(value, dict) and bool(value), f"{label}: expected nonempty object")
    return value


def _path(root, value, label, directory=False):
    _require(isinstance(value, str) and bool(value) and not any(c in value for c in "\\:\x00"),
             f"{label}: expected portable relative path")
    _require(all(part not in ("", ".", "..") for part in value.split("/")),
             f"{label}: unsafe relative path")
    path = (root / value).resolve()
    _require(path.is_relative_to(root), f"{label}: path escapes delivery root")
    _require(path.is_dir() if directory else path.is_file(),
             f"{label}: missing regular {'directory' if directory else 'file'}: {value}")
    return path


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError(f"non-finite JSON constant: {value}")

def _finite_float(value):
    number = float(value)
    _require(math.isfinite(number), f"non-finite JSON number: {value}")
    return number



def _load(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object,
                      parse_constant=_invalid_constant, parse_float=_finite_float)


def _devices(root, binding):
    devices = binding.get("devices")
    _require(isinstance(devices, list) and bool(devices), "binding.devices: expected nonempty list")
    names = set()
    for index, device in enumerate(devices):
        label = f"binding.devices[{index}]"
        _object(device, label)
        device_id = device.get("device_id")
        _identifier(device_id, f"{label}.device_id")
        _require(device_id != "board", f"{label}: device_id collides with reserved board__ namespace")
        _require(device_id not in names, f"{label}: duplicate device_id {device_id}")
        names.add(device_id)
        driver_root = _path(root, device.get("driver_root"), f"{label}.driver_root", directory=True)
        bus_id = device.get("bus_id")
        _require(isinstance(bus_id, str) and bus_id in binding["buses"], f"{label}: unknown bus_id")
        files = device.get("driver_files")
        _require(isinstance(files, list) and bool(files), f"{label}.driver_files: expected nonempty list")
        pairs, seen, resolved = [], set(), set()
        suffixes = set()
        for relative in files:
            path = _path(driver_root, relative, f"{label}.driver_files")
            _require(relative not in seen and path not in resolved, f"{label}: duplicate driver file")
            seen.add(relative)
            resolved.add(path)
            suffixes.add(path.suffix)
            pairs.append([relative, _hash(path)])
        _require({".c", ".h"} <= suffixes, f"{label}: driver_files require C source and header")
        _digest(device.get("driver_sha256"), f"{label}.driver_sha256")
        actual = _json_hash(sorted(pairs))
        _require(actual == device["driver_sha256"], f"{label}: driver_sha256 mismatch (portable driver drift)")
    return sorted(names)


def _artifacts(root, manifest):
    artifacts = manifest.get("artifacts")
    _require(isinstance(artifacts, list) and bool(artifacts), "artifacts: expected nonempty list")
    paths, resolved, roles = set(), set(), {}
    for index, artifact in enumerate(artifacts):
        label = f"artifacts[{index}]"
        _object(artifact, label)
        role = artifact.get("role")
        _require(_text(role), f"{label}.role: expected nonempty string")
        path = _path(root, artifact.get("path"), f"{label}.path")
        _require(artifact["path"] not in paths and path not in resolved, f"{label}: duplicate artifact path")
        paths.add(artifact["path"])
        resolved.add(path)
        _digest(artifact.get("sha256"), f"{label}.sha256")
        _require(_hash(path) == artifact["sha256"], f"{label}: artifact sha256 mismatch: {artifact['path']}")
        roles.setdefault(role, []).append(artifact)
    _require(REQUIRED_ROLES <= set(roles), f"artifacts: missing roles {sorted(REQUIRED_ROLES - set(roles))}")
    _require(len(roles.get("firmware", [])) <= 1, "artifacts: firmware role must be unambiguous")
    return roles


def _evidence(manifest, roles, result):
    evidence = _object(manifest.get("evidence"), "evidence")
    for name in ("target_build", "hardware_init"):
        record = _object(evidence.get(name), f"evidence.{name}")
        status = record.get("status")
        _require(status in ("passed", "failed", "not_run"), f"evidence.{name}: invalid status")
        if status != "passed":
            _require(_text(record.get("reason")), f"evidence.{name}: {status} needs a reason")
    target, hardware = evidence["target_build"], evidence["hardware_init"]
    _require("physical" not in hardware or type(hardware["physical"]) is bool,
             "evidence.hardware_init: physical must be boolean")
    if target["status"] == "passed":
        _require("firmware" in roles, "evidence.target_build: passed requires firmware artifact")
        _require(_text(target.get("toolchain")), "evidence.target_build: passed requires toolchain")
        _require(target.get("backend") not in ("native", "model", "qemu", "simulation"),
                 "evidence.target_build: native/model execution is not a target build")
    if hardware["status"] == "passed":
        _require(target["status"] == "passed", "evidence.hardware_init: requires passed target_build")
        _require(hardware.get("physical") is True and hardware.get("state") == "ready",
                 "evidence.hardware_init: passed requires physical:true and state:ready")
        _require(hardware.get("backend") not in ("native", "model", "qemu", "simulation"),
                 "evidence.hardware_init: model/native evidence is not physical readiness")
        for key in ("board_id", "binding_sha256"):
            _require(hardware.get(key) == manifest[key], f"evidence.hardware_init: stale or mismatched {key}")
        _require(hardware.get("firmware_sha256") == roles["firmware"][0]["sha256"],
                 "evidence.hardware_init: stale or mismatched firmware_sha256")
        _require(_text(hardware.get("observation")) or _text(hardware.get("source")),
                 "evidence.hardware_init: passed requires observation/source reference")
    else:
        _require(hardware.get("state") != "ready" or hardware.get("physical") is False,
                 "evidence.hardware_init: non-passed evidence claims physical readiness")
    for name in ("target_build", "hardware_init"):
        result[name] = dict(evidence[name])
        if evidence[name]["status"] == "failed":
            result["errors"].append(f"evidence.{name}: failed: {evidence[name]['reason']}")


def _board(root, board_id, manifest_path, tools, result):
    _identifier(board_id, "board_id")
    path = _path(root, manifest_path, "board manifest")
    _require(manifest_path == f"boards/{board_id}/board.json", "board manifest: expected boards/<board_id>/board.json")
    manifest = _object(_load(path), "manifest")
    _require(type(manifest.get("schema")) is int and manifest["schema"] == 1, "manifest.schema must be 1")
    _require(manifest.get("board_id") == board_id, "manifest.board_id differs from registry board_id")
    sources = manifest.get("sources")
    _require(isinstance(sources, list) and bool(sources) and all(_text(item) for item in sources),
             "manifest.sources must be nonempty source-reference strings")
    binding = _object(manifest.get("binding"), "binding")
    for key in ("profile_id", "board_revision", "mcu"):
        _require(_text(binding.get(key)), f"binding.{key}: expected nonempty string")
    for key in ("pins", "clocks", "buses", "control"):
        _object(binding.get(key), f"binding.{key}")
    for key in ("hal_sha256", "plan_sha256"):
        _digest(binding.get(key), f"binding.{key}")
    _digest(manifest.get("binding_sha256"), "binding_sha256")
    _require(_json_hash(binding) == manifest["binding_sha256"], "binding_sha256 mismatch")
    result["binding_sha256"] = manifest["binding_sha256"]
    result["device_ids"] = _devices(root, binding)
    expected = {action: f"board__{board_id}__{action}" for action in ACTIONS}
    _require(manifest.get("tools") == expected, "manifest.tools: inconsistent board tool routing")
    for action, name in expected.items():
        entry = tools.get(name)
        _require(isinstance(entry, dict), f"{name}: missing board tool")
        _require(entry.get("name") == name and entry.get("board_id") == board_id
                 and entry.get("board_action") == action, f"{name}: inconsistent board tool routing metadata")
        _require(entry.get("model") == "driver" and isinstance(entry.get("scenarios"), list)
                 and "board-level" in entry["scenarios"], f"{name}: requires driver model and board-level scenario")
    roles = _artifacts(root, manifest)
    _evidence(manifest, roles, result)


def verify_board_capabilities(mod):
    """Return JSON-safe board metadata/evidence outcomes, including malformed deliveries."""
    result = {"status": "not-requested", "errors": [], "boards": {}}
    tools = getattr(mod, "MCP_TOOLS", {})
    tools = tools if isinstance(tools, dict) else {}
    board_names = {name for name in tools if isinstance(name, str) and name.startswith("board__")}
    board_metadata = any(isinstance(entry, dict) and "board_action" in entry for entry in tools.values())
    supplied = hasattr(mod, "BOARD_CAPABILITIES")
    registry = getattr(mod, "BOARD_CAPABILITIES", {})
    if not supplied and not board_names and not board_metadata:
        return result
    if isinstance(registry, dict) and not registry and not board_names and not board_metadata:
        return result
    result["status"] = "failed"
    try:
        _require(isinstance(registry, dict), "BOARD_CAPABILITIES must be a dictionary")
        _require(bool(registry), "board__ tools require nonempty BOARD_CAPABILITIES")
        server = getattr(mod, "__file__", None)
        _require(isinstance(server, (str, Path)), "board verification requires server module.__file__")
        root = Path(server).resolve().parent
        _path(root, "capabilities/board.md", "board capability output")
        expected_names = set()
        for board_id, manifest_path in registry.items():
            # Validate keys before using them as JSON summary object keys.
            _identifier(board_id, "BOARD_CAPABILITIES board_id")
            expected_names.update(f"board__{board_id}__{action}" for action in ACTIONS)
            board = {"status": "failed", "errors": [],
                     "target_build": {"status": "not_run", "reason": "manifest validation incomplete"},
                     "hardware_init": {"status": "not_run", "reason": "manifest validation incomplete"}}
            result["boards"][board_id] = board
            try:
                _board(root, board_id, manifest_path, tools, board)
            except Exception as exc:
                board["errors"].append(f"{type(exc).__name__}: {exc}")
            if not board["errors"]:
                board["status"] = "passed"
            result["errors"].extend(f"{board_id}: {error}" for error in board["errors"])
        for name in sorted(board_names - expected_names):
            result["errors"].append(f"{name}: orphan or unknown board tool")
        for name, entry in tools.items():
            if isinstance(entry, dict) and "board_action" in entry:
                _require(isinstance(name, str) and name in expected_names,
                         f"{name!r}: board metadata on misrouted tool")
    except Exception as exc:
        result["errors"].append(f"{type(exc).__name__}: {exc}")
    if not result["errors"]:
        result["status"] = "passed"
    return result
