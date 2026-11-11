"""End-to-end checks for the portable knowledge-base guardrails (stdlib only)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("kb_check.py")


class KnowledgeBaseChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "kb"
        (self.root / "raw").mkdir(parents=True)
        (self.root / "wiki" / "Concepts").mkdir(parents=True)
        (self.root / "raw" / "a.md").write_text("# Design A\nOne validated input.\n", encoding="utf-8")
        (self.root / "raw" / "b.md").write_text("# Design B\nA second input.\n", encoding="utf-8")

    def cli(self, *args, ok=True, root=None):
        env = dict(os.environ, PYTHONUTF8="1")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), args[0], "--root", str(root or self.root), *args[1:]],
            capture_output=True, text=True, encoding="utf-8", env=env, check=False,
        )
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            self.fail("CLI must return JSON: " + result.stdout + result.stderr)
        self.assertIsInstance(payload, dict)
        return payload

    def source(self, filename="a.md", ref="S1"):
        return {
            "ref": ref,
            "path": "raw/" + filename,
            "sha256": hashlib.sha256((self.root / "raw" / filename).read_bytes()).hexdigest(),
            "locator": "Section 1",
            "version": "fixture-v1",
            "origin": "local fixture, not company data",
            "retrieved_at": "2026-11-10",
            "role": "repository-example",
        }

    def metadata(self, note_id="I001", *, kind="ingest", sources=None, parents=None, status="draft"):
        return {
            "id": note_id, "kind": kind, "scope": "test fixture only", "status": status,
            "sources": sources if sources is not None else [self.source()],
            "derived_from": parents if parents is not None else [],
        }

    def note(self, meta=None, *, filename=None, body="The input is required. [S1]\n"):
        meta = meta or self.metadata()
        filename = filename or meta["id"] + ".md"
        path = self.root / "wiki" / "Concepts" / filename
        path.write_text("# Fixture note\n\n```json\n" + json.dumps(meta, ensure_ascii=False, indent=2) + "\n```\n\n" + body, encoding="utf-8")
        return path

    def snapshot(self, name="before"):
        relative = "wiki/.checks/" + name + ".json"
        self.cli("snapshot", "--output", relative)
        return relative

    def validate(self, *, baseline=None, mode=None, ok=True):
        args = ["validate"]
        if baseline:
            args += ["--baseline", baseline]
        if mode:
            args += ["--mode", mode]
        return self.cli(*args, ok=ok)

    def test_empty_library_and_valid_ingest(self):
        self.validate()
        baseline = self.snapshot()
        self.note()
        self.validate(baseline=baseline, mode="ingest")

    def test_valid_refine_keeps_ingest_and_sources(self):
        original = self.note().read_bytes()
        baseline = self.snapshot()
        self.note(self.metadata("C001", kind="concept", parents=["I001"]), body="Merged conclusion. [S1]\n\nSee [input](I001.md).\n")
        self.validate(baseline=baseline, mode="refine")
        self.assertEqual((self.root / "wiki" / "Concepts" / "I001.md").read_bytes(), original)

    def test_raw_mutation_addition_and_deletion_are_rejected(self):
        baseline = self.snapshot()
        original = (self.root / "raw" / "a.md").read_bytes()
        (self.root / "raw" / "a.md").write_bytes(b"changed")
        self.validate(baseline=baseline, mode="ingest", ok=False)
        (self.root / "raw" / "a.md").write_bytes(original)
        (self.root / "raw" / "new.md").write_bytes(b"new")
        self.validate(baseline=baseline, mode="ingest", ok=False)
        (self.root / "raw" / "new.md").unlink()
        (self.root / "raw" / "a.md").unlink()
        self.validate(baseline=baseline, mode="ingest", ok=False)

    def test_missing_source_and_wrong_hash_are_rejected(self):
        meta = self.metadata()
        meta["sources"][0]["sha256"] = "0" * 64
        self.note(meta)
        self.validate(ok=False)
        meta["sources"][0]["path"] = "raw/missing.md"
        self.note(meta)
        self.validate(ok=False)

    def test_source_path_must_not_escape_raw(self):
        outside = self.root / "outside.md"
        outside.write_bytes(b"outside")
        meta = self.metadata()
        for invalid in ("raw/../outside.md", "outside.md", str(outside.resolve())):
            with self.subTest(path=invalid):
                meta["sources"][0]["path"] = invalid
                meta["sources"][0]["sha256"] = hashlib.sha256(outside.read_bytes()).hexdigest()
                self.note(meta)
                self.validate(ok=False)

    def test_source_symlink_escape_is_rejected_when_supported(self):
        outside = self.root / "outside.md"
        outside.write_bytes(b"outside")
        link = self.root / "raw" / "link.md"
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest("Symlink creation unavailable in this Windows session")
        self.note(self.metadata(sources=[self.source("link.md")]))
        self.validate(ok=False)

    def test_duplicate_note_id_is_rejected(self):
        self.note()
        self.note(filename="duplicate.md")
        self.validate(ok=False)

    def test_duplicate_source_ref_is_rejected(self):
        self.note(self.metadata(sources=[self.source(), self.source("b.md")]))
        self.validate(ok=False)

    def test_source_ref_must_be_cited_in_body(self):
        self.note(body="This claim has no source citation.\n")
        self.validate(ok=False)

    def test_missing_derived_parent_is_rejected(self):
        self.note(self.metadata("C001", kind="concept", parents=["I999"]))
        self.validate(ok=False)

    def test_concept_cannot_cross_scope(self):
        self.note()
        meta = self.metadata("C001", kind="concept", parents=["I001"])
        meta["scope"] = "another project"
        self.note(meta)
        self.validate(ok=False)

    def test_derived_cycle_is_rejected(self):
        self.note(self.metadata("C001", kind="concept", parents=["C002"]))
        self.note(self.metadata("C002", kind="concept", parents=["C001"]))
        self.validate(ok=False)

    def test_broken_local_markdown_link_is_rejected(self):
        self.note(body="A conclusion. [S1]\n\n[Missing note](missing.md)\n")
        self.validate(ok=False)

    def test_external_and_anchor_links_do_not_fail(self):
        self.note(body="A conclusion. [S1]\n\n[Section](#fixture-note) [Official](https://example.com/missing.md)\n")
        self.validate()

    def test_ingest_cannot_modify_an_existing_note(self):
        path = self.note()
        baseline = self.snapshot()
        path.write_text(path.read_text(encoding="utf-8") + "Extra claim. [S1]\n", encoding="utf-8")
        self.validate(baseline=baseline, mode="ingest", ok=False)

    def test_ingest_cannot_add_a_concept(self):
        self.note()
        baseline = self.snapshot()
        self.note(self.metadata("C001", kind="concept", parents=["I001"]))
        self.validate(baseline=baseline, mode="ingest", ok=False)

    def test_refine_cannot_add_new_source_from_existing_raw(self):
        self.note()
        baseline = self.snapshot()
        self.note(self.metadata("C001", kind="concept", parents=["I001"], sources=[self.source("b.md")]))
        self.validate(baseline=baseline, mode="refine", ok=False)

    def test_refine_cannot_change_ingest(self):
        path = self.note()
        baseline = self.snapshot()
        path.write_text(path.read_text(encoding="utf-8") + "Changed. [S1]\n", encoding="utf-8")
        self.validate(baseline=baseline, mode="refine", ok=False)

    def test_refine_cannot_add_ingest(self):
        self.note()
        baseline = self.snapshot()
        self.note(self.metadata("I002", sources=[self.source("b.md")]))
        self.validate(baseline=baseline, mode="refine", ok=False)

    def test_refine_cannot_delete_note(self):
        path = self.note()
        baseline = self.snapshot()
        path.unlink()
        self.validate(baseline=baseline, mode="refine", ok=False)

    def test_verified_requires_review_fields(self):
        meta = self.metadata(status="verified")
        self.note(meta)
        self.validate(ok=False)
        meta["review"] = {"reviewer": "fixture reviewer", "date": "2026-11-10", "method": "Compared each claim with source"}
        self.note(meta)
        self.validate()
        meta["review"]["date"] = "not-a-date"
        self.note(meta)
        self.validate(ok=False)

    def test_refine_cannot_self_promote_to_verified(self):
        self.note()
        baseline = self.snapshot()
        meta = self.metadata("C001", kind="concept", parents=["I001"], status="verified")
        meta["review"] = {"reviewer": "fixture", "date": "2026-11-10", "method": "claimed review"}
        self.note(meta)
        self.validate(baseline=baseline, mode="refine", ok=False)

    def test_ingest_cannot_self_promote_to_verified(self):
        baseline = self.snapshot()
        meta = self.metadata(status="verified")
        meta["review"] = {"reviewer": "fixture", "date": "2026-11-10", "method": "claimed review"}
        self.note(meta)
        self.validate(baseline=baseline, mode="ingest", ok=False)

    def test_snapshot_is_not_overwritten(self):
        relative = self.snapshot()
        original = (self.root / relative).read_bytes()
        self.cli("snapshot", "--output", relative, ok=False)
        self.assertEqual((self.root / relative).read_bytes(), original)

    def test_snapshot_is_bound_to_original_root(self):
        relative = self.snapshot()
        other = self.base / "other"
        shutil.copytree(self.root, other)
        self.cli("validate", "--baseline", relative, "--mode", "ingest", root=other, ok=False)

    def test_snapshot_and_report_cannot_write_raw_or_escape_root(self):
        raw_before = (self.root / "raw" / "a.md").read_bytes()
        for target in ("raw/a.md", "wiki/Concepts/new.json", "../outside.json"):
            with self.subTest(target=target):
                self.cli("snapshot", "--output", target, ok=False)
                self.cli("validate", "--report", target, ok=False)
        self.assertEqual((self.root / "raw" / "a.md").read_bytes(), raw_before)
        self.assertFalse((self.base / "outside.json").exists())

    def test_invalid_metadata_fails_snapshot_as_json(self):
        (self.root / "wiki" / "Concepts" / "broken.md").write_text("# Broken\n```json\n{bad json}\n```\n", encoding="utf-8")
        self.cli("snapshot", "--output", "wiki/.checks/bad.json", ok=False)
        self.assertFalse((self.root / "wiki" / ".checks" / "bad.json").exists())

    def test_report_is_json_and_does_not_change_inputs(self):
        self.note()
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.cli("validate", "--report", "wiki/.checks/report.json")
        json.loads((self.root / "wiki" / ".checks" / "report.json").read_text(encoding="utf-8"))
        for relative, content in before.items():
            self.assertEqual((self.root / relative).read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
