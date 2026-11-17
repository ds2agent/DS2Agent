"""Synthetic contract fixtures only: these tests never build or initialize hardware."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import verify_board_capabilities as board_verifier
import verify_mcp_server as verifier


def digest(value):
    return hashlib.sha256(value).hexdigest()


def canonical_digest(value):
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":"), allow_nan=False).encode("utf-8"))


class Delivery:
    """Disposable generated-delivery shape, with independently computed identities."""
    def __init__(self, root):
        self.root = Path(root)
        self.server = self.root / "agent_mcp.py"
        self.server.write_text("# Synthetic contract fixture\n", encoding="utf-8")
        self.put("capabilities/board.md", b"Synthetic board evidence; no hardware exercised.\n")
        self.mod = SimpleNamespace(__file__=str(self.server), MCP_TOOLS={}, BOARD_CAPABILITIES={})
        self.manifests = {}

    def put(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def board(self, board_id="fixture", devices=("sensor_a", "sensor_b")):
        bound = []
        for index, device_id in enumerate(devices):
            driver_root = f"devices/{device_id}/mcp"
            pairs = []
            # Non-ASCII portable include name exercises the feedback hash encoding.
            files = ["driver/value.c", "driver/value.h", "driver/données.inc"]
            for filename, content in zip(files, (
                    f"int value(void) {{ return {index}; }}\n".encode(),
                    b"int value(void);\n", b"/* synthetic portable table */\n")):
                self.put(f"{driver_root}/{filename}", content)
                pairs.append([filename, digest(content)])
            bound.append({"device_id": device_id, "driver_root": driver_root,
                          "driver_files": files, "driver_sha256": canonical_digest(sorted(pairs)),
                          "bus_id": "bus0", "address7": 32 + index})
        binding = {
            "profile_id": "synthetic-profile", "board_revision": "fixture-revision", "mcu": "fixture-mcu",
            "pins": {"scl": "synthetic-pin"}, "clocks": {"source": "synthetic-clock"},
            "buses": {"bus0": {"kind": "i2c"}}, "control": {"transport": "synthetic"},
            "hal_sha256": digest(b"synthetic HAL inputs"), "plan_sha256": digest(b"synthetic plan inputs"),
            "devices": bound,
        }
        roles = {
            "init_source": "board_init.c", "init_header": "board_init.h",
            "hal_source": "device_hal.c", "hal_header": "device_hal.h",
            "build_recipe": "build.txt", "startup": "startup.s", "linker": "memory.ld",
            "app_source": "main.c", "control_source": "control.c",
            "control_header": "control.h", "binding_header": "board_binding.h",
        }
        artifacts = []
        for role, filename in roles.items():
            relative = f"boards/{board_id}/firmware/{filename}"
            content = f"Synthetic {board_id} {role} contract bytes\n".encode()
            self.put(relative, content)
            artifacts.append({"role": role, "path": relative, "sha256": digest(content)})
        tools = {action: f"board__{board_id}__{action}" for action in board_verifier.ACTIONS}
        for action, name in tools.items():
            self.mod.MCP_TOOLS[name] = {
                "name": name, "model": "driver", "scenarios": ["board-level"],
                "board_id": board_id, "board_action": action,
                "description": "Synthetic board contract call", "source": "Synthetic fixture, not hardware",
                "params": {"type": "object", "additionalProperties": False},
                "fn": lambda: {"backend": "model", "physical": False},
                "acceptance": [{"args": {}, "expect": {"backend": "model", "physical": False}}],
            }
        self.mod.BOARD_CAPABILITIES[board_id] = f"boards/{board_id}/board.json"
        manifest = {"schema": 1, "board_id": board_id, "sources": ["synthetic contract source"],
                    "binding": binding, "binding_sha256": canonical_digest(binding), "tools": tools,
                    "artifacts": artifacts, "evidence": {
                        "target_build": {"status": "not_run", "reason": "no target toolchain in fixture"},
                        "hardware_init": {"status": "not_run", "reason": "no physical hardware in fixture"},
                    }}
        self.manifests[board_id] = manifest
        self.save(board_id)
        return manifest

    def save(self, board_id="fixture", rebind=False):
        manifest = self.manifests[board_id]
        if rebind:
            manifest["binding_sha256"] = canonical_digest(manifest["binding"])
        self.put(self.mod.BOARD_CAPABILITIES[board_id],
                 json.dumps(manifest, ensure_ascii=False).encode("utf-8"))

    def physical_record(self, board_id="fixture"):
        # Tests the shape/identity boundary only, never real physical evidence.
        manifest = self.manifests[board_id]
        content = b"Synthetic firmware identity, not an executable image\n"
        relative = f"boards/{board_id}/artifacts/firmware.elf"
        self.put(relative, content)
        manifest["artifacts"].append({"role": "firmware", "path": relative, "sha256": digest(content)})
        manifest["evidence"] = {
            "target_build": {"status": "passed", "toolchain": "synthetic-record-only"},
            "hardware_init": {"status": "passed", "physical": True, "state": "ready", "board_id": board_id,
                              "binding_sha256": manifest["binding_sha256"], "firmware_sha256": digest(content),
                              "observation": "synthetic test record; no hardware exercised"},
        }
        self.save(board_id)


class BoardContractTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.delivery = Delivery(temp.name)
        self.manifest = self.delivery.board()

    def check(self):
        result = board_verifier.verify_board_capabilities(self.delivery.mod)
        json.dumps(result, allow_nan=False)
        return result

    def assert_failed(self, diagnostic):
        result = self.check()
        self.assertEqual(result["status"], "failed")
        self.assertIn(diagnostic, "\n".join(result["errors"]))
        return result

    def test_valid_metadata_keeps_target_and_hardware_explicitly_not_run(self):
        result = self.check()
        self.assertEqual(result["status"], "passed", result["errors"])
        board = result["boards"]["fixture"]
        self.assertEqual(board["device_ids"], ["sensor_a", "sensor_b"])
        self.assertEqual(board["target_build"]["status"], "not_run")
        self.assertEqual(board["hardware_init"]["status"], "not_run")

    def test_resolution_is_relative_to_server_and_survives_relocation(self):
        with tempfile.TemporaryDirectory() as elsewhere:
            original = os.getcwd()
            try:
                os.chdir(elsewhere)
                self.assertEqual(self.check()["status"], "passed")
            finally:
                os.chdir(original)
        # Package relocation leaves identities intact without any manifest rewrite.
        import shutil
        with tempfile.TemporaryDirectory() as parent:
            relocated = Path(parent) / "delivery"
            shutil.copytree(self.delivery.root, relocated)
            self.delivery.mod.__file__ = str(relocated / "agent_mcp.py")
            self.assertEqual(self.check()["status"], "passed")

    def test_each_portable_device_drift_is_detected(self):
        for device in self.manifest["binding"]["devices"]:
            with self.subTest(device=device["device_id"]):
                path = self.delivery.root / device["driver_root"] / device["driver_files"][0]
                before = path.read_bytes()
                path.write_bytes(before + b"/* changed */\n")
                self.assert_failed("portable driver drift")
                path.write_bytes(before)
        self.assertEqual(self.check()["status"], "passed")

    def test_board_artifact_drift_and_missing_required_role_fail(self):
        artifact = self.manifest["artifacts"][0]
        path = self.delivery.root / artifact["path"]
        before = path.read_bytes()
        path.write_bytes(before + b"changed")
        self.assert_failed("artifact sha256 mismatch")
        path.write_bytes(before)
        self.manifest["artifacts"].pop(0)
        self.delivery.save()
        self.assert_failed("missing roles")

    def test_app_firmware_artifacts_are_required(self):
        baseline = copy.deepcopy(self.manifest)
        for role in ("app_source", "control_source", "control_header", "binding_header"):
            with self.subTest(role=role):
                manifest = copy.deepcopy(baseline)
                manifest["artifacts"] = [item for item in manifest["artifacts"]
                                         if item["role"] != role]
                self.delivery.manifests["fixture"] = manifest
                self.delivery.save()
                self.assert_failed(f"missing roles ['{role}']")
        self.delivery.manifests["fixture"] = copy.deepcopy(baseline)
        self.delivery.save()
        self.assertEqual(self.check()["status"], "passed")

    def test_binding_digest_detects_config_and_identity_drift(self):
        self.manifest["binding"]["clocks"]["source"] = "changed"
        self.delivery.save()
        self.assert_failed("binding_sha256 mismatch")

    def test_duplicate_devices_unknown_bus_and_incomplete_drivers_fail(self):
        baseline = copy.deepcopy(self.manifest)
        for change, diagnostic in (
            (lambda m: m["binding"]["devices"].append(copy.deepcopy(m["binding"]["devices"][0])), "duplicate device_id"),
            (lambda m: m["binding"]["devices"][0].update(bus_id="missing"), "unknown bus_id"),
            (lambda m: m["binding"]["devices"][0].update(device_id="board"), "reserved board__"),
            (lambda m: m["binding"]["devices"][0].update(driver_files=["driver/value.c"]), "C source and header"),
            (lambda m: m["binding"]["devices"][0].update(driver_files=["driver/value.c", "driver/value.c"]), "duplicate driver file"),
        ):
            with self.subTest(diagnostic=diagnostic):
                self.delivery.manifests["fixture"] = copy.deepcopy(baseline)
                change(self.delivery.manifests["fixture"])
                self.delivery.save(rebind=True)
                self.assert_failed(diagnostic)

    def test_unsafe_manifest_driver_and_artifact_paths_fail(self):
        baseline = copy.deepcopy(self.manifest)
        for bad in ("../outside.c", "/absolute.c", "C:/absolute.c", "driver\\value.c", "driver/../value.c", "./value.c", "driver//value.c"):
            with self.subTest(path=bad):
                manifest = copy.deepcopy(baseline)
                manifest["binding"]["devices"][0]["driver_files"][0] = bad
                self.delivery.manifests["fixture"] = manifest
                self.delivery.save(rebind=True)
                self.assert_failed("path")
        self.delivery.manifests["fixture"] = copy.deepcopy(baseline)
        self.delivery.manifests["fixture"]["artifacts"][0]["path"] = "../outside.c"
        self.delivery.save()
        self.assert_failed("path")
        self.delivery.mod.BOARD_CAPABILITIES["fixture"] = "../board.json"
        self.assert_failed("path")

    def test_symlink_escape_fails_when_platform_supports_links(self):
        with tempfile.TemporaryDirectory() as elsewhere:
            outside = Path(elsewhere) / "outside.c"
            outside.write_bytes(b"external bytes")
            link = self.delivery.root / "escape.c"
            try:
                link.symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            self.manifest["artifacts"][0].update(path="escape.c", sha256=digest(outside.read_bytes()))
            self.delivery.save()
            self.assert_failed("escapes delivery root")

    def test_missing_board_projection_and_malformed_manifest_fail(self):
        path = self.delivery.root / "capabilities/board.md"
        path.unlink()
        self.assert_failed("board capability output")
        path.write_text("synthetic", encoding="utf-8")
        manifest_path = self.delivery.root / self.delivery.mod.BOARD_CAPABILITIES["fixture"]
        for value, diagnostic in (
                ("[]", "nonempty object"), ("{", "JSONDecodeError"),
                ('{"schema":1,"schema":1}', "duplicate JSON key"),
                ('{"schema":NaN}', "non-finite JSON constant"),
                ('{"schema":1,"overflow":1e999}', "non-finite JSON number")):
            with self.subTest(value=value):
                manifest_path.write_text(value, encoding="utf-8")
                self.assert_failed(diagnostic)

    def test_orphan_unknown_and_wrong_route_tools_fail(self):
        name = "board__fixture__init"
        entry = self.delivery.mod.MCP_TOOLS[name]
        entry["board_id"] = "other"
        self.assert_failed("routing metadata")
        entry["board_id"] = "fixture"
        entry["model"] = "knowledge"
        self.assert_failed("driver model")
        entry["model"] = "driver"
        self.delivery.mod.MCP_TOOLS["sensor_a__init"] = self.delivery.mod.MCP_TOOLS.pop(name)
        self.assert_failed("missing board tool")
        self.delivery.mod.MCP_TOOLS[name] = self.delivery.mod.MCP_TOOLS.pop("sensor_a__init")
        self.delivery.mod.MCP_TOOLS["board__fixture__extra"] = copy.copy(entry)
        self.assert_failed("orphan or unknown")
        del self.delivery.mod.MCP_TOOLS["board__fixture__extra"]
        self.delivery.mod.MCP_TOOLS["sensor_a__init"] = copy.copy(entry)
        self.assert_failed("metadata on misrouted tool")
        del self.delivery.mod.MCP_TOOLS["sensor_a__init"]
        self.delivery.mod.BOARD_CAPABILITIES = {}
        self.assert_failed("nonempty BOARD_CAPABILITIES")

    def test_multiple_boards_keep_separate_manifests_and_evidence_identities(self):
        second = self.delivery.board("other", ("sensor_c",))
        self.delivery.physical_record("fixture")
        self.delivery.physical_record("other")
        self.assertEqual(self.check()["status"], "passed")
        second["evidence"]["hardware_init"]["board_id"] = "fixture"
        self.delivery.save("other")
        result = self.assert_failed("mismatched board_id")
        self.assertEqual(result["boards"]["fixture"]["status"], "passed")
        self.assertEqual(result["boards"]["other"]["status"], "failed")

    def test_synthetic_matched_physical_record_and_stale_evidence_boundaries(self):
        self.delivery.physical_record()
        self.assertEqual(self.check()["status"], "passed")
        baseline = copy.deepcopy(self.manifest)
        for key, value in (("board_id", "other"), ("binding_sha256", "0" * 64),
                           ("firmware_sha256", "0" * 64), ("physical", False), ("state", "unknown"),
                           ("backend", "native"), ("backend", "model"), ("observation", "")):
            with self.subTest(key=key, value=value):
                self.delivery.manifests["fixture"] = copy.deepcopy(baseline)
                self.delivery.manifests["fixture"]["evidence"]["hardware_init"][key] = value
                self.delivery.save()
                self.assert_failed("evidence.hardware_init")

    def test_target_build_and_hardware_records_cannot_overstate_readiness(self):
        baseline = copy.deepcopy(self.manifest)
        cases = (
            ({"target_build": {"status": "passed", "toolchain": "synthetic"}}, "firmware artifact"),
            ({"target_build": {"status": "not_run"}}, "needs a reason"),
            ({"target_build": {"status": "failed", "reason": "synthetic failure"}}, "failed: synthetic failure"),
            ({"hardware_init": {"status": "passed", "physical": True, "state": "ready"}}, "requires passed target_build"),
            ({"hardware_init": {"status": "not_run", "reason": "synthetic", "physical": True, "state": "ready"}}, "claims physical readiness"),
            ({"hardware_init": {"status": "not_run", "reason": "synthetic", "physical": "true"}}, "physical must be boolean"),
            ({"hardware_init": {"status": "PASS"}}, "invalid status"),
        )
        for update, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic):
                self.delivery.manifests["fixture"] = copy.deepcopy(baseline)
                self.delivery.manifests["fixture"]["evidence"].update(update)
                self.delivery.save()
                self.assert_failed(diagnostic)
        self.delivery.manifests["fixture"] = copy.deepcopy(baseline)
        self.delivery.physical_record()
        manifest = self.delivery.manifests["fixture"]
        manifest["evidence"]["target_build"].pop("toolchain")
        self.delivery.save()
        self.assert_failed("requires toolchain")

    def test_no_board_and_malformed_registries_remain_distinct(self):
        for attributes in ({}, {"BOARD_CAPABILITIES": {}}):
            with self.subTest(attributes=attributes):
                mod = SimpleNamespace(MCP_TOOLS={}, **attributes)
                self.assertEqual(board_verifier.verify_board_capabilities(mod)["status"], "not-requested")
        for registry in (None, [], "boards", {7: "boards/fixture/board.json"}):
            with self.subTest(registry=registry):
                self.delivery.mod.BOARD_CAPABILITIES = registry
                self.assertEqual(self.check()["status"], "failed")

    def test_malformed_contract_fields_and_duplicate_artifact_paths_fail(self):
        baseline = copy.deepcopy(self.manifest)
        for change, diagnostic in (
            (lambda m: m.update(schema=True), "schema must be 1"),
            (lambda m: m.update(sources=[]), "source-reference strings"),
            (lambda m: m.update(binding=[]), "binding: expected nonempty object"),
            (lambda m: m["binding"].update(hal_sha256="A" * 64), "lowercase SHA-256"),
            (lambda m: m["tools"].update(init="sensor_a__init"), "inconsistent board tool routing"),
            (lambda m: m["artifacts"].append(copy.deepcopy(m["artifacts"][0])), "duplicate artifact path"),
            (lambda m: m["artifacts"][0].update(sha256="invalid"), "lowercase SHA-256"),
        ):
            with self.subTest(diagnostic=diagnostic):
                self.delivery.manifests["fixture"] = copy.deepcopy(baseline)
                change(self.delivery.manifests["fixture"])
                self.delivery.save(rebind=True)
                self.assert_failed(diagnostic)

    def test_swapping_device_driver_identities_is_not_accepted(self):
        first, second = self.manifest["binding"]["devices"]
        self.assertNotEqual(first["driver_sha256"], second["driver_sha256"])
        first["driver_sha256"], second["driver_sha256"] = second["driver_sha256"], first["driver_sha256"]
        self.delivery.save(rebind=True)
        self.assert_failed("portable driver drift")

    @unittest.skipIf(verifier.validators is None, "jsonschema is required")
    def test_cli_reports_metadata_success_without_claiming_build_or_hardware_pass(self):
        console = io.StringIO()
        argv = [str(self.delivery.server), "--project-root", str(self.delivery.root),
                "--models", "driver", "--scenarios", "board-level"]
        with patch.object(verifier, "_load", return_value=self.delivery.mod):
            with patch.object(verifier.importlib.util, "find_spec", return_value=None):
                with contextlib.redirect_stdout(console):
                    self.assertEqual(verifier.main(argv), 0)
        report = json.loads((self.delivery.root / "tests/summary/verify_mcp_server.json").read_text(encoding="utf-8"))
        self.assertTrue(report["pass"])
        self.assertEqual(report["board"]["boards"]["fixture"]["hardware_init"]["status"], "not_run")

    @unittest.skipIf(verifier.validators is None, "jsonschema is required")
    def test_saved_specialization_drift_is_checked_after_calls(self):
        artifact = self.manifest["artifacts"][0]
        def specialize():
            (self.delivery.root / artifact["path"]).write_bytes(b"changed during saved call")
            return {"backend": "model", "physical": False}
        self.delivery.mod.MCP_TOOLS["board__fixture__specialize_driver"]["fn"] = specialize
        with patch.object(verifier.importlib.util, "find_spec", return_value=None):
            result = verifier.verify(self.delivery.mod, ("driver",), ("board-level",))
        self.assertTrue(all(case["status"] == "passed" for case in result["acceptance"]))
        self.assertFalse(result["pass"])
        self.assertIn("artifact sha256 mismatch", "\n".join(result["errors"]))

    @unittest.skipIf(verifier.validators is None, "jsonschema is required")
    def test_board_tools_still_require_schema_and_saved_acceptance(self):
        entry = self.delivery.mod.MCP_TOOLS["board__fixture__init"]
        entry["params"] = {"type": "invalid"}
        with patch.object(verifier.importlib.util, "find_spec", return_value=None):
            result = verifier.verify(self.delivery.mod, ("driver",), ("board-level",))
        self.assertFalse(result["pass"])
        self.assertEqual(result["board"]["status"], "passed")
        self.assertIn("invalid params schema", "\n".join(result["errors"]))


if __name__ == "__main__":
    unittest.main()
