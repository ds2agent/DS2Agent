#!/usr/bin/env python3
"""Regression test for datasheet_bundle.py. Exercises prepare -> extract -> build -> verify
with a stubbed MinerU call. Stdlib only (unittest).

Run: python scripts/test_datasheet_bundle.py
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("datasheet_bundle", HERE / "datasheet_bundle.py")
bundle = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(bundle)


def _fake_mineru(cmd, **kw):
    output = Path(cmd[cmd.index("-o") + 1])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("# BMP280\n\n## 4.3.1 Register 0xD0 id\n\nchip_id = 0x58\n", encoding="utf-8")
    return subprocess.CompletedProcess(cmd, 0, "", "")


class TestBundle(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.pdf = self.work / "main.pdf"
        self.pdf.write_text("%PDF-1.4 fake datasheet bytes")
        self.orig_run = bundle.subprocess.run
        self.orig_find_mineru = bundle.find_mineru

    def tearDown(self):
        bundle.subprocess.run = self.orig_run
        bundle.find_mineru = self.orig_find_mineru

    def _prepare(self):
        return bundle.cmd_prepare(argparse.Namespace(
            work=str(self.work), sources=[str(self.pdf)], name="bmp280",
            title="BMP280", main=str(self.pdf)))

    def test_full_flow(self):
        self.assertEqual(self._prepare(), 0)
        bundle.subprocess.run = _fake_mineru
        self.assertEqual(bundle.cmd_extract(argparse.Namespace(
            work=str(self.work), mineru_bin="mineru")), 0)
        plan = self.work / "documents" / "main" / "plan.json"
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_text(json.dumps({"reviewed": True, "review_notes": "checked"}))
        out = self.work / "out"
        self.assertEqual(bundle.cmd_build(argparse.Namespace(
            work=str(self.work), output=str(out), require_reviewed=True)), 0)
        self.assertTrue((out / "bmp280-datasheet" / "references" / "datasheet.md").exists())
        self.assertEqual(bundle.cmd_verify(argparse.Namespace(
            work=str(self.work), strict=True)), 0)

    def test_missing_export_does_not_accept_unrelated_markdown(self):
        self._prepare()
        output_dir = self.work / "extracted" / "main"
        output_dir.mkdir(parents=True)
        (output_dir / "old.md").write_text("Unrelated previous extraction", encoding="utf-8")
        bundle.subprocess.run = lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", "")
        self.assertEqual(bundle.cmd_extract(argparse.Namespace(
            work=str(self.work), mineru_bin="mineru")), 1)
        report = json.loads((self.work / "extract-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["sources"]["main"]["status"], "no_markdown")
        self.assertIsNone(report["sources"]["main"]["markdown"])

    def test_missing_mineru_fails(self):
        self._prepare()
        bundle.find_mineru = lambda o: None
        self.assertEqual(bundle.cmd_extract(argparse.Namespace(
            work=str(self.work), mineru_bin=None)), 1)


if __name__ == "__main__":
    unittest.main()
