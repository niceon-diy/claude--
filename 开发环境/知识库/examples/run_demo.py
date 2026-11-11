#!/usr/bin/env python3
"""Create an isolated, explicitly fictional ingest/refine file-flow demo.

No model calls, Box requests, dependency downloads or company data are involved.
Run from the knowledge-base directory, e.g.:
  python examples/run_demo.py --output examples/my-demo-001
The destination must not already exist. Existing files are never overwritten.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


KIT = Path(__file__).resolve().parents[1]
CHECKER = KIT / "tools" / "kb_check.py"
SCOPE = "DEMO-001／DEMO_EXPORT／DEMO环境（虚构示意）"

RAW = {
    "DEMO-现行设计.md": """# DEMO 现行设计（虚构，非公司资料）

版本：DEMO-v2。用途：current，示意当前版本基准。

## 1. 适用范围

Thema 为 DEMO-001，环境为 DEMO，处理对象为 DEMO_EXPORT。

## 2. 输入约束

输入字段 DEMO_CODE 最多12个ASCII字符。空值不允许。

## 3. 输出

DEMO_EXPORT 将该字段输出到 demo.csv。本文件不包含数据库改修要求。
""",
    "DEMO-同版补充.md": """# DEMO 同版补充（虚构，非公司资料）

版本：DEMO-v2。用途：current，示意同版补充说明。

## 1. 适用范围

Thema 为 DEMO-001，环境为 DEMO，处理对象为 DEMO_EXPORT。

## 2. 输入约束

输入字段 DEMO_CODE 最多10个ASCII字符。空值不允许。

## 3. 优先级

本补充没有规定自己与现行设计之间的优先级。
""",
    "DEMO-历史参考.md": """# DEMO 历史参考（虚构，非公司资料）

版本：DEMO-v1。用途：reference，仅供历史参考。

## 1. 适用范围

Thema 为 DEMO-001，环境为 DEMO，处理对象为 DEMO_EXPORT。

## 2. 历史约束

历史版本字段 DEMO_CODE 最多8个ASCII字符，允许空值。
此条仅描述历史版本，不是本次现行规格。
""",
}


def write_new(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def check(root: Path, command: str, *arguments: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(CHECKER), command, "--root", str(root), *arguments],
        capture_output=True, text=True, encoding="utf-8", check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return json.loads(result.stdout)


def note(root: Path, note_id: str, title: str, sources: list[dict], body: str,
         *, parents: tuple[str, ...] = (), status: str = "draft") -> None:
    numbered_sources = [dict(source, ref=f"S{index}") for index, source in enumerate(sources, 1)]
    metadata = {
        "id": note_id, "kind": "concept" if parents else "ingest", "scope": SCOPE,
        "status": status, "sources": numbered_sources, "derived_from": list(parents),
    }
    text = f"# {title}（虚构示例）\n\n```json\n"
    text += json.dumps(metadata, ensure_ascii=False, indent=2) + "\n```\n\n" + body
    write_new(root / "wiki" / "Concepts" / f"{note_id}.md", text)


def build(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=False)
    (root / "wiki" / "Concepts").mkdir(parents=True)
    for name, content in RAW.items():
        write_new(root / "raw" / name, content)
    retrieved = datetime.now(timezone.utc).isoformat()

    def source(name: str, locator: str, version: str, role: str) -> dict:
        return {
            "path": "raw/" + name,
            "sha256": hashlib.sha256((root / "raw" / name).read_bytes()).hexdigest(),
            "locator": locator, "version": version,
            "origin": "本套件本地生成的虚构示例；非Box文件：" + name,
            "retrieved_at": retrieved, "role": role,
        }

    main_source = source("DEMO-现行设计.md", "第1节 适用范围；第2节 输入约束；第3节 输出", "DEMO-v2", "current")
    supplement = source("DEMO-同版补充.md", "第1节 适用范围；第2节 输入约束；第3节 优先级", "DEMO-v2", "current")
    history = source("DEMO-历史参考.md", "第1节 适用范围；第2节 历史约束", "DEMO-v1", "reference")

    # Raw files have landed before the ingest boundary starts.
    check(root, "snapshot", "--output", "wiki/.checks/001-ingest-before.json")
    note(root, "I001", "现行设计读取", [main_source], """## 实际读取范围

已读取全部第1～3节；这是一份虚构文本，没有隐藏表或附件。

## 有来源的事实

- 适用于 DEMO-001／DEMO_EXPORT／DEMO环境。[S1]
- DEMO_CODE 最多12个ASCII字符，空值不允许。[S1]
- DEMO_EXPORT 输出 demo.csv；这份设计未列出数据库改修要求。[S1]

## 待确认

没有关于错误重试、事务回滚的要求记录，不能据此判断真实系统行为。
""")
    note(root, "I002", "同版补充读取", [supplement], """## 实际读取范围

已读取全部第1～3节；仅描述这份补充自身的内容。

## 有来源的事实

- 适用于 DEMO-001／DEMO_EXPORT／DEMO环境。[S1]
- DEMO_CODE 最多10个ASCII字符，空值不允许。[S1]
- 文档没有规定自己与现行设计之间的优先级。[S1]
""")
    note(root, "I003", "历史参考读取", [history], """## 实际读取范围

已读取全部第1～2节；用途为历史参考。

## 有来源的事实

