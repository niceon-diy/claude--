#!/usr/bin/env python3
"""Compare two program inventories without guessing aliases or identity rules.

Inputs are CSV files containing program_id and source_ref. Output CSV files use
UTF-8 with BOM. matched.csv is a long table: it retains every original record
from both inventories for each shared ID, rather than pairing duplicate rows.
Only program_id.strip() is used as the comparison key.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


FIELDS = (
    "program_id", "inventory", "original_program_id", "source_ref",
    "input_csv", "csv_record", "csv_line_start", "csv_line_end",
)
OUTPUT_FILES = (
    "matched.csv", "release_only.csv", "summary_only.csv", "duplicates.csv",
)


class InventoryError(ValueError):
    """An input or output requirement was not satisfied."""


@dataclass(frozen=True)
class Record:
    program_id: str
    original_program_id: str
    source_ref: str
    csv_record: int
    csv_line_start: int
    csv_line_end: int


@dataclass
class Inventory:
    path: Path
    encoding: str
    sha256: str
    headers: Tuple[str, ...]
    records: List[Record]
    by_id: Dict[str, List[Record]]
    skipped_blank_line_count: int
    csv_record_count: int
    header_line_start: int
    header_line_end: int

    def statistics(self) -> dict:
        duplicate_groups = [rows for rows in self.by_id.values() if len(rows) > 1]
        return {
            "path": str(self.path),
            "encoding": self.encoding,
            "sha256": self.sha256,
            "headers": list(self.headers),
            "record_count": len(self.records),
            "unique_id_count": len(self.by_id),
            "duplicate_id_count": len(duplicate_groups),
            "duplicate_extra_record_count": sum(len(rows) - 1 for rows in duplicate_groups),
            "duplicate_record_count": sum(len(rows) for rows in duplicate_groups),
            "skipped_blank_line_count": self.skipped_blank_line_count,
            "csv_record_count": self.csv_record_count,
            "header_line_start": self.header_line_start,
            "header_line_end": self.header_line_end,
        }


def read_inventory(path: Path, encoding: str = "utf-8-sig") -> Inventory:
    """Validate the entire input before any output directory is created.

    csv_record counts logical CSV records, including the header and skipped
    blank records. csv_line_start/end are physical CSV line numbers. source_ref
    remains the location in the original document; these are distinct locators.
    """
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    try:
        text = raw.decode(encoding, errors="strict")
    except (UnicodeError, LookupError) as exc:
        raise InventoryError("无法按指定编码读取 {}：{}".format(path, encoding)) from exc

    physical_lines = list(io.StringIO(text, newline=""))
    reader = csv.reader(physical_lines, strict=True)
    headers = None
    records = []
    by_id = defaultdict(list)
    blank_lines = 0
    logical_record = 0
    header_start = header_end = 0

    while True:
        line_start = reader.line_num + 1
        try:
            row = next(reader)
        except StopIteration:
            break
        except csv.Error as exc:
            raise InventoryError(
                "CSV结构无效：{}，物理行{}附近：{}".format(path, reader.line_num, exc)
            ) from exc
        logical_record += 1
        line_end = reader.line_num
        raw_record = "".join(physical_lines[line_start - 1:line_end])
        # Empty quoted fields and delimiter-only records are NOT blank lines.
        if not raw_record.strip():
            blank_lines += line_end - line_start + 1
            continue

        location = "{}，CSV记录{}，物理行{}-{}".format(
            path, logical_record, line_start, line_end
        )
        if headers is None:
            if any(not name.strip() for name in row):
                raise InventoryError("表头名称为空：" + location)
            if len(set(row)) != len(row):
                raise InventoryError("存在重复表头：" + location)
            missing = {"program_id", "source_ref"} - set(row)
            if missing:
                raise InventoryError("缺少必需字段 {}：{}".format(
                    ", ".join(sorted(missing)), location
                ))
            headers = tuple(row)
            id_index = row.index("program_id")
            source_index = row.index("source_ref")
            header_start, header_end = line_start, line_end
            continue

        if len(row) != len(headers):
            raise InventoryError("列数异常：{}，预期{}列，实际{}列".format(
                location, len(headers), len(row)
            ))
        if tuple(row) == headers:
            raise InventoryError("数据区出现重复表头行：" + location)
        original_id = row[id_index]
        program_id = original_id.strip()
        if not program_id:
            raise InventoryError("program_id为空：" + location)
        source_ref = row[source_index]
        if not source_ref.strip():
            raise InventoryError("source_ref缺少原始资料定位：" + location)
        record = Record(
            program_id, original_id, source_ref, logical_record,
            line_start, line_end,
        )
        records.append(record)
        by_id[program_id].append(record)

    if headers is None or not records:
        raise InventoryError("输入没有有效程序记录：" + str(path))
    return Inventory(
        path, encoding, hashlib.sha256(raw).hexdigest(), headers, records,
        dict(by_id), blank_lines, logical_record, header_start, header_end,
    )


def output_record(inventory: Inventory, label: str, record: Record) -> dict:
    return {
        "program_id": record.program_id,
        "inventory": label,
        "original_program_id": record.original_program_id,
        "source_ref": record.source_ref,
        "input_csv": str(inventory.path),
        "csv_record": record.csv_record,
        "csv_line_start": record.csv_line_start,
        "csv_line_end": record.csv_line_end,
    }


def write_csv(path: Path, fields: Sequence[str], rows: Sequence[dict]) -> None:
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def compare(
    release_path: Path,
    summary_path: Path,
    output_path: Path,
    release_encoding: str = "utf-8-sig",
    summary_encoding: str = "utf-8-sig",
) -> dict:
    release = read_inventory(release_path, release_encoding)
    summary = read_inventory(summary_path, summary_encoding)
    a, b = set(release.by_id), set(summary.by_id)
    shared, only_a, only_b = a & b, a - b, b - a
    assert len(a) == len(shared) + len(only_a)
    assert len(b) == len(shared) + len(only_b)

    matched = []
    for program_id in sorted(shared):
        for inventory, label in ((release, "release"), (summary, "summary")):
            matched.extend(output_record(inventory, label, record)
                           for record in inventory.by_id[program_id])
    release_only = [output_record(release, "release", record)
                    for key in sorted(only_a) for record in release.by_id[key]]
    summary_only = [output_record(summary, "summary", record)
                    for key in sorted(only_b) for record in summary.by_id[key]]
    duplicates = []
    for inventory, label in ((release, "release"), (summary, "summary")):
        for key in sorted(inventory.by_id):
            rows = inventory.by_id[key]
            if len(rows) > 1:
                for record in rows:
                    item = output_record(inventory, label, record)
                    item["occurrences"] = len(rows)
                    duplicates.append(item)

    needs_review = bool(only_a or only_b or duplicates)
    report = {
        "schema_version": 1,
        "exit_code": 1 if needs_review else 0,
        "needs_review": needs_review,
        "comparison_rule": {
            "normalization": "仅对program_id首尾执行str.strip()；不做其他转换",
            "case_sensitive": True,
            "paths_and_extensions_preserved": True,
            "alias_inference": False,
            "header_names": "必需字段名精确匹配；表头不自动trim",
        },
        "scope_limits": [
            "仅证明这两份CSV输入在上述精确标识规则下的差异。",
            "release_only是疑似遗漏，须回到原始资料核对提取、版本和Release范围。",
            "程序名相同不证明版本、内容或适用范围相同。",
            "CSV比对通过不证明原文提取完整，也不证明业务无遗漏。",
        ],
        "inputs": {"release": release.statistics(), "summary": summary.statistics()},
        "unique_id_counts": {
            "release": len(a), "summary": len(b), "matched": len(shared),
            "release_only": len(only_a), "summary_only": len(only_b),
        },
        "reconciliation": {
            "release": {"unique_ids": len(a), "matched_plus_only": len(shared) + len(only_a), "passed": True},
            "summary": {"unique_ids": len(b), "matched_plus_only": len(shared) + len(only_b), "passed": True},
        },
        "output_record_counts": {
            "matched.csv": len(matched), "release_only.csv": len(release_only),
            "summary_only.csv": len(summary_only), "duplicates.csv": len(duplicates),
        },
        "record_count_definitions": {
            "record_count": "有效数据原始记录数，包含重复；不含表头和跳过的纯空白行",
            "duplicate_id_count": "在同一输入中出现多次的唯一ID数",
            "duplicate_extra_record_count": "每个重复组除首次外的额外记录数",
            "duplicate_record_count": "所有重复组涉及的全部原始记录数",
            "csv_record": "逻辑CSV记录号，从1开始，包含表头和跳过的空白记录",
            "csv_line_start/end": "CSV物理起止行号；与source_ref原始资料定位分别保留",
            "matched.csv": "共同ID的两侧全部原行，长表形式，不是成对记录或唯一ID数量",
            "duplicates.csv": "同侧重复组全部原行；occurrences为该ID在该侧的出现次数",
        },
    }

    output_path = Path(output_path)
    if output_path.exists() or output_path.is_symlink():
        raise InventoryError("输出路径已存在，拒绝覆盖：" + str(output_path))
    output_path = output_path.resolve()
    if output_path.exists() or output_path.is_symlink():
        raise InventoryError("输出路径已存在，拒绝覆盖：" + str(output_path))
    # mkdir(exist_ok=False) also rejects a directory created after the check.
    output_path.mkdir(parents=True, exist_ok=False)
    write_csv(output_path / OUTPUT_FILES[0], FIELDS, matched)
    write_csv(output_path / OUTPUT_FILES[1], FIELDS, release_only)
    write_csv(output_path / OUTPUT_FILES[2], FIELDS, summary_only)
    write_csv(output_path / OUTPUT_FILES[3], FIELDS + ("occurrences",), duplicates)
    # Write the report last so a failed CSV write has no success report.
    with (output_path / "report.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="按精确程序标识核对两份CSV清单；仅trim首尾空白。")
    parser.add_argument("--release", type=Path, required=True, help="本番Release清单CSV（A）")
    parser.add_argument("--summary", type=Path, required=True, help="Claude提取清单CSV（B）")
    parser.add_argument("--output", type=Path, required=True, help="尚不存在的输出目录")
    parser.add_argument("--release-encoding", default="utf-8-sig")
    parser.add_argument("--summary-encoding", default="utf-8-sig")
    args = parser.parse_args(argv)
    try:
        report = compare(args.release, args.summary, args.output,
                         args.release_encoding, args.summary_encoding)
    except Exception as exc:
        print("比对失败：{}: {}".format(type(exc).__name__, exc), file=sys.stderr)
        return 2
    counts = report["unique_id_counts"]
    if report["needs_review"]:
        print("比对已完成：存在差异或重复，待人工核查（退出码1）。")
    else:
        print("比对已完成：两份CSV在当前规则下一致且无重复（退出码0）。")
    print("共同ID：{matched}；Release独有（疑似遗漏）：{release_only}；提取独有：{summary_only}。".format(**counts))
    duplicate_extras = sum(item["duplicate_extra_record_count"] for item in report["inputs"].values())
    print("额外重复记录：{}。结果目录：{}".format(duplicate_extras, args.output.resolve()))
    print("仅核对指定CSV；不证明原文提取完整、版本范围一致或业务无遗漏。")
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
