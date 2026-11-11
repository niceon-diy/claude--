#!/usr/bin/env python3
"""Check provenance and workflow boundaries for a local Markdown knowledge base.

Python 3.10+, standard library only. This tool checks recorded evidence and file
changes; it cannot establish whether a source actually supports a written claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import ntpath
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from datetime import date, datetime, timezone
from urllib.parse import unquote, urlsplit


SCHEMA_VERSION = 1
STATUSES = {"draft", "needs-review", "verified", "conflict", "superseded"}
ROLES = {"requirement", "current", "reference", "repository-example"}
SOURCE_FIELDS = ("path", "sha256", "locator", "version", "origin", "retrieved_at", "role")
META_BLOCK = re.compile(r"^```json[ \t]*\r?\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)
MD_LINK = re.compile(r'(?<!!)\[[^\]\n]*\]\((?:<([^>]+)>|([^\s)]+))(?:\s+"[^"\n]*")?\)')


class CheckError(ValueError):
    pass


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def linked(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def inside(path: Path, directory: Path) -> bool:
    return path == directory or directory in path.parents


def safe_path(root: Path, relative: str) -> Path:
    if not nonempty(relative) or "\\" in relative or ntpath.isabs(relative):
        raise CheckError(f"路径必须使用根目录内的相对路径和正斜杠: {relative!r}")
    parsed = PurePosixPath(relative)
    if parsed.is_absolute() or ".." in parsed.parts or parsed.as_posix() != relative:
        raise CheckError(f"路径不规范或越界: {relative!r}")
    result = root.joinpath(*parsed.parts)
    for candidate in (result, *result.parents):
        if candidate == root:
            break
        if linked(candidate):
            raise CheckError(f"不接受符号链接或目录联接: {relative}")
    if not inside(result.resolve(), root):
        raise CheckError(f"路径越出知识库根目录: {relative}")
    return result


def output_path(root: Path, argument: str) -> Path:
    candidate = Path(argument)
    if candidate.is_absolute():
        try:
            relative = candidate.relative_to(root).as_posix()
        except ValueError as exc:
            raise CheckError("输出文件必须位于知识库根目录内") from exc
    else:
        relative = candidate.as_posix()
    result = safe_path(root, relative)
    if any(inside(result, root / protected) for protected in ("raw", "wiki/Concepts")):
        raise CheckError("基线或报告不得写入 raw/ 或 wiki/Concepts/")
    if result.suffix.lower() != ".json":
        raise CheckError("基线和报告输出必须使用 .json 扩展名")
    return result


def save_new_json(path: Path, data: dict) -> None:
    """Publish a complete file atomically, without replacing an existing path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise CheckError(f"拒绝覆盖已有文件，请使用新的运行编号: {path}")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=path.parent, prefix=".kb-check-", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # link() fails when the target exists. Unlike replace(), it cannot
        # overwrite a baseline created concurrently by another process.
        os.link(temporary, path)
    except FileExistsError as exc:
        raise CheckError(f"拒绝覆盖已有文件: {path}") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def source_key(source: dict) -> tuple:
    return tuple(source[field].lower() if field == "sha256" else source[field]
                 for field in SOURCE_FIELDS)


def metadata_from_text(text: str, relative: str) -> tuple[dict, str]:
    match = META_BLOCK.search(text)
    if not match:
        raise CheckError(f"{relative}: 缺少首个 JSON 元数据代码块")
    try:
        metadata = json.loads(match.group(1))
    except (ValueError, TypeError) as exc:
        raise CheckError(f"{relative}: JSON 元数据无效: {exc}") from exc
    if not isinstance(metadata, dict):
        raise CheckError(f"{relative}: 元数据必须是 JSON 对象")
    return metadata, text[match.end():]


