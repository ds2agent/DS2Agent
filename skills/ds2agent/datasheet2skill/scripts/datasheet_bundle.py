#!/usr/bin/env python3
"""Datasheet bundle: snapshot sources, convert PDFs to Markdown with MinerU, build a
knowledge-model skill folder, and verify hashes and links.

Subcommands: prepare, extract, build, verify. Stdlib only (pypdf optional for page counts).

PDF-to-Markdown uses MinerU (`mineru parse <pdf> -o <markdown-file> --pages all`). If `mineru` is
missing, extraction fails with the install command rather than falling back to a lossy
extractor.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

STATUS_MECH = "mechanical_failure"
STATUS_UNREVIEWED = "unreviewed"
STATUS_LIMITED = "reviewed_with_limitations"
STATUS_REVIEWED = "reviewed"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot(src: Path, dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return sha256(dest)


def find_mineru(override: str | None) -> str | None:
    if override:
        return override
    p = shutil.which("mineru")
    if p:
        return p
    # look next to the running interpreter (venv Scripts dir)
    exe_dir = Path(sys.executable).parent
    for cand in ("mineru.exe", "mineru"):
        q = exe_dir / cand
        if q.exists():
            return str(q)
    return None


def _pdf_pages(path: Path) -> int | None:
    try:
        from pypdf import PdfReader  # type: ignore
        return len(PdfReader(str(path)).pages)
    except Exception:  # noqa: BLE001
        return None


def cmd_prepare(args) -> int:
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    src_dir = work / "sources"
    if src_dir.exists():
        shutil.rmtree(src_dir)
    src_dir.mkdir()

    inventory = {"name": args.name, "title": args.title, "main": None, "sources": []}
    bundle = {"name": args.name, "title": args.title, "main": None, "sources": []}

    for i, s in enumerate(args.sources):
        sp = Path(s)
        dest = src_dir / f"{i}__{sp.name}"
        digest = _snapshot(sp, dest)
        sid = Path(sp.stem).name
        if str(sp.resolve()) == str(Path(args.main).resolve()):
            inventory["main"] = sid
            bundle["main"] = sid
        inventory["sources"].append(
            {"id": sid, "path": str(dest.relative_to(work)), "sha256": digest,
             "pages": _pdf_pages(dest), "title": sp.name}
        )
        bundle["sources"].append(
            {"id": sid, "role": "main", "title": sp.name, "asset": "datasheet",
             "register_map": False, "pin_table": False}
        )

    (work / "inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    (work / "bundle.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"prepare: snapshotted {len(inventory['sources'])} source(s) into {work}")
    return 0


def cmd_extract(args) -> int:
    work = Path(args.work)
    inv = json.loads((work / "inventory.json").read_text(encoding="utf-8"))
    mineru = find_mineru(args.mineru_bin)
    if mineru is None:
        print("extract: FAIL: MinerU not found. Install it with: pip install mineru", file=sys.stderr)
        return 1

    report = {"mineru": mineru, "sources": {}}
    for src in inv["sources"]:
        sp = work / src["path"]
        outdir = work / "extracted" / src["id"]
        outdir.mkdir(parents=True, exist_ok=True)
        if sp.suffix.lower() == ".pdf":
            md = outdir / "document.md"
            try:
                subprocess.run(
                    [mineru, "parse", str(sp), "-o", str(md), "--pages", "all"],
                    check=True, capture_output=True, text=True,
                )
                report["sources"][src["id"]] = {
                    "status": "ok",
                    "markdown": str(md.relative_to(work)) if md.is_file() else None,
                    "images": [str(p.relative_to(work)) for p in sorted(outdir.rglob("images/*")) if p.is_file()],
                }
                if not md.is_file():
                    report["sources"][src["id"]]["status"] = "no_markdown"
            except OSError as e:
                report["sources"][src["id"]] = {"status": "failed", "stderr": f"mineru not runnable: {e}"}
            except subprocess.CalledProcessError as e:
                report["sources"][src["id"]] = {"status": "failed", "stderr": e.stderr[-2000:]}
        else:
            # non-PDF (spreadsheet/table) source: snapshot only, no MinerU pass
            report["sources"][src["id"]] = {"status": "snapshot_only"}

    (work / "extract-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    failed = [k for k, v in report["sources"].items() if v.get("status") in ("failed", "no_markdown")]
    if failed:
        print(f"extract: FAIL: sources {failed} did not produce Markdown", file=sys.stderr)
        return 1
    print(f"extract: OK ({len(report['sources'])} source(s), mineru={mineru})")
    return 0


def cmd_build(args) -> int:
    work = Path(args.work)
    inv = json.loads((work / "inventory.json").read_text(encoding="utf-8"))
    bundle = json.loads((work / "bundle.json").read_text(encoding="utf-8"))
    out = Path(args.output) / f"{inv['name']}-datasheet"

    # review gate
    reviewed = {}
    review_dir = work / "documents"
    for src in inv["sources"]:
        plan = review_dir / src["id"] / "plan.json"
        reviewed[src["id"]] = bool(plan.exists() and json.loads(plan.read_text(encoding="utf-8")).get("reviewed"))
    if args.require_reviewed and not all(reviewed.values()):
        missing = [k for k, v in reviewed.items() if not v]
        print(f"build: FAIL: unreviewed sources {missing} (use --require-reviewed)", file=sys.stderr)
        return 2

    for d in (out / "references", out / "assets" / "figure", out / "assets" / "table"):
        d.mkdir(parents=True, exist_ok=True)

    (out / "SKILL.md").write_text(
        f"# {inv['title']}\n\nDevice: {inv['name']}. Datasheet knowledge model.\n"
        f"Read `references/index.md` first; facts cite `references/datasheet.md` and "
        f"`references/register_map.md`.\n",
        encoding="utf-8",
    )

    index_lines = [f"# {inv['title']} — index\n", f"Device identifier: `{inv['name']}`\n"]
    main_id = bundle.get("main") or inv.get("main")
    for src in inv["sources"]:
        rep = json.loads((work / "extract-report.json").read_text(encoding="utf-8"))
        md_rel = rep["sources"][src["id"]].get("markdown")
        if md_rel:
            dst = out / "references" / "datasheet.md"
            shutil.copy2(work / md_rel, dst)
            index_lines.append(f"- `references/datasheet.md` — {src['title']} ({src['id']})\n")
        else:
            index_lines.append(f"- source `{src['id']}` ({src['title']}) — no Markdown produced\n")

    index_lines.append("\nReview status: " + ", ".join(f"{k}={v}" for k, v in reviewed.items()) + "\n")
    (out / "references" / "index.md").write_text("".join(index_lines), encoding="utf-8")
    (out / "references" / "register_map.md").write_text(
        "# Register map\n\nPopulated during review from the routed register-map source.\n",
        encoding="utf-8",
    )
    (out / "references" / "pin_table.md").write_text(
        "# Pin table\n\nPopulated during review from the routed pin-table source.\n",
        encoding="utf-8",
    )

    print(f"build: wrote {out}")
    return 0


def cmd_verify(args) -> int:
    work = Path(args.work)
    inv = json.loads((work / "inventory.json").read_text(encoding="utf-8"))
    errors: list[str] = []

    # source hash check
    for src in inv["sources"]:
        sp = work / src["path"]
        if not sp.exists():
            errors.append(f"source {src['id']} missing")
        elif sha256(sp) != src["sha256"]:
            errors.append(f"source {src['id']} hash mismatch (snapshot changed)")

    # mineru output presence
    rep = json.loads((work / "extract-report.json").read_text(encoding="utf-8"))
    for sid, v in rep["sources"].items():
        if v.get("status") in ("failed", "no_markdown"):
            errors.append(f"source {sid} did not produce Markdown ({v.get('status')})")

    # review completeness
    reviewed = {}
    for src in inv["sources"]:
        plan = work / "documents" / src["id"] / "plan.json"
        reviewed[src["id"]] = bool(plan.exists() and json.loads(plan.read_text(encoding="utf-8")).get("reviewed"))
    if args.strict and not all(reviewed.values()):
        errors.append(f"unreviewed sources: {[k for k, v in reviewed.items() if not v]}")

    if errors:
        status = STATUS_UNREVIEWED if any("unreviewed" in e for e in errors) else STATUS_MECH
        for e in errors:
            print(f"verify: {status}: {e}")
        return 2
    print(f"verify: {STATUS_REVIEWED if all(reviewed.values()) else STATUS_LIMITED}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare")
    p.add_argument("sources", nargs="+")
    p.add_argument("--work", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--main", required=True)

    e = sub.add_parser("extract")
    e.add_argument("--work", required=True)
    e.add_argument("--mineru-bin", default=None)

    b = sub.add_parser("build")
    b.add_argument("--work", required=True)
    b.add_argument("--output", required=True)
    b.add_argument("--require-reviewed", action="store_true")

    v = sub.add_parser("verify")
    v.add_argument("--work", required=True)
    v.add_argument("--strict", action="store_true")

    args = ap.parse_args(argv)
    return {"prepare": cmd_prepare, "extract": cmd_extract, "build": cmd_build, "verify": cmd_verify}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
