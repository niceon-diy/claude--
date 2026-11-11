---
name: refine
description: 仅整理已有知识笔记，合并去重、交叉链接并标记矛盾；禁止引入新来源。
argument-hint: "[Thema／对象／环境] [可选笔记ID]"
disable-model-invocation: true
---

# /refine：合并、去重与矛盾整理

用户参数：$ARGUMENTS

先定位本技能所属知识库根目录：从本文件向上查找同时包含 `CLAUDE.md`、`raw/`、`wiki/`、`tools/kb_check.py` 的目录；未找到时停止写入并说明安装问题。遵循该根目录 `CLAUDE.md`。

1. 读取进度和指定 scope 已有笔记，列出本批父笔记 ID。没有初始笔记时报告“请先 ingest”，不自行读取新资料补足。
2. 开始前执行一次普通 validate；存在悬空来源、哈希变化或错误元数据时先报告，原件问题不得自行修复。为本批创建唯一运行号，执行 `python tools/kb_check.py snapshot --root <根目录> --output wiki/.checks/<运行号>-refine-before.json`。快照成功后才修改概念笔记。
3. 处理内容仅来自基线时已存在的笔记。可读取这些笔记引用的同版本、同定位原件来复核原有主张，但不能读取新文件／新章节来补知识；工具计算 raw 哈希属于完整性检查。发现证据不足时留缺口，通过后续独立 ingest 补源。
4. 同 scope 内合并可证实为同一概念的笔记；保留来源版本、角色和适用条件。相似名称不能单独成为合并依据。跨 scope 只能明确交叉链接，不能作为本概念的派生父项。
5. 按 `templates/concept-note.md` 生成／更新 C 笔记。`derived_from` 只列本次基线已有的直接父 ID；`sources` 是这些父笔记来源集合的子集，原样保留 path、sha256、locator、version、origin、retrieved_at、role，可重新编排 S 引用编号；正文相应同步。不能用同批新 C 笔记作父项，需要下一批再派生。
6. 逐条保留证据关系、条件、例外与未知项。矛盾必须并列双方原文含义、来源和受影响结论；已明确版本／环境差异时说明条件，优先级未知时状态 `conflict`，不得自行选一方正确。未解决的缺口不能在改写时消失。
7. I 笔记保持字节不变；任何笔记不删除。合并的旧 C 保留稳定 ID、标记 `superseded` 并链接新 C。新／变更笔记设 `needs-review`／`conflict` 等，不能新增或提升为 `verified`；既有 verified 内容变化后必须降级。人工核验是单独步骤。
8. 执行 `python tools/kb_check.py validate --root <根目录> --mode refine --baseline wiki/.checks/<运行号>-refine-before.json --report wiki/.checks/<运行号>-refine-result-01.json`。失败时修复本轮 C 笔记，复用原基线、报告改用 `result-02.json` 等新文件名；不改基线、I 笔记或 raw 来绕过失败。检查通过只证明结构和来源闭包，不能证明每句话都忠实于父笔记。
9. 在 `wiki/进度.local.md` 记录父 ID、输出 ID、合并／保留项目、冲突、未解问题和校验结果。按 eval 做业务核对；本轮不接开发 Agent。

本动作仅修改 C 笔记、wiki 运行记录与进度。不引入网页、会话记忆、其他工程或未入库设计作为事实来源；没有证据支持的回答明确标记“未收录／待确认”。