def validate_metadata(metadata: dict, label: str) -> None:
    def require(condition: bool, message: str) -> None:
        if not condition:
            raise CheckError(f"{label}: {message}")

    kind = metadata.get("kind")
    require(kind in ("ingest", "concept"), "kind 必须是 ingest 或 concept")
    note_id = metadata.get("id")
    prefix = "I" if kind == "ingest" else "C"
    require(isinstance(note_id, str) and re.fullmatch(prefix + r"\d{3,}", note_id) is not None,
            f"id 必须是 {prefix} 加至少三位数字")
    require(nonempty(metadata.get("scope")), "scope 不能为空")
    require(metadata.get("status") in STATUSES, "status 无效")
    sources = metadata.get("sources")
    require(isinstance(sources, list) and bool(sources), "sources 必须是非空数组")
    refs = set()
    for source in sources:
        require(isinstance(source, dict), "每条 source 必须是 JSON 对象")
        require(all(nonempty(source.get(field)) for field in (*SOURCE_FIELDS, "ref")),
                "source 缺少非空 ref/path/sha256/locator/version/origin/retrieved_at/role")
        require(re.fullmatch(r"S[1-9]\d*", source["ref"]) is not None, "source ref 必须是 S1、S2 等")
        require(source["ref"] not in refs, f"重复 source ref: {source['ref']}")
        refs.add(source["ref"])
        require(re.fullmatch(r"[a-fA-F0-9]{64}", source["sha256"]) is not None, "source sha256 必须是64位十六进制")
        require(source["role"] in ROLES, "source role 无效")
    parents = metadata.get("derived_from")
    require(isinstance(parents, list) and all(nonempty(value) for value in parents),
            "derived_from 必须是 ID 字符串数组")
    require(len(parents) == len(set(parents)), "derived_from 不得重复")
    require(note_id not in parents, "笔记不能从自身派生")
    require((kind == "ingest" and not parents) or (kind == "concept" and bool(parents)),
            "ingest 的 derived_from 必须为空；concept 必须至少有一个父笔记")
    if metadata["status"] == "verified":
        review = metadata.get("review")
        require(isinstance(review, dict) and all(nonempty(review.get(key)) for key in ("reviewer", "date", "method")),
                "verified 必须提供 review.reviewer/date/method")
        try:
            reviewed = date.fromisoformat(review["date"])
            require(reviewed.isoformat() == review["date"], "review.date 必须是 YYYY-MM-DD")
        except ValueError as exc:
            raise CheckError(f"{label}: review.date 必须是有效的 YYYY-MM-DD 日期") from exc