- DEMO-v1 的 DEMO_CODE 最多8个ASCII字符，允许空值。[S1]
- 这些限制只描述历史版本，不代表本次现行规格。[S1]
""")
    ingest_result = check(root, "validate", "--mode", "ingest", "--baseline", "wiki/.checks/001-ingest-before.json",
                          "--report", "wiki/.checks/001-ingest-result.json")

    check(root, "snapshot", "--output", "wiki/.checks/002-refine-before.json")
    note(root, "C001", "字段长度矛盾", [main_source, supplement], """## 矛盾与适用范围

以下均是 DEMO-001／DEMO_EXPORT／DEMO环境 的 DEMO-v2 声明：

- 现行设计写最多12个ASCII字符。[S1]
- 同版补充写最多10个ASCII字符。[S2]
- 补充没有声明文档之间的优先级。[S2]

现有笔记无法确定最终采用12还是10。保留 conflict，需向该示例的规格维护者确认。

## 派生与关联

- 来自 [I001 现行设计](I001.md) 和 [I002 同版补充](I002.md)。
- 关联的版本与空值规则笔记见 [C002](C002.md)。
""", parents=("I001", "I002"), status="conflict")
    note(root, "C002", "版本与空值规则", [main_source, history], """## 现有资料支持的结论

- DEMO-v2 现行设计不允许 DEMO_CODE 为空；DEMO_EXPORT 输出 demo.csv。[S1]
- DEMO-v1 历史参考允许空值，长度是8个ASCII字符；这是历史规则。[S2]
- 历史规则不能直接当成本次现行规格。[S2]

## 待确认

字段长度的关联笔记见 [C001](C001.md)。错误重试和事务回滚未收录，应回答“待确认”。

## 派生与关联

- 来自 [I001](I001.md) 与 [I003](I003.md)；不把版本差异隐藏为同一条无条件结论。
- 尚未进行人工业务核验，保持 needs-review。
""", parents=("I001", "I003"), status="needs-review")
    refine_result = check(root, "validate", "--mode", "refine", "--baseline", "wiki/.checks/002-refine-before.json",
                          "--report", "wiki/.checks/002-refine-result.json")
    final_result = check(root, "validate", "--report", "wiki/.checks/003-final-result.json")
    write_new(root / "README.md", """# 隔离的虚构样例

此目录所有设计、程序名、字段和业务约束均为本套件自造示意，不是公司事实。

- 三份 raw 文本在动作前已落地，随后保持字节不变。
- 三份 I 笔记演示读取；两份 C 笔记演示来源闭包与交叉链接。
- 当前规格的12／10字符矛盾保留为 conflict；历史的8字符不充当现行结论。
- [验证记录](验证记录.md)记录真实执行的脚本结果及未验证事项。
- 重演请从知识库根目录运行 `python examples/run_demo.py --output examples/my-demo-001`，目标必须是新目录。
""")
    write_new(root / "验证记录.md", f"""# 样例验证记录

执行时间（UTC）：{retrieved}

实际运行：Python 先建立 ingest 前快照，再创建 I 笔记并校验；随后建立 refine 前快照，再创建 C 笔记并校验。未调用 Claude CLI／模型 API，未访问 Box，未使用公司资料。

| 检查 | 实际结果 | 报告 |
| --- | --- | --- |
| ingest 模式 | {'通过' if ingest_result['ok'] else '失败'}；3原件、3初始笔记，raw未变 | [JSON](wiki/.checks/001-ingest-result.json) |
| refine 模式 | {'通过' if refine_result['ok'] else '失败'}；3原件、5笔记，I和raw未变 | [JSON](wiki/.checks/002-refine-result.json) |
| 最终结构与来源 | {'通过' if final_result['ok'] else '失败'}；ID、来源哈希、父项、scope、本地笔记链接合法 | [JSON](wiki/.checks/003-final-result.json) |

## 可人工对照的示意问答

这是示意预期与样例笔记的对照，不是独立模型问答评测或公司业务验收。

| 问题 | 应保留的答案 | 笔记与来源 |
| --- | --- | --- |
| 当前长度上限？ | 现行设计12、同版补充10，优先级未知；不能自行选定 | [C001](wiki/Concepts/C001.md)，S1／S2 |
| 允许空值吗？ | v2不允许；v1历史参考允许，须区分版本 | [C002](wiki/Concepts/C002.md)，S1／S2 |
| 历史8字符是否可直接采用？ | 不可作为本次现行结论 | [I003](wiki/Concepts/I003.md)，S1 |
| 输出到哪里？ | v2现行设计写 demo.csv | [C002](wiki/Concepts/C002.md)，S1 |
| 失败后是否自动回滚？ | 未收录／待确认 | [C002](wiki/Concepts/C002.md)，待确认段 |

## 验证限制

脚本只能核对文件与元数据约束，不能证明每句话忠实于来源、业务覆盖完整或模型未读取额外资料。示意笔记未标 verified。

公司端 Claude 的技能发现、实际 `/ingest`／`/refine` 行为、复杂文档读取及真实业务 eval 尚未执行。基线绑定本次绝对路径，移动后只作历史记录；新的动作必须建立自己的基线。
""")
    print(json.dumps({"ok": True, "demo_root": str(root), "raw_files": 3, "ingest_notes": 3,
                      "concept_notes": 2, "model_calls": 0, "company_eval": "未执行"}, ensure_ascii=False, indent=2))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="new directory below this kit's examples/")
    args = parser.parse_args()
    root = Path(args.output).resolve()
    examples = KIT / "examples"
    if examples not in root.parents:
        parser.error("output must be a new subdirectory of this kit's examples/")
    if root.exists():
        parser.error("output already exists; select a fresh directory (no files were overwritten)")
    build(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
