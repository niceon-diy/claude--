# 派生知识入口

正式笔记存放在 [Concepts/](Concepts/)，模板在 [../templates/](../templates/)。当前正式笔记为空，公司原件尚未导入。

- I 编号：`/ingest` 从 raw 读取的初始笔记，保留具体位置与未读范围。
- C 编号：`/refine` 从已有笔记整理的概念，保留父 ID 和来源。
- `draft`／`needs-review`：尚待业务核验；`conflict`：存在未解决冲突。
- `verified`：另有审阅人、日期和方法的业务核验记录；只对记录的范围与版本成立。
- `superseded`：保留供追溯，正文指向替代笔记。

任何来源哈希变化都需要重新检查受影响笔记。普通校验通过不代表结论已核验。

在真实样例 eval 稳定前，本目录不接入开发 Agent。示意工程位于 [../examples/mini-project/](../examples/mini-project/)，与这里的知识事实隔离。
