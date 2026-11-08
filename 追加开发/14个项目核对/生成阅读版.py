"""从唯一维护的双语Markdown生成可离线使用的完整提示词页面。"""
from __future__ import annotations

import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'P002_14个项目追加对应一览核对与参考Source差分整理.md'
OUTPUT = SOURCE.with_suffix('.html')


def inline(text: str) -> str:
    parts = re.split(r'(`[^`\n]+`)', text)
    return ''.join('<code>' + html.escape(p[1:-1]) + '</code>' if p.startswith('`')
                   else re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html.escape(p))
                   for p in parts)


def render_markdown(text: str) -> str:
    lines = text.strip().splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('```'):
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i])
                i += 1
            assert i < len(lines), '代码围栏未闭合'
            blocks.append('<pre><code>' + html.escape('\n'.join(code)) + '</code></pre>')
            i += 1
            continue
        heading = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading:
            level = min(len(heading[1]), 6)
            blocks.append(f'<h{level}>' + inline(heading[2]) + f'</h{level}>')
            i += 1
            continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([v.strip() for v in lines[i].strip().strip('|').split('|')])
                i += 1
            assert len(rows) >= 2 and all(re.fullmatch(r':?-{3,}:?', c) for c in rows[1])
            header = '<thead><tr>' + ''.join('<th scope="col">' + inline(c) + '</th>' for c in rows[0]) + '</tr></thead>'
            body = '<tbody>' + ''.join('<tr>' + ''.join('<td>' + inline(c) + '</td>' for c in row) + '</tr>' for row in rows[2:]) + '</tbody>'
            blocks.append('<div class="table-wrap" tabindex="0"><table>' + header + body + '</table></div>')
            continue
        match = re.match(r'^(?:(\d+)\.\s+|-\s+)(.+)$', line)
        if match:
            ordered = match[1] is not None
            tag = 'ol' if ordered else 'ul'
            pattern = r'^(\d+)\.\s+(.+)$' if ordered else r'^-\s+(.+)$'
            items = []
            while i < len(lines):
                item_match = re.match(pattern, lines[i].strip())
                if not item_match:
                    break
                item = [item_match[2] if ordered else item_match[1]]
                value = f' value="{int(item_match[1])}"' if ordered else ''
                i += 1
                while i < len(lines) and lines[i].startswith('   '):
                    item.append(lines[i].strip())
                    i += 1
                items.append('<li' + value + '>' + ''.join('<p>' + inline(p) + '</p>' for p in item) + '</li>')
            blocks.append(f'<{tag}>' + ''.join(items) + f'</{tag}>')
            continue
        paragraph = [line]
        i += 1
        while i < len(lines) and lines[i].strip():
            if re.match(r'^(?:#{1,6}\s|\||```|-\s|\d+\.\s)', lines[i].strip()):
                break
            paragraph.append(lines[i].strip())
            i += 1
        blocks.append('<p>' + inline(' '.join(paragraph)) + '</p>')
    return '\n'.join(blocks)


def read_prompt(raw: str, language: str) -> dict:
    marker = 'ZH' if language == 'zh' else 'JA'
    start, end = f'<!-- PROMPT_{marker}_START -->', f'<!-- PROMPT_{marker}_END -->'
    assert raw.count(start) == raw.count(end) == 1
    prompt = raw.split(start, 1)[1].split(end, 1)[0].strip()
    matches = list(re.finditer(r'^### (\d{2})｜(.+)$', prompt, re.M))
    assert [m[1] for m in matches] == [f'{n:02}' for n in range(1, 11)]
    chapters = []
    for index, match in enumerate(matches):
        stop = matches[index + 1].start() if index + 1 < len(matches) else len(prompt)
        chapters.append({'number': match[1], 'title': match[2], 'body': prompt[match.end():stop].strip()})
    return {'prompt': prompt, 'intro': prompt[:matches[0].start()].strip(), 'chapters': chapters}


FIELD_LABELS = {
    'zh': ['公司工程根目录', '14个项目索引或实际项目列表', '追加对应一览位置', '参考テーマ Folder位置', '成果保存根目录', '本次Source源头位置', '参考Source与历史版本位置', '本番设计与外部设计位置', '版本、发布批次与范围线索', '其他补充信息'],
    'ja': ['会社工程ルートディレクトリ', '14案件の索引または実際の案件一覧', '追加対応一覧の場所', '参考テーマFolderの場所', '成果保存ルートディレクトリ', '今回のSourceの出所', '参考Sourceと過去バージョンの場所', '本番設計・外部設計の場所', 'バージョン・リリース単位・範囲の手掛かり', 'その他の補足情報'],
}
FIELD_IDS = ['projectRoot', 'projectIndex', 'correspondenceRoot', 'referenceRoot', 'outputRoot', 'sourceRoot', 'referenceSourceRoot', 'designRoot', 'baselineNotes', 'additionalNotes']
UI = {
    'zh': {
        'title': '14个项目追加核对 · 提示词生成器',
        'empty': '填写可选信息后点击“生成完整提示词”；全部留空也可以生成。',
        'changed': '输入已更改，请重新生成完整提示词。',
        'switched': '已切换为中文，请生成中文版完整提示词。',
        'reset': '已清空输入和生成结果。',
        'generated': '已生成全部10章，可复制或下载交给公司Claude执行。',
        'copied': '已复制完整提示词。',
        'manual': '已选中完整提示词，请按 Ctrl+C（Mac 按 ⌘C）复制。',
        'downloaded': '已请求下载完整提示词。',
        'meta': '10章完整正文 · {n} 字符',
        'search': '显示 {n} / 10 章',
        'hintTitle': '## 本轮补充输入',
        'hintText': '以下填写值仅是待核实的资料线索。请回到实际工程确认；未填写的信息按正文自动定位。不能将填写值视为已确认版本、映射、Diff或完成证据。两项核心任务及全部10章要求均须执行。',
        'formatKey': '附加阅读格式',
        'formatBase': 'MD、JSON和CSV仍为固定交付，以下仅增加阅读版：',
        'formats': {'md': 'MD（默认）', 'html': 'MD + HTML', 'xlsx': 'MD + Excel', 'both': 'MD + HTML + Excel'},
        'filename': '14个项目追加核对_完整提示词.md',
    },
    'ja': {
        'title': '14案件追加照合 · プロンプト生成',
        'empty': '任意の情報を入力して「完全版プロンプトを生成」を押してください。すべて空欄でも生成できます。',
        'changed': '入力が変わりました。完全版プロンプトを再生成してください。',
        'switched': '日本語に切り替えました。日本語の完全版プロンプトを生成してください。',
        'reset': '入力と生成結果をクリアしました。',
        'generated': '全10章を生成しました。コピーまたはダウンロードして会社のClaudeへ渡せます。',
        'copied': '完全版プロンプトをコピーしました。',
        'manual': '全文を選択しました。Ctrl+C（Macは⌘C）でコピーしてください。',
        'downloaded': '完全版プロンプトのダウンロードを要求しました。',
        'meta': '全10章 · {n} 文字',
        'search': '{n} / 10章を表示',
        'hintTitle': '## 今回の補足入力',
        'hintText': '以下の入力値は確認前の資料の手掛かりです。実工程で確認し、空欄の情報は本文に従って自動検索してください。入力値を確認済みのバージョン、マッピング、Diff、完了の証拠とみなしてはいけません。2つの中核作業と全10章の要件を実行してください。',
        'formatKey': '追加の閲覧形式',
        'formatBase': 'MD・JSON・CSVは引き続き必須の納品物とし、次の閲覧版を追加：',
        'formats': {'md': 'MD（既定）', 'html': 'MD + HTML', 'xlsx': 'MD + Excel', 'both': 'MD + HTML + Excel'},
        'filename': '14案件追加照合_完全版プロンプト.md',
    },
}

