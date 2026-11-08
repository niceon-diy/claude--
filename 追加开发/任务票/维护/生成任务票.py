"""中日双语任务票生成器／日中二言語チケット生成器。事实仅维护于JSON／事実はJSONのみで管理。"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote

MAINTENANCE_ROOT = Path(__file__).resolve().parent
ROOT = MAINTENANCE_ROOT.parent
REPO_ROOT = ROOT.parent.parent
DATA_FILE = MAINTENANCE_ROOT / '任务数据.json'

COMMON = {
'zh': """### 公司 Claude 的共同执行条件

本任务须在公司内部实际可访问的业务工程中执行。本仓库提供的是任务要求和模板，不代表公司调查、实现或测试已经完成。

- 先读取实际生效的工程规则、当前任务和已有成果，不要求用户重复提供已经能查到的信息。历史资料中的权限或特定环境，不自动作为当前授权。
- 必要前提齐全的通常工作连续执行。只有影响结果的重要业务判断、权限或访问缺失才具体询问，同时继续不依赖缺失答案的工作。
- 按项目判断前提。不能因目标14个项目未全部齐备，就阻止准备好的项目进入设计和开发；也不能虚构项目补足数量。
- 区分正式要求、本次对应一览、现行设计和历史参考。参考Source Diff不能替代本次正式规格。
- 关键结论附实际文件、版本、行／章／工作表等位置；区分事实、推测、未读、无法访问、待确认和不适用，不适用须有理由。
- 优先沿用公司工程既有成果目录；没有约定时，使用 \u0060調査結果/追加開発/<实际运行时间>/<已确认项目ID>/<任务票ID>/\u0060。项目ID未确定前不创建虚假对象。
- 公司资料正文、真实业务数据及认证信息不转载到GitHub。必要成果保存在公司内部，Issue只记录不含机密的进度和定位方式。
- 实际完成条件满足后才可结束Issue。复制、脚本成功、用例生成、Source保存不能单独证明调查或测试整体完成。

成果与交接记录必须写明实际项目／对象、输入及版本、实际操作、成果完整路径、真实验证结果、未完成／未确认事项和下一步。最后用适合拍照反馈的约10行报告实际结果。
""",
'ja': """### 会社Claudeへの共通実行条件

この作業は、会社内で実際にアクセスできる業務工程に対して実行する。本リポジトリは依頼とテンプレートを提供するもので、会社の調査・実装・試験が完了した証拠ではない。

- まず実工程で有効なルール、現在タスク、既存成果を読む。すでに調べられる情報をユーザーへ再入力させない。歴史資料にある権限や特定環境を現在の承認とみなさない。
- 必要な前提が揃う通常作業は連続実行する。結果を左右する重要な業務判断・権限・アクセス不足だけを具体的に確認し、それに依存しない作業は続ける。
- 案件単位で前提を判定する。目標14案件がすべて揃うまで、準備済み案件の設計・開発を止めない。数を合わせるための架空案件を作らない。
- 正式要求、今回の対応一覧、現行設計、歴史参考を区別する。参考Source Diffを今回の正式仕様の代わりにしない。
- 重要結論に実ファイル・版・行／章／シート等の位置を付ける。事実、推測、未読、アクセス不能、未確認、不適用を区別し、不適用には理由を残す。
- 会社工程の既存成果ディレクトリを優先する。決まりがなければ \u0060調査結果/追加開発/<実際の実行日時>/<確認済み案件ID>/<チケットID>/\u0060 を使う。案件IDが不明な間は架空の対象を作らない。
- 会社資料の本文、実業務データ、認証情報をGitHubへ転載しない。必要な成果は会社内に保存し、Issueには機密を含まない進捗と定位方法だけを残す。
- 実際の完了条件を満たしてからIssueを終了する。コピー、スクリプト成功、用例生成、Source保存だけで調査や試験全体の完了としない。