def collect(root: Path) -> tuple[dict, list[str]]:
    errors = []
    raw_files = {}
    notes = {}
    for directory in ("raw", "wiki/Concepts"):
        target = safe_path(root, directory)
        if not target.is_dir():
            raise CheckError(f"缺少目录: {directory}/")
    for file in sorted((root / "raw").rglob("*")):
        relative = file.relative_to(root).as_posix()
        try:
            safe_path(root, relative)
            if file.is_file() and file.name != ".gitkeep":
                raw_files[relative] = digest(file)
        except (CheckError, OSError) as exc:
            errors.append(str(exc))
    for file in sorted((root / "wiki/Concepts").rglob("*")):
        relative = file.relative_to(root).as_posix()
        try:
            safe_path(root, relative)
            if not file.is_file() or file.suffix.lower() != ".md":
                continue
            text = file.read_text(encoding="utf-8-sig")
            metadata, body = metadata_from_text(text, relative)
            validate_metadata(metadata, relative)
            notes[relative] = {"sha256": digest(file), "metadata": metadata}
            for source in metadata["sources"]:
                path = safe_path(root, source["path"])
                if not source["path"].startswith("raw/") or not path.is_file():
                    raise CheckError(f"{relative}: 来源必须是 raw/ 内存在的文件: {source['path']}")
                if raw_files.get(source["path"]) != source["sha256"].lower():
                    raise CheckError(f"{relative}: 来源哈希不符或文件不可读取: {source['path']}")
                if f"[{source['ref']}]" not in body:
                    raise CheckError(f"{relative}: 正文缺少来源引用 [{source['ref']}]")
            refs = {source["ref"] for source in metadata["sources"]}
            unknown = set(re.findall(r"\[(S[1-9]\d*)\]", body)) - refs
            if unknown:
                errors.append(f"{relative}: 正文含未定义来源引用: {', '.join(sorted(unknown))}")
            for match in MD_LINK.finditer(body):
                url = match.group(1) or match.group(2)
                parsed = urlsplit(url)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                link = unquote(parsed.path)
                if Path(link).suffix.lower() != ".md":
                    continue
                destination = (file.parent / link).resolve()
                if not inside(destination, root) or not destination.is_file():
                    errors.append(f"{relative}: 本地 Markdown 链接不存在或越界: {url}")
                else:
                    safe_path(root, destination.relative_to(root).as_posix())
        except (CheckError, OSError, UnicodeError, ValueError) as exc:
            errors.append(str(exc))
    by_id = {}
    for relative, entry in notes.items():
        metadata = entry["metadata"]
        note_id = metadata["id"]
        if note_id in by_id:
            errors.append(f"重复笔记 ID {note_id}: {by_id[note_id][0]} / {relative}")
        else:
            by_id[note_id] = (relative, metadata)
    for relative, entry in notes.items():
        metadata = entry["metadata"]
        permitted = set()
        for parent in metadata["derived_from"]:
            if parent not in by_id:
                errors.append(f"{relative}: 派生父笔记不存在: {parent}")
                continue
            parent_meta = by_id[parent][1]
            if parent_meta["scope"] != metadata["scope"]:
                errors.append(f"{relative}: 不得跨 scope 派生: {parent}")
            permitted.update(source_key(source) for source in parent_meta["sources"])
        if metadata["kind"] == "concept" and not {source_key(source) for source in metadata["sources"]} <= permitted:
            errors.append(f"{relative}: concept 引入了父笔记之外的来源或来源背景")
    # Iterative topological traversal avoids Python recursion limits on large wikis.
    pending = {key: set(value[1]["derived_from"]) & set(by_id) for key, value in by_id.items()}
    children = {key: set() for key in pending}
    for child, parents in pending.items():
        for parent in parents:
            children[parent].add(child)
    ready = [key for key, parents in pending.items() if not parents]
    visited = set()
    while ready:
        parent = ready.pop()
        if parent in visited:
            continue
        visited.add(parent)
        for child in children[parent]:
            pending[child].discard(parent)
            if not pending[child]:
                ready.append(child)
    if len(visited) != len(pending):
        errors.append("笔记派生关系存在循环: " + ", ".join(sorted(set(pending) - visited)))
    return {"schema_version": SCHEMA_VERSION, "root": str(root),
            "raw_files": raw_files, "notes": notes}, errors


