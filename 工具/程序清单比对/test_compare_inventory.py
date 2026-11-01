"""Run with: python -m unittest discover -s <this directory> -v."""

import contextlib
import csv
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import compare_inventory as tool


class CompareInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.a = self.root / "release.csv"
        self.b = self.root / "summary.csv"
        self.output = self.root / "result"

    def write(self, path, rows, encoding="utf-8-sig", headers=("program_id", "source_ref")):
        with path.open("w", encoding=encoding, newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(headers)
            writer.writerows(rows)

    def cli(self, extra=()):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return tool.main([
                "--release", str(self.a), "--summary", str(self.b),
                "--output", str(self.output), *extra,
            ])

    def rows(self, name):
        with (self.output / name).open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))

    def report(self):
        return json.loads((self.output / "report.json").read_text(encoding="utf-8"))

    def test_trim_only_and_every_original_record_is_traceable(self):
        self.write(self.a, [["  PROG.cbl \t", " 本番.txt:12 "]])
        self.write(self.b, [["PROG.cbl", "調査.md:7"]])
        self.assertEqual(self.cli(), 0)
        rows = self.rows("matched.csv")
        self.assertEqual(len(rows), 2)
        self.assertEqual([row["inventory"] for row in rows], ["release", "summary"])
        self.assertEqual(rows[0]["original_program_id"], "  PROG.cbl \t")
        self.assertEqual(rows[0]["program_id"], "PROG.cbl")
        self.assertEqual(rows[0]["source_ref"], " 本番.txt:12 ")
        self.assertEqual(rows[0]["input_csv"], str(self.a.resolve()))
        self.assertEqual(rows[0]["csv_record"], "2")
        self.assertEqual(rows[0]["csv_line_start"], "2")
        self.assertEqual(rows[0]["csv_line_end"], "2")
        self.assertEqual(self.rows("release_only.csv"), [])
        report = self.report()
        self.assertEqual(report["inputs"]["release"]["sha256"], hashlib.sha256(self.a.read_bytes()).hexdigest())
        self.assertTrue(any("原文提取完整" in text for text in report["scope_limits"]))

    def test_same_filename_in_different_paths_does_not_match(self):
        self.write(self.a, [["src/PROGRAM.cbl", "A:1"]])
        self.write(self.b, [["lib/PROGRAM.cbl", "B:1"]])
        self.assertEqual(self.cli(), 1)
        self.assertEqual(self.rows("matched.csv"), [])
        self.assertEqual(self.rows("release_only.csv")[0]["program_id"], "src/PROGRAM.cbl")
        self.assertEqual(self.rows("summary_only.csv")[0]["program_id"], "lib/PROGRAM.cbl")

    def test_case_extensions_slashes_and_internal_spaces_are_preserved(self):
        self.write(self.a, [["Prog", "A:1"], ["P.cbl", "A:2"], ["dir/P", "A:3"], ["P Q", "A:4"]])
        self.write(self.b, [["prog", "B:1"], ["P.CBL", "B:2"], ["dir\\P", "B:3"], ["P  Q", "B:4"]])
        self.assertEqual(self.cli(), 1)
        counts = self.report()["unique_id_counts"]
        self.assertEqual(counts["matched"], 0)
        self.assertEqual(counts["release_only"], 4)
        self.assertEqual(counts["summary_only"], 4)

    def test_repeated_original_rows_are_retained_even_if_id_matches(self):
        self.write(self.a, [[" P ", "A:20"], [" P ", "A:20"]])
        self.write(self.b, [["P", "B:3"]])
        self.assertEqual(self.cli(), 1)
        duplicates = self.rows("duplicates.csv")
        self.assertEqual(len(duplicates), 2)
        self.assertEqual([r["csv_record"] for r in duplicates], ["2", "3"])
        self.assertEqual([r["original_program_id"] for r in duplicates], [" P ", " P "])
        self.assertEqual([r["occurrences"] for r in duplicates], ["2", "2"])
        self.assertEqual(len(self.rows("matched.csv")), 3)
        stats = self.report()["inputs"]["release"]
        self.assertEqual(stats["record_count"], 2)
        self.assertEqual(stats["unique_id_count"], 1)
        self.assertEqual(stats["duplicate_id_count"], 1)
        self.assertEqual(stats["duplicate_extra_record_count"], 1)
        self.assertEqual(stats["duplicate_record_count"], 2)

    def test_summary_duplicates_are_reported_in_summary_side(self):
        self.write(self.a, [["P", "A:2"]])
        self.write(self.b, [["P", "B:4"], ["P", "B:8"]])
        self.assertEqual(self.cli(), 1)
        self.assertEqual([r["source_ref"] for r in self.rows("duplicates.csv")], ["B:4", "B:8"])
        self.assertEqual({r["inventory"] for r in self.rows("duplicates.csv")}, {"summary"})

    def test_missing_source_and_empty_id_are_errors_before_output_creation(self):
        self.write(self.b, [["P", "B:1"]])
        for row in (["P", ""], ["P", " \t"], ["", "A:1"], [" \t", "A:1"]):
            with self.subTest(row=row):
                self.write(self.a, [row])
                self.assertEqual(self.cli(), 2)
                self.assertFalse(self.output.exists())

    def test_invalid_csv_structure_is_rejected(self):
        self.write(self.b, [["P", "B:1"]])
        cases = [
            "program_id\nP\n",
            "program_id,source_ref,source_ref\nP,A:1,A:1\n",
            "program_id,,source_ref\nP,x,A:1\n",
            " program_id,source_ref\nP,A:1\n",
            "program_id,source_ref\nP\n",
            "program_id,source_ref\nP,A:1,extra\n",
            "program_id,source_ref\nprogram_id,source_ref\n",
            'program_id,source_ref\nP,"unterminated\n',
            'program_id,source_ref\n""\n',
            "program_id,source_ref\n,,\n",
            "program_id,source_ref\n,\n",
        ]
        for text in cases:
            with self.subTest(text=text):
                self.a.write_text(text, encoding="utf-8")
                self.assertEqual(self.cli(), 2)
                self.assertFalse(self.output.exists())

    def test_empty_or_header_only_inputs_are_rejected(self):
        self.write(self.b, [["P", "B:1"]])
        for text in ("", "\n \t\n", "program_id,source_ref\n", "\ufeff"):
            with self.subTest(text=text):
                self.a.write_text(text, encoding="utf-8")
                self.assertEqual(self.cli(), 2)
                self.assertFalse(self.output.exists())

    def test_pure_blank_lines_are_skipped_and_counted(self):
        self.a.write_text("\n  \t\nprogram_id,source_ref\nP,A:2\n\n", encoding="utf-8")
        self.write(self.b, [["P", "B:1"]])
        self.assertEqual(self.cli(), 0)
        stats = self.report()["inputs"]["release"]
        self.assertEqual(stats["skipped_blank_line_count"], 3)
        self.assertEqual(stats["record_count"], 1)
        row = self.rows("matched.csv")[0]
        self.assertEqual(row["csv_record"], "4")
        self.assertEqual(row["csv_line_start"], "4")

    def test_utf8_bom_is_accepted_by_default_and_output_has_bom(self):
        self.write(self.a, [["日本語", "資料:1"]])
        self.write(self.b, [["日本語", "別資料:2"]])
        self.assertTrue(self.a.read_bytes().startswith(b"\xef\xbb\xbf"))
        self.assertEqual(self.cli(), 0)
        self.assertTrue((self.output / "matched.csv").read_bytes().startswith(b"\xef\xbb\xbf"))
        self.assertEqual(self.rows("matched.csv")[0]["program_id"], "日本語")

    def test_cp932_requires_explicit_encoding(self):
        self.write(self.a, [["日本語", "資料:1"]], encoding="cp932")
        self.write(self.b, [["日本語", "別資料:2"]], encoding="cp932")
        self.assertEqual(self.cli(), 2)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.cli(["--release-encoding", "cp932", "--summary-encoding", "cp932"]), 0)
        self.assertEqual(self.report()["inputs"]["release"]["encoding"], "cp932")

    def test_decode_errors_and_unknown_encoding_are_rejected(self):
        self.write(self.b, [["P", "B:1"]])
        self.a.write_bytes(b"program_id,source_ref\n\xff,A:1\n")
        self.assertEqual(self.cli(), 2)
        self.assertFalse(self.output.exists())
        self.write(self.a, [["P", "A:1"]])
        self.assertEqual(self.cli(["--release-encoding", "not-an-encoding"]), 2)
        self.assertFalse(self.output.exists())

    def test_existing_directory_is_never_overwritten(self):
        self.write(self.a, [["P", "A:1"]])
        self.write(self.b, [["P", "B:1"]])
        self.output.mkdir()
        sentinel = self.output / "report.json"
        sentinel.write_text("original content", encoding="utf-8")
        self.assertEqual(self.cli(), 2)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "original content")
        self.assertEqual(list(self.output.iterdir()), [sentinel])

    def test_existing_file_is_never_overwritten(self):
        self.write(self.a, [["P", "A:1"]])
        self.write(self.b, [["P", "B:1"]])
        self.output.write_text("keep", encoding="utf-8")
        self.assertEqual(self.cli(), 2)
        self.assertEqual(self.output.read_text(encoding="utf-8"), "keep")

    def test_output_created_between_check_and_mkdir_is_not_overwritten(self):
        self.write(self.a, [["P", "A:1"]])
        self.write(self.b, [["P", "B:1"]])
        original_mkdir = Path.mkdir

        def concurrent_mkdir(path, *args, **kwargs):
            if path == self.output:
                original_mkdir(path)
                (path / "sentinel").write_text("keep", encoding="utf-8")
            return original_mkdir(path, *args, **kwargs)

        with mock.patch.object(Path, "mkdir", concurrent_mkdir):
            self.assertEqual(self.cli(), 2)
        self.assertEqual((self.output / "sentinel").read_text(encoding="utf-8"), "keep")
        self.assertFalse((self.output / "report.json").exists())

    def test_both_inputs_are_fully_validated_before_creating_output(self):
        self.write(self.a, [["P", "A:1"]])
        self.write(self.b, [["P", "B:1"], ["Q", ""]])
        self.assertEqual(self.cli(), 2)
        self.assertFalse(self.output.exists())

    def test_multiline_source_ref_keeps_logical_and_physical_locations(self):
        self.write(self.a, [["P", "original.txt:4\ncontinued:5"], ["Q", "original.txt:8"]])
        self.write(self.b, [["P", "B:1"], ["Q", "B:2"]])
        self.assertEqual(self.cli(), 0)
        rows = [r for r in self.rows("matched.csv") if r["inventory"] == "release"]
        self.assertEqual(rows[0]["source_ref"], "original.txt:4\ncontinued:5")
        self.assertEqual(rows[0]["csv_record"], "2")
        self.assertEqual(rows[0]["csv_line_start"], "2")
        self.assertEqual(rows[0]["csv_line_end"], "3")
        self.assertEqual(rows[1]["csv_record"], "3")
        self.assertEqual(rows[1]["csv_line_start"], "4")

    def test_set_reconciliation_and_all_records_survive_classification(self):
        a_ids = ["A", "B", "B", "C", "D", "D"]
        b_ids = ["B", "B", "D", "E", "F", "F", "F"]
        self.write(self.a, [[value, "A:{}".format(i)] for i, value in enumerate(a_ids, 1)])
        self.write(self.b, [[value, "B:{}".format(i)] for i, value in enumerate(b_ids, 1)])
        self.assertEqual(self.cli(), 1)
        report = self.report()
        counts = report["unique_id_counts"]
        self.assertEqual(counts, {"release": 4, "summary": 4, "matched": 2, "release_only": 2, "summary_only": 2})
        self.assertEqual(counts["release"], counts["matched"] + counts["release_only"])
        self.assertEqual(counts["summary"], counts["matched"] + counts["summary_only"])
        classified = self.rows("matched.csv") + self.rows("release_only.csv") + self.rows("summary_only.csv")
        self.assertEqual(len(classified), len(a_ids) + len(b_ids))
        self.assertEqual(len({(r["inventory"], r["csv_record"]) for r in classified}), len(classified))
        self.assertEqual(len(self.rows("duplicates.csv")), 9)

    def test_additional_named_columns_are_allowed_with_exact_column_count(self):
        self.write(self.a, [["A:3", "P", "notes"]], headers=("source_ref", "program_id", "note"))
        self.write(self.b, [["P", "B:5"]])
        self.assertEqual(self.cli(), 0)
        self.assertEqual(self.rows("matched.csv")[0]["source_ref"], "A:3")

    def test_output_write_failure_returns_two_and_does_not_write_success_report(self):
        self.write(self.a, [["P", "A:1"]])
        self.write(self.b, [["P", "B:1"]])
        with mock.patch.object(tool, "write_csv", side_effect=OSError("simulated disk error")):
            self.assertEqual(self.cli(), 2)
        self.assertFalse((self.output / "report.json").exists())

    def test_executable_cli_has_documented_exit_codes(self):
        self.write(self.a, [["P", "A:1"]])
        self.write(self.b, [["Q", "B:1"]])
        result = subprocess.run(
            [sys.executable, str(Path(tool.__file__)), "--release", str(self.a),
             "--summary", str(self.b), "--output", str(self.output)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertNotIn(b"Traceback", result.stderr)
        self.assertEqual(self.report()["exit_code"], 1)
        invalid = subprocess.run([sys.executable, str(Path(tool.__file__))],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(invalid.returncode, 2)


if __name__ == "__main__":
    unittest.main()