成果と引継ぎには、実案件／対象、入力と版、実施内容、成果の完全なパス、実際の検証結果、未完了／未確認事項、次の一手を残す。最後は写真で共有しやすい約10行で実結果を報告する。
"""}

LABELS = {
'zh': dict(language='中文（可单独复制执行）',priority='优先级',state='业务状态',goal='目的',condition='执行条件',depends='前置任务',inputs='输入',steps='实际执行步骤',outputs='成果物',criteria='完成条件',boundary='修改范围',failure='缺失或失败时',refs='参考来源及资料处理',none='无；可从已有资料直接确认。',dependency_note='按每个实际目标项目判断必要成果是否齐全，或是否有不适用依据；不是要求等待前置任务的全部项目一起完成。',failure_text='保存缺失项、实际已检查范围、受影响结论／对象、确认人或资料及最短补充方式，并继续可独立完成的工作。重要规格矛盾不能擅自消解；没有执行、没有生成或没有测试的内容不得报告完成。',refs_note='即使公司环境无法读取参考源文件，本任务正文也已包含步骤、成果和完成条件。参考资料中的方案不等于已部署配置。',source_path='资料路径'),
'ja': dict(language='日本語（単独でコピーして実行可能）',priority='優先区分',state='業務状態',goal='目的',condition='実行条件',depends='前提チケット',inputs='入力',steps='実際に行う手順',outputs='成果物',criteria='完了条件',boundary='変更範囲',failure='不足・失敗時',refs='参考元と資料の扱い',none='なし。既存資料から直接確認できる。',dependency_note='各実案件について必要な成果が揃うか、不適用の根拠があるかを判定する。前提チケットの全案件が一斉に完了するまで待つ意味ではない。',failure_text='不足項、実際に調べた範囲、影響する結論／対象、確認先・資料と最短の補充方法を保存し、独立して進められる作業は続ける。重要な仕様矛盾を勝手に解消せず、未実行・未生成・未試験の内容を完了と報告しない。',refs_note='会社環境で参考ファイルを読めなくても、本チケット本文には手順・成果・完了条件を含めている。参考資料の提案を導入済み設定とは扱わない。',source_path='資料パス')}

MASTER_TEXT = {
'zh': """### 交给公司 Claude 的执行要求

当前最高优先级是今后追加改修的Source开发。AI智能体工作机制调查和构成优化安排在后续，不作为Source开发的前提。

请阅读本总任务和相关个别任务，在实际公司工程中执行。先通过ADD-001确认既有输入和真实目标项目，再按项目逐一执行前提齐备的最高优先任务。不能只返回计划或表示理解，应依据各任务的步骤、成果物、完成条件保存实际结果。

分别记录资料存在、规格确定、实现完成、测试执行和测试通过。当前创建任务票时，尚未核实公司的真实项目、Source、设计和测试环境。目标14个项目来自既有要求，不代表本仓库已确认其实际存在或资料齐全。

首次执行时，先从已有资料查实际工程根、当前规则与任务记录、Source基准、有效设计、追加对应一览、参考Thema和成果保存位置。已有资料可回答的内容不要求用户重复输入；只具体询问确实无法找到的重要信息。

### 最优先的追加开发顺序

ADD-001 → ADD-002 → ADD-003／ADD-004。索引齐备后ADD-005／ADD-006可以并行。将结果在ADD-007统一为开发Input，再按ADD-008 基本设计 → ADD-009 详细设计 → ADD-010 Source实现 → ADD-011 单体测试 → ADD-012 连接测试 → ADD-013 最终评审与交接推进。

规格已明确部分的测试用例和连接环境可提前准备，但执行证据须对应实际改修版本。Source编辑前确认SUP-002的版本保存；SUP-001只在现有规则不足时适用，SUP-003只在涉及受影响批处理时适用。后续任务不能自动提升为最优先。

按项目独立推进。某项目资料不足时，记录其阻碍的具体对象；不能要求14个项目资料全部齐备，才允许准备好的项目开始开发。
""",
'ja': """### 会社Claudeへ渡す実行依頼

最優先は今後の追加改修分のSource開発。AIエージェントの仕組み調査と構成見直しは後続とし、Source開発の前提条件にしない。

この総合タスクと関係する個別チケットを読み、実際の会社工程で実行する。まずADD-001で既存入力と実案件を確認し、案件ごとに前提が揃う最優先タスクを進める。計画や了承だけで終わらず、各チケットの手順・成果物・完了条件に沿って実結果を残す。

資料の存在、仕様の確定、実装の完了、試験の実行と通過を別々に記録する。チケット作成時点では、会社の実案件、Source、設計、試験環境をまだ確認していない。目標14案件は既存要求に由来し、本リポジトリで実在や資料充足を確認済みという意味ではない。

初回は、実工程の根、現在ルールとタスク記録、Source基準、有効設計、追加対応一覧、参考Thema、成果保存場所を既存資料から探す。資料から分かる情報をユーザーへ再入力させず、本当に見つからない重要項目だけを具体的に確認する。

### 最優先の追加開発順序

ADD-001 → ADD-002 → ADD-003／ADD-004。索引ができ次第ADD-005／ADD-006は並行可能。結果をADD-007で開発Inputへ統合し、ADD-008 基本設計 → ADD-009 詳細設計 → ADD-010 Source実装 → ADD-011 単体テスト → ADD-012 接続テスト → ADD-013 最終レビュー・引継ぎへ進む。