def load_baseline(root: Path, argument: str) -> dict:
    path = output_path(root, argument)
    try:
        baseline = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise CheckError(f"无法读取基线: {exc}") from exc
    if not isinstance(baseline, dict) or baseline.get("schema_version") != SCHEMA_VERSION:
        raise CheckError("基线 schema_version 无效")
    if baseline.get("root") != str(root):
        raise CheckError("基线属于其他知识库根目录")
    for field in ("raw_files", "notes"):
        if not isinstance(baseline.get(field), dict):
            raise CheckError(f"基线缺少有效 {field}")
    ids = set()
    for relative, value in baseline["raw_files"].items():
        safe_path(root, relative)
        if not relative.startswith("raw/") or not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
            raise CheckError("基线 raw_files 格式无效")
    for relative, entry in baseline["notes"].items():
        safe_path(root, relative)
        if not relative.startswith("wiki/Concepts/") or not isinstance(entry, dict):
            raise CheckError("基线笔记路径或内容无效")
        if not isinstance(entry.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", entry["sha256"]):
            raise CheckError("基线笔记哈希无效")
        metadata = entry.get("metadata")
        if not isinstance(metadata, dict):
            raise CheckError("基线笔记元数据无效")
        validate_metadata(metadata, relative)
        if metadata["id"] in ids:
            raise CheckError("基线笔记 ID 重复")
        ids.add(metadata["id"])
    return baseline


def compare_baseline(current: dict, baseline: dict, mode: str) -> list[str]:
    errors = []
    before_raw, after_raw = baseline["raw_files"], current["raw_files"]
    for relative in sorted(set(before_raw) | set(after_raw)):
        if before_raw.get(relative) != after_raw.get(relative):
            change = "新增" if relative not in before_raw else "删除" if relative not in after_raw else "改写"
            errors.append(f"raw 原件发生{change}: {relative}")
    before, after = baseline["notes"], current["notes"]
    before_ids = {entry["metadata"]["id"]: entry["metadata"] for entry in before.values()}
    for relative in sorted(set(before) - set(after)):
        errors.append(f"不得删除已有笔记: {relative}")
    for relative, entry in after.items():
        old = before.get(relative)
        if old and old["sha256"] == entry["sha256"]:
            continue
        metadata = entry["metadata"]
        if old:
            for field in ("id", "kind", "scope"):
                if metadata[field] != old["metadata"][field]:
                    errors.append(f"{relative}: 已有笔记的 {field} 必须保持稳定")
        if metadata["status"] == "verified":
            errors.append(f"{relative}: {mode} 不得新增或改写 verified 笔记，需降为 needs-review 后单独核验")
        if mode == "ingest":
            if old:
                errors.append(f"{relative}: ingest 不得改写已有笔记")
            elif metadata["kind"] != "ingest":
                errors.append(f"{relative}: ingest 只允许新增 ingest 笔记")
            continue
        if metadata["kind"] != "concept" or (old and old["metadata"]["kind"] != "concept"):
            errors.append(f"{relative}: refine 只允许新增或改写 concept，ingest 笔记必须保持原样")
            continue
        permitted = set()
        for parent in metadata["derived_from"]:
            if parent not in before_ids:
                errors.append(f"{relative}: refine 的父笔记必须在基线中存在: {parent}")
            else:
                if before_ids[parent]["scope"] != metadata["scope"]:
                    errors.append(f"{relative}: refine 不得变更来源 scope: {parent}")
                permitted.update(source_key(source) for source in before_ids[parent]["sources"])
        if not {source_key(source) for source in metadata["sources"]} <= permitted:
            errors.append(f"{relative}: refine 引入了基线父笔记之外的新来源或新来源背景")
    return errors


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    snapshot = commands.add_parser("snapshot", help="保存 raw 与笔记的不可覆盖基线")
    snapshot.add_argument("--root", default=".")
    snapshot.add_argument("--output", required=True)
    validate = commands.add_parser("validate", help="检查来源、引用与可选流程边界")
    validate.add_argument("--root", default=".")
    validate.add_argument("--baseline")
    validate.add_argument("--mode", choices=("ingest", "refine"))
    validate.add_argument("--report")
    return result


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    report = {"command": args.command, "ok": False, "errors": [],
              "limits": ["仅核对来源元数据、文件哈希、引用及流程边界，不证明正文事实正确或实际已被 Agent 使用。"]}
    report_path = None
    try:
        root = Path(args.root).resolve(strict=True)
        if not root.is_dir():
            raise CheckError("--root 必须是知识库目录")
        if args.command == "validate":
            if bool(args.baseline) != bool(args.mode):
                raise CheckError("--baseline 与 --mode 必须同时提供")
            if args.report:
                report_path = output_path(root, args.report)
        current, errors = collect(root)
        report.update(root=str(root), counts={"raw_files": len(current["raw_files"]), "notes": len(current["notes"])})
        if args.command == "validate" and args.baseline:
            errors.extend(compare_baseline(current, load_baseline(root, args.baseline), args.mode))
        report["errors"] = errors
        report["ok"] = not errors
        if args.command == "snapshot" and not errors:
            current["created_at"] = datetime.now(timezone.utc).isoformat()
            path = output_path(root, args.output)
            save_new_json(path, current)
            report["snapshot"] = str(path)
    except (CheckError, OSError, ValueError, TypeError, KeyError) as exc:
        report["ok"] = False
        report["errors"].append(str(exc))
    if report_path is not None:
        try:
            save_new_json(report_path, report)
            report["report"] = str(report_path)
        except (CheckError, OSError) as exc:
            report["ok"] = False
            report["errors"].append(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
