"""Behavioral regression tests; run with PROJECT_PYTHON -m unittest discover -s scripts."""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import verify_mcp_server as verifier


EMPTY_ARGS = {"type": "object", "properties": {}, "additionalProperties": False}


def tool(name="read_value", model="knowledge", fn=None, expected=7):
    return {
        "name": name,
        "model": model,
        "scenarios": ["mcp-interface"],
        "description": "Read the documented reset value",
        "params": copy.deepcopy(EMPTY_ARGS),
        "source": "datasheet section 4, reset value",
        "fn": fn if fn is not None else lambda: 7,
        "acceptance": [{"args": {}, "expect": expected}],
    }


def module(*entries):
    return SimpleNamespace(MCP_TOOLS={entry["name"]: entry for entry in entries})


@unittest.skipIf(verifier.validators is None, "jsonschema is required")
class ContractTests(unittest.TestCase):
    def check(self, mod, models=("knowledge",), scenarios=("mcp-interface",)):
        # Contract-only tests isolate the explicitly SDK-absent environment.
        with patch.object(verifier.importlib.util, "find_spec", return_value=None):
            result = verifier.verify(mod, models, scenarios)
        json.dumps(result, allow_nan=False)
        return result

    def assert_failed(self, result, diagnostic):
        self.assertFalse(result["pass"])
        self.assertIn(diagnostic, "\n".join(result["errors"]))

    def test_valid_contract_reports_each_case_and_sdk_absence(self):
        entry = tool()
        result = self.check(module(entry))
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["acceptance"][0]["status"], "passed")
        self.assertEqual(result["acceptance"][0]["actual"], 7)
        self.assertEqual(result["mcp"]["status"], "not-checked")
        self.assertEqual(result["board"]["status"], "not-requested")

    def test_malformed_registry_and_entries_are_not_ignored(self):
        for registry in (None, [], {}, {"bad": None}, {12: tool()}, {"bad": []}):
            with self.subTest(registry=registry):
                result = self.check(SimpleNamespace(MCP_TOOLS=registry))
                self.assertFalse(result["pass"])
                self.assertTrue(result["errors"])
        for field, value, diagnostic in (
            ("name", "other", "name must equal"),
            ("description", " ", "description must be nonempty"),
            ("source", None, "source must be nonempty"),
            ("model", [], "model must be one of"),
            ("scenarios", ["made-up"], "known scenario tags"),
            ("scenarios", "mcp-interface", "known scenario tags"),
            ("fn", None, "fn must be callable"),
            ("acceptance", None, "acceptance must be a nonempty list"),
            ("acceptance", [], "acceptance must be a nonempty list"),
        ):
            with self.subTest(field=field, value=value):
                entry = tool()
                entry[field] = value
                # Preserve the original registry key to exercise name disagreement.
                result = self.check(SimpleNamespace(MCP_TOOLS={"read_value": entry}))
                self.assert_failed(result, diagnostic)

    def test_missing_metadata_and_requested_coverage_fail(self):
        entry = tool()
        del entry["params"]
        self.assert_failed(self.check(module(entry)), "missing keys")
        self.assert_failed(self.check(module(tool()), models=("driver",)), "required model")
        self.assert_failed(self.check(module(tool()), scenarios=("digital-twin",)), "required scenario")
        self.assert_failed(self.check(module(tool()), models=("unknown",)), "unknown requested model")
        self.assert_failed(self.check(module(tool()), scenarios=("unknown",)), "unknown requested scenario")

    def test_schema_definition_and_arguments_are_validated_before_execution(self):
        calls = []
        entry = tool(fn=lambda **kwargs: calls.append(kwargs) or 7)
        entry["params"] = {"type": "not-a-type"}
        self.assert_failed(self.check(module(entry)), "invalid params schema")
        self.assertEqual(calls, [])
        entry["params"] = {
            "type": "object", "properties": {"value": {"type": "integer", "minimum": 1}},
            "required": ["value"], "additionalProperties": False,
        }
        for args in ({}, {"value": "1"}, {"value": 0}, {"value": 1, "extra": 0}):
            with self.subTest(args=args):
                entry["acceptance"] = [{"args": args, "expect": 7}]
                self.assert_failed(self.check(module(entry)), "ValidationError")
        self.assertEqual(calls, [])
        entry["acceptance"] = [{"args": {"value": 1}, "expect": 7}]
        self.assertTrue(self.check(module(entry))["pass"])
        self.assertEqual(calls, [{"value": 1}])

    def test_unknown_schema_dialect_fails_closed(self):
        entry = tool()
        entry["params"]["$schema"] = "https://example.invalid/unknown-dialect"
        self.assert_failed(self.check(module(entry)), "unsupported JSON Schema dialect")

    def test_evidence_preserves_call_inputs_and_outputs(self):
        shared_result = {"value": 7}
        def read_value(values):
            values.append(99)
            shared_result["value"] += 1
            return shared_result
        entry = tool(fn=read_value)
        entry["params"] = {
            "type": "object", "properties": {"values": {"type": "array"}},
            "required": ["values"],
        }
        entry["acceptance"] = [
            {"args": {"values": [1]}, "expect": {"value": 8}},
            {"args": {"values": [2]}, "expect": {"value": 9}},
        ]
        result = self.check(module(entry))
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["acceptance"][0]["actual"], {"value": 8})
        self.assertEqual(result["acceptance"][0]["args"], {"values": [1]})
        self.assertEqual(entry["acceptance"][0]["args"], {"values": [1]})

    def test_cases_require_explicit_json_arguments_and_expectation(self):
        for case in (None, [], {}, {"args": {}}, {"expect": 7},
                     {"args": [], "expect": 7}, {"args": {}, "expect": float("nan")},
                     {"args": {1: 2}, "expect": 7}, {"args": {}, "expect": (7,)},
                     {"args": {}, "expect": 7, "source": ""}):
            with self.subTest(case=case):
                entry = tool()
                entry["acceptance"] = [case]
                result = self.check(module(entry))
                self.assertFalse(result["pass"])
                self.assertEqual(result["acceptance"][0]["status"], "failed")

    def test_result_must_be_finite_json_even_outside_partial_assertion(self):
        for value in (float("nan"), float("inf"), {"ok": 7, "bad": float("nan")},
                      {1: 7}, (7,), object()):
            with self.subTest(value=value):
                result = self.check(module(tool(fn=lambda: value, expected={"ok": 7})))
                self.assertFalse(result["pass"])

    def test_partial_objects_and_exact_lists(self):
        entry = tool(fn=lambda: {"value": [1, 2], "trace": "extra"}, expected={"value": [1, 2]})
        self.assertTrue(self.check(module(entry))["pass"])
        entry["acceptance"][0]["expect"] = {"value": [1]}
        self.assert_failed(self.check(module(entry)), "length")
        entry["acceptance"][0]["expect"] = {"missing": 1}
        self.assert_failed(self.check(module(entry)), "missing key")

    def test_numeric_boundaries_never_coerce_integers_or_booleans(self):
        for actual, expected in ((True, 1), (1, True), (1.0, 1), (2**60 + 1, 2**60),
                                 (100.001, 100.0), (0.0000000001, 0.0)):
            with self.subTest(actual=actual, expected=expected):
                self.assertFalse(self.check(module(tool(fn=lambda: actual, expected=expected)))["pass"])
        for value in (True, 2**60 + 1, 100.0, None):
            with self.subTest(exact=value):
                self.assertTrue(self.check(module(tool(fn=lambda: value, expected=value)))["pass"])

    def test_sourced_tolerance_has_explicit_success_and_failure_bounds(self):
        entry = tool(fn=lambda: 10.25, expected=10.0)
        entry["acceptance"][0]["tolerance"] = {"abs": 0.25, "source": "datasheet rounding table"}
        result = self.check(module(entry))
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["acceptance"][0]["tolerances"], [
            {"path": "$", "abs": 0.25, "source": "datasheet rounding table"}])
        entry["fn"] = lambda: 10.250001
        self.assertFalse(self.check(module(entry))["pass"])
        entry["fn"] = lambda: 10.5
        entry["acceptance"][0]["tolerance"] = {"rel": 0.05, "source": "datasheet bound"}
        self.assertTrue(self.check(module(entry))["pass"])
        entry["fn"] = lambda: 11
        entry["acceptance"][0]["expect"] = 10
        self.assertFalse(self.check(module(entry))["pass"])

    def test_invalid_tolerances_fail_instead_of_becoming_defaults(self):
        for tolerance in (None, {}, {"abs": 1}, {"source": "citation"},
                          {"abs": -1, "source": "citation"},
                          {"rel": float("inf"), "source": "citation"},
                          {"abs": True, "source": "citation"},
                          {"abs": "1", "source": "citation"},
                          {"abs": 1, "source": " "},
                          {"abs": 1, "source": "citation", "implicit": True}):
            with self.subTest(tolerance=tolerance):
                entry = tool(fn=lambda: 7.0, expected=7.0)
                entry["acceptance"][0]["tolerance"] = tolerance
                self.assert_failed(self.check(module(entry)), "tolerance")

    def test_integer_scope_masks_reserved_bits_and_accepts_valid_set(self):
        entry = tool(fn=lambda: 0x58, expected=0x18)
        entry["acceptance"][0]["mask"] = 0x3F
        result = self.check(module(entry))
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["acceptance"][0]["tolerances"],
                         [{"path": "$", "mask": 0x3F}])
        entry["fn"] = lambda: 0x68  # differing defined bit still fails
        self.assertFalse(self.check(module(entry))["pass"])

        entry = tool(fn=lambda: 0x59, expected=0x58)
        entry["acceptance"][0]["valid"] = [0x58, 0x59, 0x5A]
        result = self.check(module(entry))
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["acceptance"][0]["tolerances"],
                         [{"path": "$", "valid": [0x58, 0x59, 0x5A]}])
        entry["fn"] = lambda: 0x5B
        self.assertFalse(self.check(module(entry))["pass"])

    def test_invalid_integer_scope_fails_instead_of_becoming_defaults(self):
        for scope, diagnostic in (({"mask": -1}, "mask"), ({"mask": True}, "mask"),
                                  ({"mask": 1, "valid": [1]}, "mask"),
                                  ({"valid": []}, "valid"), ({"valid": [1, "2"]}, "valid"),
                                  ({"valid": "1"}, "valid")):
            with self.subTest(scope=scope):
                entry = tool(fn=lambda: 7, expected=7)
                entry["acceptance"][0].update(scope)
                self.assert_failed(self.check(module(entry)), diagnostic)

    def cross_module(self):
        mod = module(tool("driver_read", "driver"), tool("behavior_read", "behavior"))
        mod.DRIVER_REGISTERS = {"id": {"address": 208, "reset": 7}}
        mod.BEHAVIOR_REGISTERS = {"id": {"address": 208, "reset": 7}}
        mod.CROSS_MODEL_CHECKS = lambda: [
            {"name": "id register", "source": "datasheet register table",
             "expected": mod.BEHAVIOR_REGISTERS["id"], "actual": mod.DRIVER_REGISTERS["id"]}]
        return mod

    def test_cross_model_checks_are_required_and_evaluate_live_records(self):
        mod = self.cross_module()
        result = self.check(mod, models=("driver", "behavior"))
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["cross_model"]["checks"][0]["status"], "passed")
        mod.DRIVER_REGISTERS["id"]["reset"] = 8
        self.assert_failed(self.check(mod, models=("driver", "behavior")), "CROSS_MODEL_CHECKS")
        mod = self.cross_module()
        del mod.CROSS_MODEL_CHECKS
        self.assert_failed(self.check(mod, models=("driver", "behavior")), "required and must be callable")

    def test_cross_checks_reject_malformed_empty_and_partial_records(self):
        for checks in ([], None, ["PASS"], [True], [{}],
                       [{"name": "", "source": "table", "expected": 1, "actual": 1}],
                       [{"name": "reset", "source": "", "expected": 1, "actual": 1}],
                       [{"name": "reset", "source": "table", "expected": {}, "actual": {"x": 1}}],
                       [{"name": "reset", "source": "table", "expected": float("nan"), "actual": 1}]):
            with self.subTest(checks=checks):
                mod = self.cross_module()
                mod.CROSS_MODEL_CHECKS = lambda: checks
                self.assert_failed(self.check(mod, models=("driver", "behavior")), "CROSS_MODEL_CHECKS")

    def test_cross_checks_support_sourced_float_tolerance(self):
        mod = self.cross_module()
        mod.CROSS_MODEL_CHECKS = lambda: [{
            "name": "coefficient", "source": "coefficient table", "expected": 1.0, "actual": 1.125,
            "tolerance": {"abs": 0.125, "source": "documented representation rounding"}}]
        result = self.check(mod, models=("driver", "behavior"))
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(len(result["cross_model"]["checks"][0]["tolerances"]), 1)

    def refine_module(self, fn=None):
        mod = module(tool("refine_model", fn=fn))
        mod.IMMUTABLE_DATASHEET = {"id": {"reset": 7}, "coefficient": {"typ": 1.25}}
        return mod

    def test_refine_requires_canonical_facts_and_executed_acceptance(self):
        mod = self.refine_module()
        result = self.check(mod)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["refinement"]["status"], "passed")
        del mod.IMMUTABLE_DATASHEET
        self.assert_failed(self.check(mod), "IMMUTABLE_DATASHEET")
        mod.IMMUTABLE_DATASHEET = {}
        self.assert_failed(self.check(mod), "IMMUTABLE_DATASHEET")
        mod.MCP_TOOLS["refine_model"]["acceptance"] = []
        self.assert_failed(self.check(mod), "executed refine acceptance")

    def test_refine_detects_nested_mutation_rebinding_and_raise(self):
        for operation in ("mutate", "rebind", "mutate-raise", "rebind-raise"):
            with self.subTest(operation=operation):
                mod = self.refine_module()
                def refine():
                    if operation.startswith("mutate"):
                        mod.IMMUTABLE_DATASHEET["id"]["reset"] = 8
                    else:
                        mod.IMMUTABLE_DATASHEET = copy.deepcopy(mod.IMMUTABLE_DATASHEET)
                    if operation.endswith("raise"):
                        raise RuntimeError("refinement failed")
                    return 7
                mod.MCP_TOOLS["refine_model"]["fn"] = refine
                result = self.check(mod)
                self.assert_failed(result, "IMMUTABLE_DATASHEET")
                self.assertEqual(result["refinement"]["checks"][0]["status"], "failed")
                if operation.endswith("raise"):
                    self.assertIn("RuntimeError", "\n".join(result["errors"]))

    def test_every_refine_case_gets_independent_before_after_snapshots(self):
        mod = self.refine_module()
        calls = []
        def refine():
            calls.append(True)
            if len(calls) == 2:
                mod.IMMUTABLE_DATASHEET["coefficient"]["typ"] = 2.0
            return 7
        mod.MCP_TOOLS["refine_model"]["fn"] = refine
        mod.MCP_TOOLS["refine_model"]["acceptance"] *= 2
        result = self.check(mod)
        self.assertEqual([record["status"] for record in result["refinement"]["checks"]],
                         ["passed", "failed"])
        self.assertFalse(result["pass"])

    def test_async_acceptance_is_executed(self):
        async def read_value():
            return 7
        self.assertTrue(self.check(module(tool(fn=read_value)))["pass"])

    def test_installed_sdk_errors_never_become_absent(self):
        mod = module(tool())
        with patch.object(verifier.importlib.util, "find_spec", return_value=object()):
            self.assert_failed(verifier.verify(mod, ("knowledge",), ("mcp-interface",)), "build_server")
            def broken_build():
                raise RuntimeError("build failed")
            mod.build_server = broken_build
            result = verifier.verify(mod, ("knowledge",), ("mcp-interface",))
            self.assert_failed(result, "build failed")
            self.assertEqual(result["mcp"]["status"], "failed")
            mod.build_server = lambda: object()
            self.assert_failed(verifier.verify(mod, ("knowledge",), ("mcp-interface",)), "list_tools")
            async def broken_list():
                raise RuntimeError("listing failed")
            mod.build_server = lambda: SimpleNamespace(list_tools=broken_list)
            self.assert_failed(verifier.verify(mod, ("knowledge",), ("mcp-interface",)), "listing failed")
        with patch.object(verifier.importlib.util, "find_spec", side_effect=ImportError("broken SDK")):
            self.assert_failed(verifier.verify(mod, ("knowledge",), ("mcp-interface",)), "broken SDK")

    def test_cli_writes_success_failure_and_import_evidence(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "server.py"
            path.write_text(
                "def read_value(): return 7\n"
                "MCP_TOOLS = {'read_value': {'name': 'read_value', 'model': 'knowledge',\n"
                " 'description': 'Reset value', 'source': 'datasheet reset table',\n"
                " 'params': {'type': 'object'}, 'fn': read_value,\n"
                " 'acceptance': [{'args': {}, 'expect': 7}]}}\n", encoding="utf-8")
            argv = [str(path), "--project-root", root, "--models", "knowledge", "--scenarios", ""]
            evidence = Path(root) / "tests" / "summary" / "verify_mcp_server.json"
            with patch.object(verifier.importlib.util, "find_spec", return_value=None):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(verifier.main(argv), 0)
                    result = json.loads(evidence.read_text(encoding="utf-8"))
                    self.assertTrue(result["pass"])
                    self.assertEqual(result["acceptance"][0]["status"], "passed")
                    path.write_text("MCP_TOOLS = {'bad': None}\n", encoding="utf-8")
                    self.assertEqual(verifier.main(argv), 1)
                    self.assertFalse(json.loads(evidence.read_text(encoding="utf-8"))["pass"])
                    path.write_text("raise RuntimeError('cannot import')\n", encoding="utf-8")
                    self.assertEqual(verifier.main(argv), 1)
                    self.assertIn("cannot import", evidence.read_text(encoding="utf-8"))

    def compare_schemas(self, registry, exposed):
        entry = tool()
        entry["params"] = registry
        mod = module(entry)
        mod.build_server = lambda: SimpleNamespace(list_tools=lambda: [
            SimpleNamespace(name="read_value", inputSchema=exposed)])
        with patch.object(verifier.importlib.util, "find_spec", return_value=object()):
            return verifier.verify(mod, ("knowledge",), ("mcp-interface",))

    def test_schema_annotations_are_ignored_only_at_schema_nodes(self):
        registry = {
            "type": "object", "title": "Old tool", "description": "Old description",
            "$comment": "Old comment", "examples": [{}],
            "properties": {
                "title": {"type": "string", "title": "Old field", "description": "Old text"},
                "description": {"type": "integer", "default": 7},
                "payload": {"const": {"title": "payload", "description": "literal",
                                      "$comment": "data", "examples": [1]},
                            "default": {"title": "default payload"}},
                "choice": {"anyOf": [{"type": "string", "title": "Old branch"},
                                     {"type": "null", "examples": [None]}]},
            },
            "$defs": {"title": {"type": "string", "title": "Old definition"}},
        }
        exposed = copy.deepcopy(registry)
        for key in ("title", "description", "$comment", "examples"):
            exposed.pop(key)
        exposed["properties"]["title"]["title"] = "New field"
        exposed["properties"]["title"]["description"] = "New text"
        exposed["properties"]["choice"]["anyOf"][0]["title"] = "New branch"
        exposed["properties"]["choice"]["anyOf"][1].pop("examples")
        exposed["$defs"]["title"]["title"] = "New definition"
        result = self.compare_schemas(registry, exposed)
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["mcp"]["status"], "passed")

    def test_schema_property_names_constraints_and_literal_payloads_are_preserved(self):
        base = {
            "type": "object",
            "properties": {
                "title": {"type": "integer", "minimum": 0, "default": 7},
                "description": {"type": "string"},
                "payload": {
                    "const": {"title": "literal", "description": "literal",
                              "$comment": "literal", "examples": [1]},
                    "default": {"title": "literal", "description": "literal"},
                },
                "boolean": {"const": True},
            },
        }
        variants = []
        missing_title = copy.deepcopy(base)
        del missing_title["properties"]["title"]
        variants.append(missing_title)
        missing_description = copy.deepcopy(base)
        del missing_description["properties"]["description"]
        variants.append(missing_description)
        constraint = copy.deepcopy(base)
        constraint["properties"]["title"]["minimum"] = 1
        variants.append(constraint)
        field_default = copy.deepcopy(base)
        field_default["properties"]["title"]["default"] = 8
        variants.append(field_default)
        for keyword, fields in (
            ("const", ("title", "description", "$comment", "examples")),
            ("default", ("title", "description")),
        ):
            for field in fields:
                literal = copy.deepcopy(base)
                del literal["properties"]["payload"][keyword][field]
                variants.append(literal)
        boolean = copy.deepcopy(base)
        boolean["properties"]["boolean"]["const"] = 1
        variants.append(boolean)
        for exposed in variants:
            with self.subTest(exposed=exposed):
                self.assert_failed(self.compare_schemas(base, exposed), "inputSchema differs")


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "mcp SDK is not installed")
@unittest.skipIf(verifier.validators is None, "jsonschema is required")
class FastMCPTests(unittest.TestCase):
    def server_module(self):
        from mcp.server.fastmcp import FastMCP
        server = FastMCP("verifier-regression")
        @server.tool()
        def echo(value: int) -> dict:
            """Return a documented integer without conversion."""
            return {"value": value}
        exposed = verifier._resolve(server.list_tools())
        entry = tool("echo", fn=echo, expected={"value": 7})
        entry["params"] = copy.deepcopy(exposed[0].inputSchema)
        entry["acceptance"] = [{"args": {"value": 7}, "expect": {"value": 7}}]
        mod = module(entry)
        mod.build_server = lambda: server
        return mod, server

    def test_actual_async_fastmcp_inventory_and_schema_pass(self):
        mod, _ = self.server_module()
        result = verifier.verify(mod, ("knowledge",), ("mcp-interface",))
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["mcp"]["status"], "passed")
        self.assertEqual(result["mcp"]["tools"], ["echo"])

    def test_actual_fastmcp_accepts_harmless_schema_annotations(self):
        mod, _ = self.server_module()
        params = mod.MCP_TOOLS["echo"]["params"]
        params["title"] = "Independent registry label"
        params["description"] = "Registry wording differs from SDK wording"
        params["$comment"] = "Editorial note"
        params["examples"] = [{"value": 7}]
        params["properties"]["value"]["title"] = "Independent field label"
        params["properties"]["value"]["description"] = "Editorial field description"
        result = verifier.verify(mod, ("knowledge",), ("mcp-interface",))
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["mcp"]["status"], "passed")

    def test_actual_fastmcp_extra_inventory_fails(self):
        mod, server = self.server_module()
        @server.tool()
        def extra() -> int:
            return 1
        result = verifier.verify(mod, ("knowledge",), ("mcp-interface",))
        self.assertFalse(result["pass"])
        self.assertIn("inventory differs", "\n".join(result["errors"]))

    def test_actual_fastmcp_missing_inventory_fails(self):
        mod, _ = self.server_module()
        mod.MCP_TOOLS["missing"] = tool("missing")
        result = verifier.verify(mod, ("knowledge",), ("mcp-interface",))
        self.assertFalse(result["pass"])
        self.assertIn("missing=['missing']", "\n".join(result["errors"]))

    def test_actual_fastmcp_schema_mismatch_fails(self):
        mod, _ = self.server_module()
        mod.MCP_TOOLS["echo"]["params"]["properties"]["value"]["minimum"] = 0
        result = verifier.verify(mod, ("knowledge",), ("mcp-interface",))
        self.assertFalse(result["pass"])
        self.assertEqual(result["acceptance"][0]["status"], "passed")
        self.assertIn("inputSchema differs", "\n".join(result["errors"]))


if __name__ == "__main__":
    unittest.main()
