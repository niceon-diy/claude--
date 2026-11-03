# 旧仓库完整迁移记录／旧リポジトリ移行記録

日期／日付：2026-11-03

目录整理说明／ディレクトリ整理：本记录及 JSON 中的原路径表示迁移当天的位置；当前目录见[整理说明与路径对应表](../../整理记录/2026-11-03/README.md)。記録内の旧パスは当時の位置で、現在の場所は対応表を参照してください。

## 中文

主仓库是 [niceon-diy/claude--](https://github.com/niceon-diy/claude--)；日常使用默认分支 `codex/claude-environment`。
旧仓库为 `niceon-diy/Claude-AI------`，本次按用户要求将剩余内容与历史保存在主仓库，再删除旧仓库。实际删除结果见 [删除状态.json](删除状态.json)。

### 文件与 Git 历史

- 旧仓库默认分支 `main` 的最后提交为 `67652ff0530599f55dc0a70bf3aa9ae49e8582dd`，共 2 次提交、6 个文件，没有其他分支或标签。
- 4 份个人规则已原样存在于主仓库的 `参考资料/个人规则/`，Git blob SHA 逐份相同，不重复覆盖。
- 《项目追加注意事项》和 14 项目 P002 提示词在主仓库已有更新后的完整中日双语版，继续使用现用文件。本次另存旧仓库最后的中文原文，避免用旧版覆盖更新版。
- [旧版原文入口](../../旧仓库原文/Claude-AI------/README.md)保留上述 2 份原始文件；[文件映射.json](文件映射.json)记录全部 6 份文件的原路径、SHA 和主仓库位置。
- 完整旧 Git 历史保存在主仓库的 [codex/archive-legacy-private-main 分支](https://github.com/niceon-diy/claude--/tree/codex/archive-legacy-private-main)，其分支头与旧库最后提交相同，包含旧库全部提交和原始目录。
- 本机另外保存了 Git bundle 和全部文件 ZIP；位置为 `C:/Users/niceo/Documents/ChatGPT/Claude AI驱动系统开发/仓库迁移备份/2026-11-03_Claude-AI------/`。Git bundle 已通过完整历史校验，删除旧远端不影响本机备份。

### Issue 与其他资产

- 已逐项核对旧库 22 个 Issue 与主库 22 个 Issue，编号映射 22/22；主库保留完整中日双语任务正文、50 条已迁移的任务依赖链接和全部来源引用。
- 旧 Issue 因迁移而关闭，主仓库 Issue 保持打开；不能把旧库的关闭状态误认为公司业务任务已经完成。
- [Issue迁移映射.json](Issue迁移映射.json)：旧／新编号与 URL。
- [迁移前Issue原文.json](迁移前Issue原文.json)：原始标题、正文及来源快照。
- [删除前Issue完整快照.json](删除前Issue完整快照.json)：删除前重新读取的 GitHub Issue 数据，包含迁移提示和当时状态。
- 此前采用“重建新 Issue 后关闭原 Issue”，不是 GitHub Transfer。**删除后旧仓库 URL 不会自动重定向**；请使用映射中的主仓库链接。历史快照中的旧 URL 保持原文，用于追溯。
- 两库没有 PR；旧库没有 Issue 评论、附件、已使用标签、负责人、里程碑、Git 标签、Release、Release 附件、关联 Project 或 Actions 运行记录；Wiki、Discussions 和 Pages 未启用。旧库的 10 个预定义 GitHub 标签名称和说明与主仓库一致，无需另行创建。
- [仓库资产清单.json](仓库资产清单.json)保存删除前的仓库身份、分支、文件树、文件映射和核对数量。现用历史来源链接已改为主仓库中保存的提交。

## 日本語

主リポジトリは [niceon-diy/claude--](https://github.com/niceon-diy/claude--)、通常利用する既定ブランチは `codex/claude-environment` です。
旧 `niceon-diy/Claude-AI------` の未保存資料と履歴を移行してから、ユーザーの依頼に従い旧リポジトリを削除します。実際の削除結果は [删除状态.json](删除状态.json) に記録します。

- 旧 main の最終コミットは `67652ff`、全 2 コミット・6 ファイルです。個人ルール 4 件は既に主リポジトリと同一 SHA、残る 2 件は現用の中日二言語版を保持し、旧原文を別途保存します。
- 全 Git 履歴は主リポジトリの `codex/archive-legacy-private-main` に保管し、元の最終コミットと同一であることを確認します。ローカルにも完全履歴の bundle と ZIP を保存しています。
- Issue は 22/22 件を照合済みです。旧 Issue の閉鎖は移行処理を表し、業務の完了を表しません。現用の主リポジトリ Issue は open のまま維持します。
- 原文、移行先対応表、削除前 API スナップショットをこのディレクトリへ保存します。旧 URL は削除後に自動転送されないため、対応表の新 URL を使ってください。
- PR、コメント、添付、使用中ラベル・担当者・マイルストーン、タグ、Release、関連 Project、Actions 実行の追加移行対象はありません。Wiki・Discussions・Pages は無効です。
