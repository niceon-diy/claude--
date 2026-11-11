# Box 设计书知识库：从这里开始

把 Box 资料保存在 `raw/`，由 Claude 提炼成 `wiki/Concepts/` 内可追溯的 Markdown 笔记，再合并、去重和标记矛盾。本套件先完成资料入库与知识整理；业务 eval 稳定后，再另做开发 Agent 接入。

**当前状态：套件已建立；公司资料尚未入库。** `examples/mini-project/` 全部是明确标注的虚构示例，不能作为公司规格使用。

## 公司电脑上的第一次使用

1. 将整个 `知识库/` 目录复制到公司允许保存设计资料的位置，例如 `D:\Work\Thema123\knowledge-base`。首次使用建议作为独立工作目录。若已有 `raw/`，沿用原目录及内容，不移动、不覆盖；让 Claude 按[公司接入提示词](公司接入提示词.md)适配路径。
2. 把选定的一套真实设计书从 Box 下载到 `raw/`。保留原文件名与字节，按 Thema／版本建子目录；记录 Box 链接、版本 ID、下载时间和用途。新版本另存，保留旧版本。下载在 `/ingest` 开始前完成。
3. 在该知识库目录打开 Claude Code，先发送[公司接入提示词](公司接入提示词.md)。确认本目录的 `CLAUDE.md` 已加载，`/ingest`、`/refine` 可被识别，再选择一个熟悉的小功能。
4. 输入 `/ingest`，附上本次文件路径和适用范围，例如下面的指令。Claude 读取原件，生成带来源的初始笔记并校验。
5. 检查初始笔记后输入 `/refine`。Claude 仅在现有笔记之间合并、去重、交叉链接和标记矛盾，不引入新来源。随后按[验收与 eval](验收与eval.md)核对真实样例。

```text
/ingest
范围：Thema123／文件输出功能／测试环境
文件：raw/Thema123/Box版本目录/实际设计书.xlsx
Box来源：填写实际Box链接；版本ID：填写实际版本
获取时间：填写实际下载时间；用途：current（当前版本基准）
先做这个功能，逐条保留工作表和单元格位置；资料未说明的内容标记待确认。
```

```text
/refine
范围：Thema123／文件输出功能／测试环境
只整理该范围已入库笔记，保留当前基准、正式要求与历史参考的区别。
```

不清楚版本时写“未确认”，不把文件夹名称或下载时间当成版本有效性的证明。Word、Excel、PDF 的具体定位与读取失败处理见 [CLAUDE.md](CLAUDE.md)。本阶段不安装解析框架；公司已有的读取工具可用时直接使用，无法读取的表格／页面保留缺口。

若接入提示词已完成首轮 ingest／refine，直接检查笔记并开展 eval；第4～5步的命令用于尚未处理或后续新增的批次。

## 目录与作用

```text
知识库/                       ← Claude Code 的工作目录
  CLAUDE.md                   ← 总规则，定义 /ingest 和 /refine
  .claude/skills/
    ingest/SKILL.md            ← /ingest 实际入口
    refine/SKILL.md            ← /refine 实际入口
  raw/                        ← 原件；两个动作都不得改写
  wiki/
    Concepts/                 ← I编号初始笔记、C编号概念笔记
    进度.md                   ← 不含公司内容的初始模板
    进度.local.md             ← 本次范围、结果与恢复入口（运行时生成）
    .checks/                  ← 每次动作的前置快照与检查报告（运行时生成）
  templates/                  ← 两种笔记模板，不是知识事实
  tools/                      ← Python 标准库校验与回归测试
  examples/mini-project/      ← 隔离的虚构样例与实际校验记录
```

所有路径均相对知识库根目录。不同 Thema／对象／环境用明确的 `scope` 区分；跨范围只建立显式关联，不自动合并。

`I001` 表示一次读取形成的初始笔记；`C001` 表示由既有笔记整理得到的概念。两者同放 `Concepts/`，通过 `kind` 区分。稳定编号不重用；合并后保留旧笔记并标记 `superseded`，防止链接断裂。

## 校验怎么运行

需要 Python 3.10 或更高版本，无第三方依赖。在知识库根目录执行：

```powershell
python tools/kb_check.py validate --root .
python -m unittest discover -s tools -p "test_*.py"
```

动作开始前建立唯一快照（把示意运行号换成实际时间／运行号）：

```powershell
python tools/kb_check.py snapshot --root . --output wiki/.checks/20261110-001-ingest-before.json
```

动作结束后检查本次变更：

```powershell
python tools/kb_check.py validate --root . --mode ingest --baseline wiki/.checks/20261110-001-ingest-before.json --report wiki/.checks/20261110-001-ingest-result.json
```

`/refine` 使用另一份动作前快照，并把 `--mode` 改成 `refine`。快照和报告都不可覆盖；修复后复用原基线，报告另存为 `result-02.json` 等新文件名。不通过重建基线掩盖异常。空目录校验通过只代表空壳结构合法。

工具检查来源路径／哈希、编号、链接、范围、派生关系和来源闭包；**不会判断设计内容是否正确、有没有遗漏，也不会阻止操作系统层面的写入。** 原件出现变动会被检查发现，但工具不会自动恢复原件。业务确认、版本有效性和事实核对仍按 eval 执行。

## 已有工程如何接入

优先使用独立目录完成第一套真实样例。必须放进现有工程时，让公司 Claude 按[接入提示词](公司接入提示词.md)合并规则和入口：保留工程现有 `CLAUDE.md`，先检查同名命令；不要直接覆盖整棵 `.claude/`。嵌套目录的发现行为受运行位置和版本影响，需实际验证，不能仅凭文件已复制就宣称命令可用。

套件的 `.gitignore` 默认排除公司原件、笔记和运行记录；部署前仍须核对公司仓库的跟踪状态，忽略规则不会取消已跟踪文件。这里没有创建自动上传、Box 同步、向量库或开发 Agent 调用。

## 接口依据

本次查阅的 [Claude Code 官方技能说明](https://code.claude.com/docs/en/skills)说明 `.claude/skills/<name>/SKILL.md` 可作为 `/name` 入口；本套件使用手动调用配置。`CLAUDE.md` 负责简短总规则，具体动作放在技能中。规则是模型上下文，不能当作强制权限控制，参见[官方记忆说明](https://code.claude.com/docs/en/memory)。公司端的实际版本、命令加载与执行尚待实测。