仕様が明らかな範囲の試験用例・接続環境は前倒しで準備できる。ただし実行証拠は実際の改修版に対応させる。Source編集前にSUP-002の版保存を確認する。SUP-001は既存ルールが不足する場合のみ、SUP-003は影響バッチがある場合のみ適用する。後続タスクを自動的に最優先へ繰り上げない。

案件単位で独立して進める。ある案件の資料不足は、その案件の具体的な対象を阻むものとして記録する。14案件の資料がすべて揃うことを、準備済み案件の開発開始条件にしない。
"""}

END_TEXT = {
'zh': """### 完成的判断

- 总任务是执行入口。任务票已建立，不代表公司业务作业已经完成。
- 追加改修主任务按ADD-001～ADD-013的逐项目结果和剩余事项判断；可选／后续任务不必强行标为完成。
- 本番Release、公司DB本番变更和整个AI基础重建，不在本次任务的自动执行范围内。
""",
'ja': """### 完了の判断

- 総合タスクは実行の入口。チケット作成と会社の業務作業完了は別である。
- 追加改修の主タスクはADD-001～ADD-013の案件別結果と残件で判定する。任意・後続タスクを無理に完了にしない。
- 本番Release、会社DBの本番変更、AI基盤全体の再構築は、この依頼の自動実行範囲に含めない。
"""}

def value(row,key,lang):
    return row[key+'_zh'] if lang=='zh' else row[key]

def validate(pack):
    tickets=pack['tickets'];index={t['id']:t for t in tickets};sources={s['id']:s for s in pack['sources']}
    assert len(tickets)==len(index)==21,'任务票ID或数量错误／チケットID・数が不正'
    assert len(sources)==22,'来源数量错误／資料数が不正'
    repo=pack['repository'];urls=[]
    for t in tickets:
        assert all(dep in index for dep in t['depends']),(t['id'],'不明依赖／不明依存')
        assert all(ref in sources for ref in t['refs']),(t['id'],'不明来源／不明資料')
        for key in ['title','group','goal','inputs','steps','outputs','criteria','condition','boundary','status']:
            assert key in t and key+'_zh' in t,(t['id'],key,'缺翻译／翻訳不足')
            if isinstance(t[key],list):
                assert len(t[key])==len(t[key+'_zh']) and t[key],(t['id'],key,'两语条数不符／項目数不一致')
        assert t['issue_number']>0 and t['issue_url']==f"https://github.com/{repo}/issues/{t['issue_number']}"
        urls.append(t['issue_url']);assert not any(k.startswith('previous_') for k in t)
    assert set(sources)=={s for t in tickets for s in t['refs']},'来源未全部关联／未対応資料'
    assert pack['master_issue_number']>0
    assert pack['master_issue_url']==f"https://github.com/{repo}/issues/{pack['master_issue_number']}"
    urls.append(pack['master_issue_url']);assert len(urls)==len(set(urls))==22,'URL重复／URL重複'
    assert not any(k.startswith('previous_') for k in pack)
    for s in sources.values():
        assert s.get('title') and s.get('title_zh')
        source_file=REPO_ROOT/s['path']
        assert source_file.is_file(),('不存在的来源路径／存在しない資料',s['path'])
        if s.get('anchor'):
            assert re.fullmatch(r'[a-z][a-z0-9-]*',s['anchor']),('不合法的来源锚点／不正な資料アンカー',s['anchor'])
            source_text=source_file.read_text(encoding='utf-8')
            assert f'id="{s["anchor"]}"' in source_text,('来源章节不存在／資料の節が存在しない',s['path'],s['anchor'])
    visiting=set();visited=set()
    def walk(id):
        assert id not in visiting,('依赖环／依存循環',id)
        if id in visited:return
        visiting.add(id)
        for dep in index[id]['depends']:walk(dep)
        visiting.remove(id);visited.add(id)
    for id in index:walk(id)

def source_url(pack,source):
    branch=pack.get('default_branch','codex/claude-environment')
    url=f"https://github.com/{pack['repository']}/blob/{quote(branch,safe='/')}/{quote(source['path'],safe='/')}"
    return url+'#'+quote(source['anchor'],safe='') if source.get('anchor') else url

def issue_link(t,lang):
    return f"[{t['id']}｜{value(t,'title',lang)}]({t['issue_url']})"

def render_language(t,pack,lang,anchor):
    labels=LABELS[lang];index={x['id']:x for x in pack['tickets']};sources={x['id']:x for x in pack['sources']}
    text=f'<a id="{anchor}"></a>\n\n## {labels["language"]}\n\n'
    text+=f"### {t['id']}｜{value(t,'title',lang)}\n\n"
    text+=f"{labels['priority']}：{value(t,'group',lang)}  \n{labels['state']}：{value(t,'status',lang)}  \nGitHub：{t['issue_url']}\n\n"
    text+=f"### {labels['goal']}\n\n{value(t,'goal',lang)}\n\n"
    condition=value(t,'condition',lang)
    if condition:text+=f"### {labels['condition']}\n\n{condition}\n\n"
    text+=f"### {labels['depends']}\n\n"
    text+='\n'.join('- '+issue_link(index[id],lang) for id in t['depends']) if t['depends'] else '- '+labels['none']
    text+='\n\n'+labels['dependency_note']+'\n\n'
    for key in ['inputs','steps','outputs','criteria']:
        text+=f"### {labels[key]}\n\n"
        if key=='steps':text+='\n'.join(f'{i}. {item}' for i,item in enumerate(value(t,key,lang),1))
        else:text+='\n'.join(('- [ ] ' if key=='criteria' else '- ')+item for item in value(t,key,lang))
        text+='\n\n'
    boundary=value(t,'boundary',lang)
    if boundary:text+=f"### {labels['boundary']}\n\n{boundary}\n\n"
    text+=f"### {labels['failure']}\n\n{labels['failure_text']}\n\n"+COMMON[lang]+'\n'
    text+=f"### {labels['refs']}\n\n"
    for id in t['refs']:
        s=sources[id];location=s['path']+('#'+s['anchor'] if s.get('anchor') else '')
        text+=f"- {id}：[{value(s,'title',lang)}]({source_url(pack,s)})  \n  {labels['source_path']}：\u0060{location}\u0060\n"
    return text+'\n'+labels['refs_note']+'\n'

def render_ticket(t,pack,prefix=''):
    za=prefix+'zh-cn';ja=prefix+'ja'
    text=f"# {t['id']}｜{t['title_zh']}／{t['title']}\n\n[中文](#{za}) · [日本語](#{ja})\n\n"
    text+='中文与日文是同一个任务的完整等价版本，选择一种语言执行一次即可。  \n中国語と日本語は同じ作業の完全な二言語版です。一方の言語を選び、一度だけ実行してください。\n\n'
    return text+render_language(t,pack,'zh',za)+'\n---\n\n'+render_language(t,pack,'ja',ja)

def render_master(pack,prefix=''):
    za=prefix+'zh-cn';ja=prefix+'ja'
    text=f"# 总任务：追加改修优先／総合タスク：追加改修を優先\n\n[中文](#{za}) · [日本語](#{ja})  \nGitHub：{pack['master_issue_url']}\n\n"
    text+='以下两种语言描述同一组任务，只需选择一种语言。  \n以下の二言語は同じタスク群を示します。一方の言語だけを選んでください。\n\n'
    for lang,anchor in [('zh',za),('ja',ja)]:
        text+=f'<a id="{anchor}"></a>\n\n## {LABELS[lang]["language"]}\n\n'+MASTER_TEXT[lang]+'\n'
        text+=('### 全部任务清单\n\n' if lang=='zh' else '### 全チケット一覧\n\n')
        for group in dict.fromkeys(value(t,'group',lang) for t in pack['tickets']):
            text+=f'#### {group}\n\n'
            for t in pack['tickets']:
                if value(t,'group',lang)==group:text+='- [ ] '+issue_link(t,lang)+' — '+value(t,'goal',lang)+'\n'
            text+='\n'
        text+=COMMON[lang]+'\n'+END_TEXT[lang]+'\n'
        if lang=='zh':text+='---\n\n'
    return text

def render_readme(pack):
    text='# 公司用中日双语任务票／会社用日中二言語チケット\n\n'
    text+=f"创建日／作成日：{pack['created_date']}（日本时间／日本時間）  \n版本／版：{pack['version']}  \n业务状态／業務状態：未开始，尚未在公司工程执行／未着手、会社工程では実行前\n\n"
    text+=f"**[总任务入口／総合タスク入口]({pack['master_issue_url']})**\n\n"
    text+='## 使用方法／使い方\n\n'
    text+='- 中文：将总任务Issue交给公司Claude。无法读取GitHub时，可复制 [全部任务原文](全部任务.md)；每份文件都含完整中文和日文，选择一种语言执行一次即可。资料索引先行，追加Source开发最优先，智能体调查后置。\n'
    text+='- 日本語：総合Issueを会社Claudeへ渡します。GitHubを読めない場合は [全チケット本文](全部任务.md) をコピーできます。各ファイルは完全な中国語・日本語版を含むため、一方の言語を選び、一度だけ実行します。資料索引から始め、追加Source開発を最優先にし、エージェント調査は後続にします。\n\n'
    text+='## 任务清单／チケット一覧\n\n| ID | 优先级／優先区分 | 任务／タスク | 前置／依存 | GitHub |\n|---|---|---|---|---|\n'
    for t in pack['tickets']:
        text+=f"| {t['id']} | {t['group_zh']}／{t['group']} | [{t['title_zh']}／{t['title']}](个别任务/{t['id']}.md) | {', '.join(t['depends']) or '无／なし'} | [打开／開く]({t['issue_url']}) |\n"
    text+='\n## 来源与任务对应／資料とチケットの対応\n\n| 来源／資料 | 文件／ファイル | 对应任务／対応チケット |\n|---|---|---|\n'
    for s in pack['sources']:
        mappings=', '.join(t['id'] for t in pack['tickets'] if s['id'] in t['refs'])
        text+=f"| {s['id']} {s['title_zh']}／{s['title']} | [{s['path']}]({source_url(pack,s)}) | {mappings} |\n"
    text+='\n## 维护与实际状态／保守と実際の状態\n\n'
    text+='- 中文：\u0060维护/任务数据.json\u0060是任务事实、编号、依赖、状态和双语内容的唯一维护来源。更新后在任务票目录运行\u0060python 维护/生成任务票.py\u0060，生成个别任务、总任务、README和合并原文；脚本只生成本地文件，不会上传或更新GitHub。共通规则、当前任务、任务要求模板和证据原则已纳入各任务。历史来源已合并为主题文档，章节链接可直接定位；原件通过历史归档的来源索引追溯，不重复建票。创建文件或Issue不代表公司业务已经调查、开发或测试完成。\n'
    text+='- 日本語：\u0060维护/任务数据.json\u0060がタスク事実、ID、依存、状態、二言語内容の唯一の保守元です。更新後にタスク票ディレクトリで\u0060python 维护/生成任务票.py\u0060を実行すると、個別チケット、総合、README、統合本文を生成します。スクリプトはローカル生成のみで、GitHubへ送信・更新しません。共通ルール、現在タスク、依頼テンプレート、証拠原則を各チケットへ反映しています。旧資料はテーマ別文書へ統合し、節リンクで参照できます。原文は履歴索引から追跡し、重複起票しません。ファイルやIssue作成は、会社の調査・開発・試験完了を意味しません。\n'
    return text

def main():
    parser=argparse.ArgumentParser(description='生成中日双语任务票／日中二言語チケットを生成')
    parser.add_argument('--register',nargs=3,metavar=('ID','NUMBER','URL'))
    parser.add_argument('--master',nargs=2,metavar=('NUMBER','URL'))
    args=parser.parse_args();pack=json.loads(DATA_FILE.read_text(encoding='utf-8'))
    if args.register:
        id,number,url=args.register;matches=[t for t in pack['tickets'] if t['id']==id]
        assert len(matches)==1;matches[0].update(issue_number=int(number),issue_url=url)
    if args.master:
        number,url=args.master;pack.update(master_issue_number=int(number),master_issue_url=url)
    validate(pack)
    if args.register or args.master:DATA_FILE.write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    destination=ROOT/'个别任务';destination.mkdir(exist_ok=True)
    for t in pack['tickets']:(destination/f"{t['id']}.md").write_text(render_ticket(t,pack),encoding='utf-8')
    (ROOT/'总任务.md').write_text(render_master(pack),encoding='utf-8')
    bundle='# 公司Claude全部任务原文／会社Claude用・全チケット本文\n\n'
    bundle+='选中文或日文执行同一组任务一次，不要因为双语重复执行。  \n中国語か日本語を選び、同じタスク群を一度だけ実行してください。二言語だからといって重複実行しないでください。\n\n'
    bundle+=render_master(pack,'master-')+'\n\n---\n\n'
    bundle+='\n\n---\n\n'.join(render_ticket(t,pack,t['id'].lower()+'-') for t in pack['tickets'])
    (ROOT/'全部任务.md').write_text(bundle,encoding='utf-8')
    (ROOT/'README.md').write_text(render_readme(pack),encoding='utf-8')
    print(json.dumps({'tickets':len(pack['tickets']),'sources':len(pack['sources']),'languages':['zh-CN','ja'],'repository':pack['repository'],'master':pack['master_issue_url']},ensure_ascii=False))

if __name__=='__main__':
    main()
