# 公司用中日双语任务票／会社用日中二言語チケット

创建日／作成日：2026-11-02（日本时间／日本時間）  
版本／版：1.1  
业务状态／業務状態：未开始，尚未在公司工程执行／未着手、会社工程では実行前

**[总任务入口／総合タスク入口](https://github.com/niceon-diy/claude--/issues/22)**

## 使用方法／使い方

- 中文：将总任务Issue交给公司Claude。无法读取GitHub时，可复制 [全部任务原文](全部任务.md)；每份文件都含完整中文和日文，选择一种语言执行一次即可。资料索引先行，追加Source开发最优先，智能体调查后置。
- 日本語：総合Issueを会社Claudeへ渡します。GitHubを読めない場合は [全チケット本文](全部任务.md) をコピーできます。各ファイルは完全な中国語・日本語版を含むため、一方の言語を選び、一度だけ実行します。資料索引から始め、追加Source開発を最優先にし、エージェント調査は後続にします。

## 任务清单／チケット一覧

| ID | 优先级／優先区分 | 任务／タスク | 前置／依存 | GitHub |
|---|---|---|---|---|
| ADD-001 | 最高优先：追加开发／最優先：追加開発 | [建立公司工程、追加项目、资料及 Source 基准索引／会社工程・追加案件・資料・Source基準の索引を作る](个别任务/ADD-001.md) | 无／なし | [打开／開く](https://github.com/niceon-diy/claude--/issues/1) |
| ADD-002 | 最高优先：追加开发／最優先：追加開発 | [从参考 Release 一览反向核对追加对应一览中的 Source 漏项／参考Release一覧から追加対応一覧のSource漏れを逆照合する](个别任务/ADD-002.md) | ADD-001 | [打开／開く](https://github.com/niceon-diy/claude--/issues/3) |
| ADD-003 | 最高优先：追加开发／最優先：追加開発 | [调查目标 Source 的用途、调用、数据处理及影响范围／対象Sourceの用途・呼出し・データ処理・影響範囲を調査する](个别任务/ADD-003.md) | ADD-002 | [打开／開く](https://github.com/niceon-diy/claude--/issues/4) |
| ADD-004 | 最高优先：追加开发／最優先：追加開発 | [保存参考 テーマ 改修前后 Source 与 Diff，形成开发 Input／参考テーマの改修前後SourceとDiffを開発Inputとして保存する](个别任务/ADD-004.md) | ADD-002 | [打开／開く](https://github.com/niceon-diy/claude--/issues/5) |
| ADD-005 | 最高优先：追加开发／最優先：追加開発 | [逐项核对 Word 基本设计与原对应一览，并在右侧补充依据／Word基本設計の各要求を原対応一覧と照合し右側に根拠を補列する](个别任务/ADD-005.md) | ADD-001 | [打开／開く](https://github.com/niceon-diy/claude--/issues/6) |
| ADD-006 | 最高优先：追加开发／最優先：追加開発 | [建立 DB Object 与改修环境的变更及影响矩阵／DB Objectと改修環境ごとの変更・影響マトリクスを作る](个别任务/ADD-006.md) | ADD-001 | [打开／開く](https://github.com/niceon-diy/claude--/issues/7) |
| ADD-007 | 最高优先：追加开发／最優先：追加開発 | [将漏项、设计、用途、DB 和参考差分统合为正式开发 Input／漏れ・設計・用途・DB・参考差分を正式な開発Inputへ統合する](个别任务/ADD-007.md) | ADD-002, ADD-003, ADD-004, ADD-005, ADD-006 | [打开／開く](https://github.com/niceon-diy/claude--/issues/8) |
| ADD-008 | 最高优先：追加开发／最優先：追加開発 | [编制或改修本次追加的基本设计，明确业务规格／今回追加の基本設計を作成・改修し業務仕様を明確にする](个别任务/ADD-008.md) | ADD-007 | [打开／開く](https://github.com/niceon-diy/claude--/issues/9) |
| ADD-009 | 最高优先：追加开发／最優先：追加開発 | [编制详细设计及实现、测试对应表／詳細設計と実装・試験の対応表を作る](个别任务/ADD-009.md) | ADD-008, ADD-003, ADD-004, ADD-006 | [打开／開く](https://github.com/niceon-diy/claude--/issues/10) |
| ADD-010 | 最高优先：追加开发／最優先：追加開発 | [实现追加改修 Source，执行构建和静态检查／追加改修のSourceを実装しビルド・静的確認を行う](个别任务/ADD-010.md) | ADD-009, SUP-002 | [打开／開く](https://github.com/niceon-diy/claude--/issues/11) |
| ADD-011 | 最高优先：追加开发／最優先：追加開発 | [设计、生成并执行单体测试，修复失败／単体テストを設計・生成・実行し失敗を修正する](个别任务/ADD-011.md) | ADD-010 | [打开／開く](https://github.com/niceon-diy/claude--/issues/12) |
| ADD-012 | 最高优先：追加开发／最優先：追加開発 | [准备并执行连接测试，确认跨组件结果／接続テストを準備・実行しコンポーネント間結果を確認する](个别任务/ADD-012.md) | ADD-011, ADD-006 | [打开／開く](https://github.com/niceon-diy/claude--/issues/13) |
| ADD-013 | 最高优先：追加开发／最優先：追加開発 | [评审最终差分、要求满足度、测试证据和变更对象并交接／最終差分・要求充足・試験証拠・変更対象一覧をレビューし引き継ぐ](个别任务/ADD-013.md) | ADD-010, ADD-011, ADD-012 | [打开／開く](https://github.com/niceon-diy/claude--/issues/14) |
| SUP-001 | 按需：开发支援／必要時：開発支援 | [按最小必要范围整理公司 Claude 的规则、任务和交接记录／会社Claudeの既存ルールと作業・引継ぎ記録を最小限整える](个别任务/SUP-001.md) | 无／なし | [打开／開く](https://github.com/niceon-diy/claude--/issues/15) |
| SUP-002 | 按需：开发支援／必要時：開発支援 | [确保 Source 变更前后的版本、备份和变更记录／Source変更前後の版・バックアップ・変更記録を確保する](个别任务/SUP-002.md) | ADD-001 | [打开／開く](https://github.com/niceon-diy/claude--/issues/2) |
| SUP-003 | 按需：开发支援／必要時：開発支援 | [调查验证受影响批处理的重运行、中途异常及再执行条件／影響バッチのリラン・途中異常・再実行条件を調査検証する](个别任务/SUP-003.md) | ADD-003, ADD-006, ADD-009 | [打开／開く](https://github.com/niceon-diy/claude--/issues/16) |
| LATER-001 | 后续：追加开发之后／後続：追加開発後 | [结合 Manual 与代码调查 AI 智能体在五个工程阶段的工作机制／ManualとコードからAIエージェントの五工程の動きを調査する](个别任务/LATER-001.md) | 无／なし | [打开／開く](https://github.com/niceon-diy/claude--/issues/17) |
| LATER-002 | 后续：需要采用判断／後続：採用判断が必要 | [整理 COBOL 解析用 Agent、Skill、Command 构成方案／COBOL解析用Agent・Skill・Commandの構成案を整理する](个别任务/LATER-002.md) | LATER-001 | [打开／開く](https://github.com/niceon-diy/claude--/issues/18) |
| LATER-003 | 后续：追加开发之后／後続：追加開発後 | [将真实 Source 整理成小白可读的图解 HTML／実Sourceを初心者が読める図解付きHTMLにまとめる](个别任务/LATER-003.md) | ADD-003 | [打开／開く](https://github.com/niceon-diy/claude--/issues/19) |
| LATER-004 | 后续：追加开发之后／後続：追加開発後 | [只读评估既有调查基础、共通规范及证据质量／既存の調査基盤・共通規範・証拠品質を読み取り評価する](个别任务/LATER-004.md) | 无／なし | [打开／開く](https://github.com/niceon-diy/claude--/issues/20) |
| LATER-005 | 后续：可选环境整理／後続：任意の環境整備 | [仅在必要时整合并验证远程 Claude 个人规则／必要な場合だけリモートClaudeの個人ルールを統合・検証する](个别任务/LATER-005.md) | 无／なし | [打开／開く](https://github.com/niceon-diy/claude--/issues/21) |

## 来源与任务对应／資料とチケットの対応

| 来源／資料 | 文件／ファイル | 对应任务／対応チケット |
|---|---|---|
| S01 AI 智能体与 Manual 调查／AIエージェントとManualの調査 | [通用提示词/AI智能体与Manual调查/P002_AI驱动开发工程智能体与Manual调查提示词.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E9%80%9A%E7%94%A8%E6%8F%90%E7%A4%BA%E8%AF%8D/AI%E6%99%BA%E8%83%BD%E4%BD%93%E4%B8%8EManual%E8%B0%83%E6%9F%A5/P002_AI%E9%A9%B1%E5%8A%A8%E5%BC%80%E5%8F%91%E5%B7%A5%E7%A8%8B%E6%99%BA%E8%83%BD%E4%BD%93%E4%B8%8EManual%E8%B0%83%E6%9F%A5%E6%8F%90%E7%A4%BA%E8%AF%8D.md) | LATER-001 |
| S02 COBOL Agent／Skill 构成咨询／COBOL Agent・Skill構成相談 | [通用提示词/COBOL分析/COBOL解析要求与候选方案.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E9%80%9A%E7%94%A8%E6%8F%90%E7%A4%BA%E8%AF%8D/COBOL%E5%88%86%E6%9E%90/COBOL%E8%A7%A3%E6%9E%90%E8%A6%81%E6%B1%82%E4%B8%8E%E5%80%99%E9%80%89%E6%96%B9%E6%A1%88.md#requirements) | LATER-002 |
| S03 COBOL 解析构成讨论记录／COBOL解析の構成検討記録 | [通用提示词/COBOL分析/COBOL解析要求与候选方案.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E9%80%9A%E7%94%A8%E6%8F%90%E7%A4%BA%E8%AF%8D/COBOL%E5%88%86%E6%9E%90/COBOL%E8%A7%A3%E6%9E%90%E8%A6%81%E6%B1%82%E4%B8%8E%E5%80%99%E9%80%89%E6%96%B9%E6%A1%88.md#candidate-architecture) | LATER-002 |
| S04 既有配置与调查基础评估／既存設定と調査基盤の評価 | [通用提示词/调查与证据核对.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E9%80%9A%E7%94%A8%E6%8F%90%E7%A4%BA%E8%AF%8D/%E8%B0%83%E6%9F%A5%E4%B8%8E%E8%AF%81%E6%8D%AE%E6%A0%B8%E5%AF%B9.md#system-review) | LATER-004 |
| S05 首次接入／初回導入 | [开发环境/首次接入提示词.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83/%E9%A6%96%E6%AC%A1%E6%8E%A5%E5%85%A5%E6%8F%90%E7%A4%BA%E8%AF%8D.md) | ADD-001, SUP-001 |
| S06 项目共通规则／プロジェクト共通ルール | [开发环境/模板/CLAUDE.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83/%E6%A8%A1%E6%9D%BF/CLAUDE.md) | SUP-001 |
| S07 当前任务与交接／現在の作業と引継ぎ | [开发环境/模板/当前任务.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83/%E6%A8%A1%E6%9D%BF/%E5%BD%93%E5%89%8D%E4%BB%BB%E5%8A%A1.md) | ADD-001, SUP-001 |
| S08 程序与设计书对应调查／プログラムと設計書の対応調査 | [通用提示词/程序与设计书对应调查/P001_程序与设计书对应调查及报告生成提示词.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E9%80%9A%E7%94%A8%E6%8F%90%E7%A4%BA%E8%AF%8D/%E7%A8%8B%E5%BA%8F%E4%B8%8E%E8%AE%BE%E8%AE%A1%E4%B9%A6%E5%AF%B9%E5%BA%94%E8%B0%83%E6%9F%A5/P001_%E7%A8%8B%E5%BA%8F%E4%B8%8E%E8%AE%BE%E8%AE%A1%E4%B9%A6%E5%AF%B9%E5%BA%94%E8%B0%83%E6%9F%A5%E5%8F%8A%E6%8A%A5%E5%91%8A%E7%94%9F%E6%88%90%E6%8F%90%E7%A4%BA%E8%AF%8D.md) | ADD-003, ADD-005, ADD-006, ADD-007, ADD-008, ADD-009, ADD-011, ADD-012, ADD-013, LATER-003 |
| S09 14 项目追加对应一览及参考 Source 差分／14案件の追加対応一覧と参考Source差分 | [中文版](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E8%BF%BD%E5%8A%A0%E5%BC%80%E5%8F%91/14%E4%B8%AA%E9%A1%B9%E7%9B%AE%E6%A0%B8%E5%AF%B9/%E4%B8%AD%E6%96%87/P002_14%E4%B8%AA%E9%A1%B9%E7%9B%AE%E8%BF%BD%E5%8A%A0%E5%AF%B9%E5%BA%94%E4%B8%80%E8%A7%88%E6%A0%B8%E5%AF%B9%E4%B8%8E%E5%8F%82%E8%80%83Source%E5%B7%AE%E5%88%86%E6%95%B4%E7%90%86.md) · [日本語版](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E8%BF%BD%E5%8A%A0%E5%BC%80%E5%8F%91/14%E4%B8%AA%E9%A1%B9%E7%9B%AE%E6%A0%B8%E5%AF%B9/%E6%97%A5%E6%9C%AC%E8%AA%9E/P002_14%E6%A1%88%E4%BB%B6%E3%81%AE%E8%BF%BD%E5%8A%A0%E5%AF%BE%E5%BF%9C%E4%B8%80%E8%A6%A7%E7%85%A7%E5%90%88%E3%81%A8%E5%8F%82%E8%80%83Source%E5%B7%AE%E5%88%86%E6%95%B4%E7%90%86.md) | ADD-001, ADD-002, ADD-004, ADD-006, ADD-007, ADD-010 |
| S10 全工程共通调查规范／全工程共通調査規範 | [通用提示词/调查与证据核对.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E9%80%9A%E7%94%A8%E6%8F%90%E7%A4%BA%E8%AF%8D/%E8%B0%83%E6%9F%A5%E4%B8%8E%E8%AF%81%E6%8D%AE%E6%A0%B8%E5%AF%B9.md#scope-and-evidence) | ADD-002, ADD-005, ADD-011, ADD-012, LATER-001, LATER-004 |
| S11 基本设计书覆盖核对／基本設計書のカバレッジ確認 | [追加开发/基本设计书覆盖核对.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E8%BF%BD%E5%8A%A0%E5%BC%80%E5%8F%91/%E5%9F%BA%E6%9C%AC%E8%AE%BE%E8%AE%A1%E4%B9%A6%E8%A6%86%E7%9B%96%E6%A0%B8%E5%AF%B9.md) | ADD-005, ADD-007, ADD-008 |
| S12 程序清单比对／プログラム一覧の突合せ | [追加开发/程序清单比对/程序清单比对任务.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E8%BF%BD%E5%8A%A0%E5%BC%80%E5%8F%91/%E7%A8%8B%E5%BA%8F%E6%B8%85%E5%8D%95%E6%AF%94%E5%AF%B9/%E7%A8%8B%E5%BA%8F%E6%B8%85%E5%8D%95%E6%AF%94%E5%AF%B9%E4%BB%BB%E5%8A%A1.md) | ADD-002, ADD-013 |
| S13 COBOL SECTION 索引／COBOL SECTIONマップ | [通用提示词/COBOL分析/COBOL解析要求与候选方案.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E9%80%9A%E7%94%A8%E6%8F%90%E7%A4%BA%E8%AF%8D/COBOL%E5%88%86%E6%9E%90/COBOL%E8%A7%A3%E6%9E%90%E8%A6%81%E6%B1%82%E4%B8%8E%E5%80%99%E9%80%89%E6%96%B9%E6%A1%88.md#section-map) | ADD-003, LATER-002 |
| S14 遗留系统静态解析／レガシーシステム静的解析 | [通用提示词/COBOL分析/单程序静态调查清单.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E9%80%9A%E7%94%A8%E6%8F%90%E7%A4%BA%E8%AF%8D/COBOL%E5%88%86%E6%9E%90/%E5%8D%95%E7%A8%8B%E5%BA%8F%E9%9D%99%E6%80%81%E8%B0%83%E6%9F%A5%E6%B8%85%E5%8D%95.md#static-checklist) | ADD-003, SUP-003 |
| S15 影响调查及小白用 HTML 解说／影響調査と初心者向けHTML解説 | [通用提示词/影响调查与程序解说.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E9%80%9A%E7%94%A8%E6%8F%90%E7%A4%BA%E8%AF%8D/%E5%BD%B1%E5%93%8D%E8%B0%83%E6%9F%A5%E4%B8%8E%E7%A8%8B%E5%BA%8F%E8%A7%A3%E8%AF%B4.md#impact-and-explanation) | ADD-003, ADD-008, ADD-009, LATER-003 |
| S16 重运行调查／リラン調査 | [追加开发/重运行调查清单.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E8%BF%BD%E5%8A%A0%E5%BC%80%E5%8F%91/%E9%87%8D%E8%BF%90%E8%A1%8C%E8%B0%83%E6%9F%A5%E6%B8%85%E5%8D%95.md#rerun-checklist) | SUP-003 |
| S17 分析依据检查／分析根拠の点検 | [通用提示词/调查与证据核对.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E9%80%9A%E7%94%A8%E6%8F%90%E7%A4%BA%E8%AF%8D/%E8%B0%83%E6%9F%A5%E4%B8%8E%E8%AF%81%E6%8D%AE%E6%A0%B8%E5%AF%B9.md#evidence-review) | ADD-011, ADD-012, ADD-013, SUP-003, LATER-001, LATER-004 |
| S18 变更版本管理／変更の版管理 | [开发环境/规则部署与验收.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83/%E8%A7%84%E5%88%99%E9%83%A8%E7%BD%B2%E4%B8%8E%E9%AA%8C%E6%94%B6.md#version-backup) | ADD-004, ADD-010, SUP-002 |
| S19 任务要求模板／作業依頼テンプレート | [开发环境/模板/当前任务.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83/%E6%A8%A1%E6%9D%BF/%E5%BD%93%E5%89%8D%E4%BB%BB%E5%8A%A1.md#task-request) | ADD-001, SUP-001 |
| S20 远程个人规则部署／リモート個人ルール導入 | [开发环境/规则部署与验收.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83/%E8%A7%84%E5%88%99%E9%83%A8%E7%BD%B2%E4%B8%8E%E9%AA%8C%E6%94%B6.md#deployment) | LATER-005 |
| S21 个人工作与表达规则／個人の作業・説明ルール | [开发环境/模板/CLAUDE.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83/%E6%A8%A1%E6%9D%BF/CLAUDE.md#working-rules) | SUP-001, LATER-005 |
| S22 解析与评审工作备忘／解析とレビューの作業メモ | [通用提示词/COBOL分析/COBOL解析要求与候选方案.md](https://github.com/niceon-diy/claude--/blob/codex/claude-environment/%E9%80%9A%E7%94%A8%E6%8F%90%E7%A4%BA%E8%AF%8D/COBOL%E5%88%86%E6%9E%90/COBOL%E8%A7%A3%E6%9E%90%E8%A6%81%E6%B1%82%E4%B8%8E%E5%80%99%E9%80%89%E6%96%B9%E6%A1%88.md#workflow-review) | ADD-003, ADD-009, ADD-010, ADD-011, ADD-013, LATER-002 |

## 维护与实际状态／保守と実際の状態

- 中文：`维护/任务数据.json`是任务事实、编号、依赖、状态和双语内容的唯一维护来源。更新后在任务票目录运行`python 维护/生成任务票.py`，生成个别任务、总任务、README和合并原文；脚本只生成本地文件，不会上传或更新GitHub。共通规则、当前任务、任务要求模板和证据原则已纳入各任务。历史来源已合并为主题文档，章节链接可直接定位；原件通过历史归档的来源索引追溯，不重复建票。创建文件或Issue不代表公司业务已经调查、开发或测试完成。
- 日本語：`维护/任务数据.json`がタスク事実、ID、依存、状態、二言語内容の唯一の保守元です。更新後にタスク票ディレクトリで`python 维护/生成任务票.py`を実行すると、個別チケット、総合、README、統合本文を生成します。スクリプトはローカル生成のみで、GitHubへ送信・更新しません。共通ルール、現在タスク、依頼テンプレート、証拠原則を各チケットへ反映しています。旧資料はテーマ別文書へ統合し、節リンクで参照できます。原文は履歴索引から追跡し、重複起票しません。ファイルやIssue作成は、会社の調査・開発・試験完了を意味しません。