SCRIPT = r'''
'use strict';
const data = JSON.parse(document.getElementById('promptData').textContent);
const byId = id => document.getElementById(id);
const fieldIds = data.fieldIds;
let language = 'zh';
let generated = null;
const message = key => data.ui[language][key];
function setStatus(key) { byId('generationStatus').textContent = message(key); }
function clearGenerated(key) {
  generated = null;
  byId('promptPreview').value = '';
  byId('previewMeta').textContent = '';
  ['copyPrompt', 'downloadPrompt', 'selectPrompt'].forEach(id => { byId(id).disabled = true; });
  byId('result').dataset.state = 'empty';
  setStatus(key);
}
function buildPrompt(lang) {
  const hints = {};
  for (const id of fieldIds) {
    const value = byId(id).value;
    if (value.trim()) hints[data.fieldLabels[lang][id]] = value;
  }
  const format = byId('reportFormat').value;
  if (format !== 'md') hints[data.ui[lang].formatKey] = data.ui[lang].formatBase + data.ui[lang].formats[format];
  const prefix = Object.keys(hints).length ? data.ui[lang].hintTitle + '\n\n' + data.ui[lang].hintText + '\n\n```json\n' + JSON.stringify(hints, null, 2) + '\n```\n\n' : '';
  return prefix + data.prompts[lang];
}
function filterChapters() {
  const query = byId('chapterSearch').value.trim().toLocaleLowerCase();
  let count = 0;
  document.querySelectorAll('.chapter').forEach(chapter => {
    if (!chapter.id.startsWith('chapter-' + language + '-')) return;
    chapter.hidden = !!query && !chapter.textContent.toLocaleLowerCase().includes(query);
    if (!chapter.hidden) { count++; if (query) chapter.open = true; }
  });
  byId('searchStatus').textContent = message('search').replace('{n}', count);
}
function setLanguage(lang) {
  language = lang;
  document.body.dataset.lang = lang;
  document.documentElement.lang = lang === 'ja' ? 'ja' : 'zh-CN';
  document.title = message('title');
  byId('languageZh').setAttribute('aria-pressed', String(lang === 'zh'));
  byId('languageJa').setAttribute('aria-pressed', String(lang === 'ja'));
  document.querySelectorAll('[data-placeholder-zh]').forEach(el => { el.placeholder = el.getAttribute('data-placeholder-' + lang) || ''; });
  document.querySelectorAll('[data-label-zh]').forEach(el => { el.setAttribute('aria-label', el.getAttribute('data-label-' + lang) || ''); });
  for (const option of byId('reportFormat').options) option.textContent = data.ui[lang].formats[option.value];
  byId('chapterSearch').value = '';
  clearGenerated('switched');
  filterChapters();
}
byId('languageZh').addEventListener('click', () => { if (language !== 'zh') setLanguage('zh'); });
byId('languageJa').addEventListener('click', () => { if (language !== 'ja') setLanguage('ja'); });
byId('promptForm').addEventListener('submit', event => {
  event.preventDefault();
  generated = { language, text: buildPrompt(language), filename: message('filename') };
  byId('promptPreview').value = generated.text;
  byId('previewMeta').textContent = message('meta').replace('{n}', generated.text.length.toLocaleString(language === 'ja' ? 'ja-JP' : 'zh-CN'));
  ['copyPrompt', 'downloadPrompt', 'selectPrompt'].forEach(id => { byId(id).disabled = false; });
  byId('result').dataset.state = 'ready';
  setStatus('generated');
  byId('result').scrollIntoView({ behavior: 'smooth', block: 'start' });
});
byId('promptForm').addEventListener('input', () => { if (generated) clearGenerated('changed'); });
byId('promptForm').addEventListener('change', () => { if (generated) clearGenerated('changed'); });
byId('promptForm').addEventListener('reset', () => { clearGenerated('reset'); });
function selectPreview() {
  byId('promptPreview').focus();
  byId('promptPreview').select();
  byId('promptPreview').setSelectionRange(0, byId('promptPreview').value.length);
}
byId('copyPrompt').addEventListener('click', async () => {
  if (!generated) return;
  const current = generated;
  let copied = false;
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) { await navigator.clipboard.writeText(current.text); copied = true; }
  } catch (_) { /* 离线环境继续尝试本地选择复制。 */ }
  if (generated !== current) return;
  if (!copied) {
    selectPreview();
    try { copied = document.execCommand('copy'); } catch (_) { copied = false; }
  }
  setStatus(copied ? 'copied' : 'manual');
});
byId('selectPrompt').addEventListener('click', () => { if (generated) { selectPreview(); setStatus('manual'); } });
byId('downloadPrompt').addEventListener('click', () => {
  if (!generated) return;
  const url = URL.createObjectURL(new Blob(['\ufeff' + generated.text + '\n'], { type: 'text/markdown;charset=utf-8' }));
  const anchor = document.createElement('a');
  anchor.href = url; anchor.download = generated.filename;
  document.body.appendChild(anchor); anchor.click(); anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  setStatus('downloaded');
});
byId('chapterSearch').addEventListener('input', filterChapters);
for (const [id, open] of [['expandAll', true], ['collapseAll', false]]) {
  byId(id).addEventListener('click', () => document.querySelectorAll('.chapter').forEach(chapter => {
    if (chapter.id.startsWith('chapter-' + language + '-') && !chapter.hidden) chapter.open = open;
  }));
}
document.querySelectorAll('a[href^="#chapter-"]').forEach(link => link.addEventListener('click', () => {
  byId('chapterSearch').value = ''; filterChapters();
  const chapter = byId(link.hash.slice(1)); if (chapter) chapter.open = true;
}));
setLanguage('zh');
setStatus('empty');
byId('generatePrompt').disabled = false;
'''


def main() -> None:
    raw = SOURCE.read_text(encoding='utf-8')
    texts = {lang: read_prompt(raw, lang) for lang in ('zh', 'ja')}
    payload = {'prompts': {lang: value['prompt'] for lang, value in texts.items()},
               'fieldIds': FIELD_IDS, 'ui': UI,
               'fieldLabels': {lang: dict(zip(FIELD_IDS, labels)) for lang, labels in FIELD_LABELS.items()}}
    serialized = json.dumps(payload, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    replacements = {'@@DATA@@': serialized, '@@SCRIPT@@': SCRIPT, '@@SOURCE_NAME@@': html.escape(SOURCE.name, quote=True)}
    for lang, text in texts.items():
        blocks = ['<div class="guide-intro">' + render_markdown(text['intro']) + '</div>']
        navigation = []
        for chapter in text['chapters']:
            number, title = chapter['number'], html.escape(chapter['title'])
            target = f'chapter-{lang}-{number}'
            blocks.append(f'<details class="chapter" id="{target}"><summary><span class="chapter-number">{number}</span><h3>{title}</h3></summary><div class="chapter-body">' + render_markdown(chapter['body']) + '</div></details>')
            navigation.append(f'<a href="#{target}" data-lang="{lang}"><span>{number}</span><span>{title}</span></a>')
        replacements[f'@@{lang.upper()}_CHAPTERS@@'] = '\n'.join(blocks)
        replacements[f'@@{lang.upper()}_NAV@@'] = '\n'.join(navigation)
    output = TEMPLATE
    for key, value in replacements.items():
        assert output.count(key) == 1, ('模板插槽数量错误', key)
        output = output.replace(key, value)
    assert not re.search(r'@@[A-Z_]+@@', output), '模板插槽未替换'
    OUTPUT.write_text(output, encoding='utf-8', newline='\n')
    print(json.dumps({'output': OUTPUT.name, 'chapters_per_language': 10, 'languages': ['zh', 'ja'], 'bytes': OUTPUT.stat().st_size}, ensure_ascii=False))


# The complete offline page template is embedded below; Markdown remains the prompt source.
TEMPLATE = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="description" content="为14个追加项目生成完整提示词：核对Source漏项，保存真实参考改修Input。">
<title>P002 · 14项目追加核对</title>
<style>
:root{--bg:#f3f6f7;--paper:#fff;--ink:#19323f;--muted:#657982;--line:#dae5e8;--teal:#086c65;--soft:#e8f4f0;--navy:#142c3b;--gold:#d0a765}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.8 "Segoe UI","Microsoft YaHei","Yu Gothic",Meiryo,system-ui,sans-serif}body[data-lang=zh] [data-lang=ja],body[data-lang=ja] [data-lang=zh]{display:none!important}button,input,textarea,select{font:inherit}button{cursor:pointer}button:disabled{cursor:not-allowed}a{color:var(--teal);text-underline-offset:3px}button,a,input,textarea,select,summary{-webkit-tap-highlight-color:transparent;outline-offset:4px}button:focus-visible,a:focus-visible,input:focus-visible,textarea:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid var(--gold)}::selection{background:#cce9e0}[hidden]{display:none!important}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}.skip-link{position:fixed;top:-90px;left:16px;z-index:20;padding:12px 18px;background:#fff;border-radius:8px;box-shadow:0 4px 22px #142c3b30}.skip-link:focus{top:14px}
.app{display:grid;grid-template-columns:250px minmax(0,1fr);min-height:100vh}.sidebar{position:sticky;top:0;align-self:start;display:flex;flex-direction:column;height:100vh;padding:27px 18px 22px;background:var(--navy);color:#e4eef0;overflow-y:auto}.brand{display:flex;align-items:center;gap:11px;padding:0 9px 23px}.brand-mark{display:grid;place-items:center;width:39px;height:42px;border:1px solid #6fae9e88;border-radius:10px;background:#1e3d48;color:#95d6c5;font:11px/1.5 Consolas,monospace;flex:none}.brand b{display:block;font-size:13px;font-weight:600;line-height:1.6}.brand small{display:block;font:9px/1.5 Consolas,monospace;letter-spacing:.1em;color:#9cb5bf;margin-top:4px}.quick-nav{display:grid;gap:4px;padding-bottom:20px;border-bottom:1px solid #35505e}.quick-nav a{display:flex;gap:10px;padding:8px 11px;border-radius:7px;color:#d6e6e8;text-decoration:none;font-size:11.5px}.quick-nav a:hover{background:#284652}.quick-nav .nav-dot{font:10px/1.9 Consolas,monospace;color:#7db8aa}.nav-caption{margin:23px 11px 10px;color:#9db5bd;font-size:10px;letter-spacing:.04em}.chapter-nav a{display:flex;gap:9px;align-items:flex-start;padding:8px 10px;border-radius:7px;color:#c9dbe0;text-decoration:none;font-size:11px;line-height:1.65}.chapter-nav a:hover,.chapter-nav a.active,.chapter-nav a[aria-current=location]{background:#294754;color:#fff}.chapter-nav a.active,.chapter-nav a[aria-current=location]{box-shadow:inset 3px 0 #79d0b8}.chapter-nav a>span:first-child,.chapter-nav .nav-number{flex:none;font:9px/2 Consolas,monospace;color:#90adb8}.chapter-nav b{font-weight:400}.sidebar-foot{margin-top:auto;padding:24px 10px 0}.sidebar-foot p{margin:0;padding-top:17px;border-top:1px solid #35505e;font-size:10px;line-height:1.9;color:#a6bec6}.sidebar-foot a{display:inline-block;margin-top:10px;font-size:10px;color:#bcdcd2;text-decoration:none}
main{min-width:0;width:100%;max-width:1300px;margin:0 auto;padding:24px 39px 47px}.topline{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:19px}.breadcrumb{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:10.5px}.breadcrumb:before{content:"";width:6px;height:6px;background:var(--teal);border-radius:50%}.language-switch{display:inline-flex;gap:2px;padding:3px;border:1px solid #ccddd7;border-radius:8px;background:#fff;flex:none}.language-switch button{padding:6px 12px;min-width:60px;border:0;border-radius:5px;background:transparent;color:var(--muted);font-size:10.5px}.language-switch button[aria-pressed=true]{background:var(--teal);color:#fff}.hero h1{font-size:clamp(25px,2.7vw,34px);line-height:1.45;letter-spacing:-.035em;margin:0 0 7px;font-weight:700}.hero h1 em{font-style:normal;color:var(--teal)}.hero p{max-width:850px;font-size:11.5px;line-height:1.9;color:var(--muted);margin:0}.scope-strip{display:flex;align-items:center;gap:19px;flex-wrap:wrap;margin:15px 0 21px;font-size:10.5px;color:#5d747b}.scope-strip b{font-weight:600;color:var(--ink);padding-right:4px}.scope-strip .scope-task{padding-left:15px;border-left:1px solid #d3dfe1;color:var(--teal)}
.panel{border:1px solid var(--line);border-radius:16px;background:var(--paper);box-shadow:0 6px 26px #1d405005}.setup-section{padding:22px 24px}.section-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:20px}.section-heading h2{font-size:17px;line-height:1.6;margin:0;font-weight:650}.section-heading p{max-width:650px;font-size:10.5px;color:var(--muted);line-height:1.85;margin:5px 0 0}.button{display:inline-flex;justify-content:center;align-items:center;gap:7px;min-height:39px;padding:9px 14px;border:1px solid var(--line);border-radius:7px;background:#fff;color:var(--ink);font-size:11px;font-weight:600;line-height:1.5;white-space:nowrap;text-decoration:none}.button:hover{background:#f1f7f5;border-color:#c1d5cd}.button.primary{color:#fff;background:var(--teal);border-color:var(--teal);box-shadow:0 3px 8px #096e6414}.button.primary:hover{background:#07564f;border-color:#07564f}.button:disabled,.button.primary:disabled{color:#8e9da5;background:#edf2f3;border-color:#e0e7e9;box-shadow:none}.button.quiet{background:transparent;border-color:transparent;font-weight:400;color:var(--muted);padding-left:8px;padding-right:8px}.button.quiet:hover{color:var(--teal);background:#f0f6f4}.button.quiet:disabled{color:#a0acb2;background:transparent}.actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.field-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:14px 19px;margin-top:19px}.field{min-width:0}.field.full{grid-column:1/-1}.field label{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px;font-size:10.5px;font-weight:600;color:#304955}.optional{font-size:9px;font-weight:400;color:#899a9a;white-space:nowrap}.field input,.field textarea,.field select{display:block;width:100%;min-height:40px;padding:9px 11px;border:1px solid #cddbe0;border-radius:7px;background:#fbfcfd;color:var(--ink);font-size:11.5px;line-height:1.65}.field textarea{min-height:70px;resize:vertical}.field input::placeholder,.field textarea::placeholder{color:#8b9ba3}.field input:focus,.field textarea:focus,.field select:focus{background:#fff;border-color:#6ba89b;box-shadow:0 0 0 3px #0b746a08}.field-help{font-size:10px;line-height:1.8;color:var(--muted);margin:5px 0 0}.advanced{margin-top:17px;border:1px solid #e0e9eb;border-radius:9px;background:#f9fbfb;overflow:hidden}.advanced>summary{display:flex;align-items:center;justify-content:space-between;list-style:none;padding:11px 14px;cursor:pointer;color:#43645c;font-size:10.5px;font-weight:600;gap:12px}.advanced>summary::-webkit-details-marker{display:none}.advanced>summary:after{content:"+";font:18px/1 Consolas,monospace;color:#78958e}.advanced[open]>summary:after{content:"−"}.advanced[open]>summary{border-bottom:1px solid #e1eaea}.advanced .field-grid{margin:0;padding:17px 15px 19px}.advanced .field input,.advanced .field textarea{background:#fff}.form-bottom{display:flex;align-items:center;justify-content:space-between;gap:16px;border-top:1px solid #e6ecee;padding-top:12px;margin-top:17px}.local-note{font-size:10px;color:var(--muted);line-height:1.85;margin:0}.generation-status{font-size:10.5px;color:var(--muted);line-height:1.8;min-height:19px;margin:8px 0 0}.noscript{font-size:10.5px;padding:11px 14px;border:1px solid #e3d6b8;background:#faf5e9;color:#806432;border-radius:8px;margin-top:12px}
.result-section{padding:22px 24px;margin-top:20px;scroll-margin-top:23px}.result-section .section-heading{align-items:center}.preview-meta{font:10px/1.7 Consolas,"Microsoft YaHei","Yu Gothic",sans-serif;color:var(--muted);text-align:right}.preview-label{display:block;font-size:10.5px;font-weight:600;color:#526c77;margin:15px 0 7px}#promptPreview{display:block;width:100%;min-height:285px;max-height:620px;padding:17px 18px;resize:vertical;border:1px solid #d7e2e6;border-radius:9px;background:#f7f9fa;color:#334d5a;font:11px/1.95 Consolas,"Microsoft YaHei","Yu Gothic",Meiryo,monospace;tab-size:2;overflow-wrap:anywhere}.result-bottom{display:flex;justify-content:space-between;align-items:center;gap:17px;flex-wrap:wrap;margin-top:14px}.preview-note{max-width:420px;margin:0;font-size:10px;line-height:1.85;color:var(--muted)}
.guide-section{margin-top:32px;scroll-margin-top:23px}.guide-heading{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;flex-wrap:wrap}.guide-heading h2{font-size:18px;margin:0;line-height:1.65;font-weight:650}.guide-heading p{font-size:10.5px;color:var(--muted);margin:4px 0 0}.chapter-search{display:block;position:relative;width:240px;max-width:100%}.chapter-search:before{content:"⌕";position:absolute;left:12px;top:7px;font-size:22px;line-height:1;color:#7f96a0;pointer-events:none}.chapter-search input{min-height:39px;width:100%;padding:8px 11px 8px 34px;border:1px solid #d2dfe3;border-radius:7px;background:#fff;font-size:11px;color:var(--ink)}.guide-tools{display:flex;align-items:center;justify-content:space-between;gap:13px;margin:13px 0 11px}.search-status{margin:0;min-height:18px;font-size:10px;color:var(--muted);line-height:1.8}.guide-tools .actions{gap:2px}.guide-tools .button{font-size:10px;min-height:30px;padding:5px 8px}.guide-intro{padding:15px 18px;margin-bottom:13px;border:1px solid #d7e7e0;border-radius:11px;background:#edf6f2;color:#3e6256;font-size:11.5px;line-height:1.95;overflow-wrap:anywhere}.guide-intro p{margin:5px 0}.chapters,.chapter{margin:0 0 11px;border:1px solid var(--line);border-radius:11px;background:#fff;overflow:hidden;scroll-margin-top:23px}.chapters>summary,.chapter>summary{display:flex;align-items:center;gap:11px;min-height:61px;padding:16px 18px;list-style:none;cursor:pointer;font-size:12.5px;font-weight:600;line-height:1.8}.chapters>summary::-webkit-details-marker,.chapter>summary::-webkit-details-marker{display:none}.chapters>summary:after,.chapter>summary:after{content:"⌄";font-size:18px;font-weight:400;color:#8198a0;margin-left:auto;padding-left:8px;flex:none;line-height:1;transition:transform .15s}.chapters[open]>summary:after,.chapter[open]>summary:after{transform:rotate(180deg)}.chapters[open]>summary,.chapter[open]>summary{border-bottom:1px solid #e6edef}.chapter-number,.chapter-no{flex:none;padding:3px 6px;border-radius:5px;background:var(--soft);color:var(--teal);font:10px/1.7 Consolas,monospace}.chapters summary h3,.chapters summary h2,.chapter summary h3,.chapter summary h2{font:inherit;margin:0}.chapter-body,.chapter-content{padding:6px 21px 21px;font-size:11.5px;line-height:1.95;overflow-wrap:anywhere}.chapter-body p,.chapter-content p{margin:12px 0}.chapter-body h3,.chapter-body h4,.chapter-content h3,.chapter-content h4{font-size:12.5px;line-height:1.7;margin:24px 0 10px}.chapter-body ul,.chapter-body ol,.chapter-content ul,.chapter-content ol{margin:12px 0;padding-left:22px}.chapter-body li,.chapter-content li{margin:10px 0;padding-left:3px}.chapter-body li>p,.chapter-content li>p{margin:6px 0}.chapter-body code,.chapter-content code,.guide-intro code{padding:2px 5px;border:1px solid #e2eaed;border-radius:4px;background:#eef4f5;color:#315762;font:10.5px/1.8 Consolas,"Microsoft YaHei","Yu Gothic",monospace;white-space:pre-wrap}.chapter-body pre,.chapter-content pre{max-width:100%;margin:15px 0;padding:15px 17px;overflow:auto;border:1px solid #dde7eb;border-radius:8px;background:#f3f7f8;tab-size:2;white-space:pre;font-size:10.5px;line-height:1.8}.chapter-body pre code,.chapter-content pre code{padding:0;border:0;background:transparent;white-space:pre}.table-wrap{width:100%;max-width:100%;overflow-x:auto;margin:16px 0;border:1px solid var(--line);border-radius:8px}.chapter-body table,.chapter-content table{border-collapse:collapse;width:100%;min-width:510px;font-size:10.5px;line-height:1.95;text-align:left}.chapter-body th,.chapter-content th{background:#edf4f1;color:#345b4f;font-weight:600}.chapter-body th,.chapter-body td,.chapter-content th,.chapter-content td{padding:10px 11px;border-bottom:1px solid #e2eaed;vertical-align:top}.chapter-body tr:last-child td,.chapter-content tr:last-child td{border-bottom:0}.chapter-body tbody tr:nth-child(even),.chapter-content tbody tr:nth-child(even){background:#fafcfc}.chapter-body blockquote,.chapter-content blockquote{margin:14px 0;padding:10px 14px;border-left:3px solid #74b09e;background:#f1f7f4;color:#4b695f}.footer{display:flex;justify-content:space-between;gap:20px;margin-top:28px;padding-top:18px;border-top:1px solid var(--line);font-size:10px;line-height:1.85;color:var(--muted)}.footer p{margin:0}.footer a{color:#5d7b70;white-space:nowrap}
@media(min-width:1600px){main{padding-left:58px;padding-right:58px}.sidebar{padding-left:23px;padding-right:23px}}
@media(max-width:1160px){.app{grid-template-columns:225px minmax(0,1fr)}main{padding:23px 26px 42px}.sidebar{padding:25px 14px 20px}.brand{padding-left:7px}.brand b{font-size:12px}.chapter-nav a{font-size:10.5px}.setup-section,.result-section{padding:21px}.scope-strip{gap:12px}.scope-strip .scope-task{padding-left:12px}.field-grid{gap:14px 16px}}
@media(max-width:860px){.app{display:block}.sidebar{position:relative;display:block;height:auto;padding:14px 22px}.brand{padding:0}.brand-mark{width:33px;height:34px;border-radius:8px;font-size:10px}.brand b{font-size:13px}.brand small{display:none}.quick-nav{display:flex;gap:6px;padding:10px 0 0;border:0}.quick-nav a{font-size:10px;padding:5px 8px}.nav-caption,.chapter-nav,.sidebar-foot{display:none}main{padding:21px 24px 39px}.topline{margin-bottom:19px}.hero h1{font-size:29px}.guide-section{margin-top:28px}.chapter-body,.chapter-content{padding:6px 18px 19px}}
@media(max-width:580px){main{padding:17px 15px 32px}.sidebar{padding:13px 15px}.quick-nav{justify-content:space-between;gap:0}.quick-nav a{padding-left:3px;padding-right:6px}.breadcrumb{font-size:9.5px}.language-switch button{min-width:51px;padding:6px 9px;font-size:10px}.topline{gap:10px;margin-bottom:18px}.hero h1{font-size:26px}.hero p{font-size:11px}.scope-strip{font-size:10px;gap:8px 13px;margin:12px 0 17px}.scope-strip .scope-task{padding:0;border:0}.setup-section,.result-section{padding:18px 16px;border-radius:13px}.section-heading{gap:12px}.section-heading h2{font-size:15px}.section-heading p{font-size:10px}.section-heading .primary{font-size:10px;padding:9px 10px;min-height:39px}.field-grid{grid-template-columns:minmax(0,1fr);gap:15px;margin-top:18px}.field.full{grid-column:auto}.field input,.field textarea,.field select{font-size:11px;min-height:43px}.field label{font-size:10.5px}.advanced .field-grid{padding:15px 12px 17px}.advanced>summary{font-size:10.5px;padding:11px 12px}.form-bottom{gap:12px}.local-note{font-size:9.5px}.generation-status{font-size:10px}.preview-meta{max-width:95px;font-size:9px}.preview-label{font-size:10px}#promptPreview{min-height:260px;padding:13px 12px;font-size:10.5px;line-height:1.9}.result-bottom{gap:13px}.result-bottom .actions{width:100%}.result-bottom .primary{flex:1}.result-bottom .button{font-size:10.5px;padding:10px 12px}.result-bottom .quiet{padding-left:7px;padding-right:7px}.preview-note{font-size:9.5px}.guide-heading{gap:13px}.guide-heading h2{font-size:16px}.chapter-search{width:100%}.guide-tools{gap:8px}.guide-tools .button{padding-left:5px;padding-right:5px;font-size:9.5px}.search-status{font-size:9.5px}.chapters>summary,.chapter>summary{padding:14px 13px;min-height:59px;gap:8px;font-size:11.5px}.chapter-body,.chapter-content{padding:5px 14px 17px;font-size:11px}.guide-intro{padding:12px 14px;font-size:11px}.footer{flex-direction:column;gap:9px;font-size:9.5px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*:before,*:after{transition:none!important}}
@media print{@page{size:A4;margin:15mm 12mm}body{background:#fff}.app{display:block}.sidebar,.topline,.setup-section,.result-section,.chapter-search,.guide-tools,.skip-link,.noscript{display:none!important}main{max-width:none;padding:0}.hero h1{font-size:23pt}.hero p{font-size:9pt}.scope-strip{margin-bottom:20px}.guide-section{margin-top:20px}.guide-intro{padding:12px 14px}.chapters,.chapter{border:0;border-radius:0;overflow:visible;margin-bottom:13px}.chapters>summary,.chapter>summary{padding:10px 0 6px;font-size:12pt;break-after:avoid}.chapters>summary:after,.chapter>summary:after{display:none}.chapter-body,.chapter-content{padding:2px 0 10px;font-size:9pt}.table-wrap{overflow:visible;border:0}.chapter-body table,.chapter-content table{min-width:0;font-size:8pt}.chapter-body th,.chapter-body td,.chapter-content th,.chapter-content td{border:1px solid #ccd7da;padding:6px}.chapter-body pre,.chapter-content pre{white-space:pre-wrap;overflow:visible;font-size:8pt}.chapters::details-content,.chapter::details-content{content-visibility:visible;display:block}.chapters[hidden],.chapter[hidden]{display:block!important}.footer{font-size:8pt}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
</style>
</head>
<body data-lang="zh">
<a class="skip-link" href="#main"><span data-lang="zh">跳到主要内容</span><span data-lang="ja">本文へ移動</span></a>
<div class="app">
<aside class="sidebar">
  <div class="brand"><div class="brand-mark" aria-hidden="true">P002</div><div><b><span data-lang="zh">项目追加工作手册</span><span data-lang="ja">追加案件の作業ガイド</span></b><small>SOURCE / DIFF / INPUT</small></div></div>
  <nav class="quick-nav" aria-label="快速入口" data-label-zh="快速入口" data-label-ja="クイックアクセス">
    <a href="#setup"><span class="nav-dot" aria-hidden="true">01</span><span data-lang="zh">填写信息</span><span data-lang="ja">情報を入力</span></a>
    <a href="#result"><span class="nav-dot" aria-hidden="true">02</span><span data-lang="zh">预览与复制</span><span data-lang="ja">プレビューとコピー</span></a>
    <a href="#guide"><span class="nav-dot" aria-hidden="true">03</span><span data-lang="zh">阅读全文</span><span data-lang="ja">全文を読む</span></a>
  </nav>
  <div class="nav-caption"><span data-lang="zh">完整提示词 · 10章</span><span data-lang="ja">プロンプト全文 · 全10章</span></div>
  <nav class="chapter-nav" aria-label="章节目录" data-label-zh="章节目录" data-label-ja="章の目次"><div data-lang="zh">@@ZH_NAV@@</div><div data-lang="ja">@@JA_NAV@@</div></nav>
  <div class="sidebar-foot"><p><span data-lang="zh">核对清单、记录证据、保存真实差分，再交给后续开发。</span><span data-lang="ja">一覧を照合し、証拠と実差分を残して、次の開発へ渡します。</span></p><a href="#setup"><span data-lang="zh">↑ 返回信息填写</span><span data-lang="ja">↑ 入力欄へ戻る</span></a></div>
</aside>
<main id="main">
  <div class="topline"><div class="breadcrumb"><span data-lang="zh">项目追加 / 14项目核对</span><span data-lang="ja">追加開発 / 14案件照合</span></div><div class="language-switch" role="group" aria-label="显示与生成语言" data-label-zh="显示与生成语言" data-label-ja="表示・生成する言語"><button id="languageZh" type="button" aria-pressed="true"><span data-lang="zh">中文</span><span data-lang="ja">中国語</span></button><button id="languageJa" type="button" aria-pressed="false"><span data-lang="zh">日文</span><span data-lang="ja">日本語</span></button></div></div>
  <header class="hero"><h1><span data-lang="zh">核对Source漏项，<em>保存开发Input。</em></span><span data-lang="ja">Sourceの記載漏れを照合し、<em>開発Inputを残す。</em></span></h1><p><span data-lang="zh">填写已知信息，生成完整提示词，再交给公司Claude执行。未知位置可留空，从实际资料定位。</span><span data-lang="ja">分かっている情報を入力し、生成した全文を会社のClaudeへ渡します。不明な場所は空欄にし、実際の資料から特定させます。</span></p></header>
  <div class="scope-strip"><span><b>14</b><span data-lang="zh">个目标项目</span><span data-lang="ja">件の対象案件</span></span><span class="scope-task"><span data-lang="zh">01 · 发布清单反查漏项</span><span data-lang="ja">01 · リリース一覧から記載漏れ照合</span></span><span class="scope-task"><span data-lang="zh">02 · 真实差分形成Input</span><span data-lang="ja">02 · 実差分からInputを作成</span></span></div>
  <section class="panel setup-section" id="setup" aria-labelledby="setupTitle">
    <form id="promptForm" autocomplete="off">
      <div class="section-heading"><div><h2 id="setupTitle"><span data-lang="zh">补充已知信息</span><span data-lang="ja">分かっている情報を入力</span></h2><p><span data-lang="zh">所有信息均可留空。输入只作为补充线索，完整正文和两项核心任务都会保留。</span><span data-lang="ja">すべて空欄でも生成できます。入力は補足情報となり、本文全文と2つの中核作業は保持されます。</span></p></div><button class="button primary" type="submit" id="generatePrompt" disabled><span data-lang="zh">生成完整提示词</span><span data-lang="ja">プロンプト全文を生成</span><span aria-hidden="true">→</span></button></div>
      <div class="field-grid">
        <div class="field"><label for="projectRoot"><span data-lang="zh">公司工程根目录</span><span data-lang="ja">会社のプロジェクトルート</span><small class="optional"><span data-lang="zh">可选</span><span data-lang="ja">任意</span></small></label><input id="projectRoot" type="text" spellcheck="false" placeholder="实际业务工程的位置" data-placeholder-zh="实际业务工程的位置" data-placeholder-ja="実際の業務プロジェクトの場所"></div>
        <div class="field"><label for="outputRoot"><span data-lang="zh">调查成果保存目录</span><span data-lang="ja">調査成果の保存先</span><small class="optional"><span data-lang="zh">可选</span><span data-lang="ja">任意</span></small></label><input id="outputRoot" type="text" spellcheck="false" placeholder="留空时沿用公司工程既有位置" data-placeholder-zh="留空时沿用公司工程既有位置" data-placeholder-ja="空欄の場合はプロジェクトの既存保存先を使用"></div>
        <div class="field"><label for="correspondenceRoot"><span data-lang="zh">追加对应一览位置</span><span data-lang="ja">追加対応一覧の場所</span><small class="optional"><span data-lang="zh">可选</span><span data-lang="ja">任意</span></small></label><input id="correspondenceRoot" type="text" spellcheck="false" placeholder="清单文件或所在目录" data-placeholder-zh="清单文件或所在目录" data-placeholder-ja="一覧ファイルまたは保存ディレクトリ"></div>
        <div class="field"><label for="referenceRoot"><span data-lang="zh">参考テーマ资料位置</span><span data-lang="ja">参考テーマの資料の場所</span><small class="optional"><span data-lang="zh">可选</span><span data-lang="ja">任意</span></small></label><input id="referenceRoot" type="text" spellcheck="false" placeholder="参考Folder或发布模块一览的位置" data-placeholder-zh="参考Folder或发布模块一览的位置" data-placeholder-ja="参考フォルダーまたはリリースモジュール一覧の場所"></div>
        <div class="field full"><label for="projectIndex"><span data-lang="zh">项目清单位置或实际项目列表</span><span data-lang="ja">案件一覧の場所、または実際の案件リスト</span><small class="optional"><span data-lang="zh">可选</span><span data-lang="ja">任意</span></small></label><textarea id="projectIndex" rows="2" spellcheck="false" placeholder="填写清单位置，或逐行粘贴实际テーマID、名称及已知资料位置" data-placeholder-zh="填写清单位置，或逐行粘贴实际テーマID、名称及已知资料位置" data-placeholder-ja="一覧の場所、または実際のテーマID・名称・既知の資料の場所を1行ずつ入力"></textarea></div>
        <div class="field full"><label for="reportFormat"><span data-lang="zh">调查成果的阅读格式</span><span data-lang="ja">調査成果の閲覧形式</span></label><select id="reportFormat"><option value="md" selected>MD（默认）</option><option value="html">附加HTML阅读版</option><option value="xlsx">附加Excel阅读版</option><option value="both">附加HTML和Excel阅读版</option></select><p class="field-help"><span data-lang="zh">MD／JSON／CSV固定交付；HTML／Excel是公司Claude调查报告的附加阅读版。本页下载的提示词始终为.md。</span><span data-lang="ja">MD／JSON／CSVは必須の納品物です。HTML／Excelは会社のClaudeが作る調査報告書の追加閲覧版です。このページで保存するプロンプトは常に.mdです。</span></p></div>
      </div>
      <details class="advanced"><summary><span data-lang="zh">更多资料与说明（可选）</span><span data-lang="ja">資料と補足説明を追加（任意）</span></summary><div class="field-grid">
        <div class="field"><label for="sourceRoot"><span data-lang="zh">本次Source源头</span><span data-lang="ja">今回使用するSourceの出所</span></label><input id="sourceRoot" type="text" spellcheck="false" placeholder="本次开发所基于的Source位置" data-placeholder-zh="本次开发所基于的Source位置" data-placeholder-ja="今回の開発の基準となるSourceの場所"></div>
        <div class="field"><label for="referenceSourceRoot"><span data-lang="zh">参考Source历史位置</span><span data-lang="ja">参考Sourceの過去バージョンの場所</span></label><input id="referenceSourceRoot" type="text" spellcheck="false" placeholder="改修前后版本、历史提交或已有Diff的位置" data-placeholder-zh="改修前后版本、历史提交或已有Diff的位置" data-placeholder-ja="改修前後の版、過去のコミット、既存Diffの場所"></div>
        <div class="field full"><label for="designRoot"><span data-lang="zh">本番或外部设计位置</span><span data-lang="ja">本番設計・外部設計の場所</span></label><input id="designRoot" type="text" spellcheck="false" placeholder="设计书及新增项目说明的位置" data-placeholder-zh="设计书及新增项目说明的位置" data-placeholder-ja="設計書と新規追加項目の説明の場所"></div>
        <div class="field"><label for="baselineNotes"><span data-lang="zh">版本、批次与范围说明</span><span data-lang="ja">バージョン・リリース単位・範囲</span></label><textarea id="baselineNotes" rows="3" spellcheck="false" placeholder="已知有效版本、发布批次、适用范围或冲突" data-placeholder-zh="已知有效版本、发布批次、适用范围或冲突" data-placeholder-ja="既知の有効な版、リリース単位、適用範囲、競合"></textarea></div>
        <div class="field"><label for="additionalNotes"><span data-lang="zh">其他补充说明</span><span data-lang="ja">その他の補足説明</span></label><textarea id="additionalNotes" rows="3" spellcheck="false" placeholder="已有记录、资料限制或恢复线索" data-placeholder-zh="已有记录、资料限制或恢复线索" data-placeholder-ja="既存記録、資料の制約、再開に必要な手掛かり"></textarea></div>
      </div></details>
      <div class="form-bottom"><p class="local-note"><span data-lang="zh">只在本地生成提示词，不读取目录，不上传输入内容。</span><span data-lang="ja">ローカルで生成します。ディレクトリの読取りや入力内容の送信は行いません。</span></p><button class="button quiet" type="reset" id="resetForm"><span data-lang="zh">清空输入</span><span data-lang="ja">入力をクリア</span></button></div>
    </form>
    <p class="generation-status" id="generationStatus" role="status"><span data-lang="zh">尚未生成。可保留空白，直接生成完整正文。</span><span data-lang="ja">未生成です。入力せずに本文全文を生成することもできます。</span></p>
    <noscript><p class="noscript"><span data-lang="zh">生成、复制和下载需要JavaScript。下方完整原文仍可阅读和手动复制。</span><span data-lang="ja">生成・コピー・保存にはJavaScriptが必要です。下の本文全文は読み、手動コピーできます。</span></p></noscript>
  </section>
  <section class="panel result-section" id="result" aria-labelledby="resultTitle">
    <div class="section-heading"><h2 id="resultTitle"><span data-lang="zh">预览与复制</span><span data-lang="ja">プレビューとコピー</span></h2><span class="preview-meta" id="previewMeta"><span data-lang="zh">生成后显示语言与字数</span><span data-lang="ja">生成後に言語と文字数を表示</span></span></div>
    <label class="preview-label" for="promptPreview"><span data-lang="zh">将复制或下载的完整提示词</span><span data-lang="ja">コピー・保存するプロンプト全文</span></label>
    <textarea id="promptPreview" readonly rows="12" spellcheck="false" wrap="soft" aria-describedby="previewDescription"></textarea>
    <div class="result-bottom"><p class="preview-note" id="previewDescription"><span data-lang="zh">核对预览后交给公司Claude。复制和下载使用同一份生成结果。</span><span data-lang="ja">プレビューを確認して会社のClaudeへ渡します。コピーと保存には同じ生成結果を使います。</span></p><div class="actions"><button class="button quiet" type="button" id="selectPrompt" disabled><span data-lang="zh">全选文本</span><span data-lang="ja">全文を選択</span></button><button class="button" type="button" id="downloadPrompt" disabled><span data-lang="zh">下载MD</span><span data-lang="ja">MDを保存</span></button><button class="button primary" type="button" id="copyPrompt" disabled><span data-lang="zh">复制全文</span><span data-lang="ja">全文をコピー</span></button></div></div>
  </section>
  <section class="guide-section" id="guide" aria-labelledby="guideTitle">
    <div class="guide-heading"><div><h2 id="guideTitle"><span data-lang="zh">完整提示词 · 10章</span><span data-lang="ja">プロンプト全文 · 全10章</span></h2><p><span data-lang="zh">可逐章展开阅读；生成时会保留全部章节。</span><span data-lang="ja">章ごとに開いて読めます。生成時は全章が保持されます。</span></p></div><label class="chapter-search" for="chapterSearch"><span class="sr-only" data-lang="zh">搜索章节</span><span class="sr-only" data-lang="ja">章を検索</span><input id="chapterSearch" type="search" autocomplete="off" placeholder="搜索章节内容…" data-placeholder-zh="搜索章节内容…" data-placeholder-ja="章の内容を検索…"></label></div>
    <div class="guide-tools"><p class="search-status" id="searchStatus" role="status"><span data-lang="zh">显示全部10章</span><span data-lang="ja">全10章を表示</span></p><div class="actions"><button class="button quiet" type="button" id="expandAll"><span data-lang="zh">全部展开</span><span data-lang="ja">すべて開く</span></button><button class="button quiet" type="button" id="collapseAll"><span data-lang="zh">全部收起</span><span data-lang="ja">すべて閉じる</span></button></div></div>
    <div data-lang="zh" lang="zh-CN">@@ZH_CHAPTERS@@</div>
    <div data-lang="ja" lang="ja">@@JA_CHAPTERS@@</div>
  </section>
  <footer class="footer"><p><span data-lang="zh">P002 · 14项目追加核对<br>以实际资料、真实差分和可复查证据形成开发Input。</span><span data-lang="ja">P002 · 14案件追加照合<br>実資料、実差分、再確認できる証拠から開発Inputを作成します。</span></p><a href="@@SOURCE_NAME@@" download><span data-lang="zh">原始Markdown文件 ↗</span><span data-lang="ja">元のMarkdownファイル ↗</span></a></footer>
</main>
</div>
<script type="application/json" id="promptData">@@DATA@@</script>
<script>
@@SCRIPT@@
</script>
</body>
</html>
'''

if __name__ == '__main__':
    main()
