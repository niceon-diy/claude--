"""生成中日双语离线提示词。中日二言語のオフラインHTMLを生成する。"""

from __future__ import annotations

import html
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "P002_AI驱动开发工程智能体与Manual调查提示词.md"
OUTPUT = SOURCE.with_suffix(".html")


def inline(value: str) -> str:
    # 本文只使用受控的行内代码语法；一律先转义，保持代码及路径原文。
    return re.sub(r"`([^`]+)`", lambda m: "<code>" + m.group(1) + "</code>", html.escape(value))


def render_markdown(source: str) -> str:
    lines = source.strip().splitlines()
    blocks: list[str] = []
    position = 0
    while position < len(lines):
        line = lines[position].strip()
        if not line:
            position += 1
            continue
        heading = re.match(r"^(#{3,6})\s+(.+)$", line)
        if heading:
            level = len(heading.group(1))
            blocks.append(f"<h{level}>" + inline(heading.group(2)) + f"</h{level}>")
            position += 1
            continue
        if line.startswith("|"):
            table_lines = []
            while position < len(lines) and lines[position].strip().startswith("|"):
                table_lines.append(lines[position].strip())
                position += 1
            rows = [row.strip("|").split("|") for row in table_lines]
            head = "<thead><tr>" + "".join("<th>" + inline(c.strip()) + "</th>" for c in rows[0]) + "</tr></thead>"
            body = "<tbody>" + "".join("<tr>" + "".join("<td>" + inline(c.strip()) + "</td>" for c in row) + "</tr>" for row in rows[2:]) + "</tbody>"
            blocks.append('<div class="table-wrap" role="region" tabindex="0" aria-label="调查要求表格"><table>' + head + body + "</table></div>")
            continue
        list_match = re.match(r"^(?:- |\d+\. )(.+)$", line)
        if list_match:
            numbered = bool(re.match(r"^\d+\.", line))
            tag = "ol" if numbered else "ul"
            pattern = r"^\d+\. (.+)$" if numbered else r"^- (.+)$"
            items = []
            while position < len(lines):
                match = re.match(pattern, lines[position].strip())
                if not match:
                    break
                items.append("<li>" + inline(match.group(1)) + "</li>")
                position += 1
            blocks.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue
        paragraph = []
        while position < len(lines) and lines[position].strip():
            current = lines[position].strip()
            if paragraph and re.match(r"^(?:#{3,6} |\||- |\d+\. )", current):
                break
            paragraph.append(current)
            position += 1
        blocks.append("<p>" + inline(" ".join(paragraph)) + "</p>")
    return "\n".join(blocks)


raw = SOURCE.read_text(encoding="utf-8")
prompt = raw.split("<!-- PROMPT_START -->", 1)[1].split("<!-- PROMPT_END -->", 1)[0].strip()
japanese_prompt = raw.split("<!-- PROMPT_JA_START -->", 1)[1].split("<!-- PROMPT_JA_END -->", 1)[0].strip()
ja_parts = re.split(r"(?m)^## (.+)$", japanese_prompt)
ja_chapters = {}
for ja_index in range(1, len(ja_parts), 2):
    ja_title = ja_parts[ja_index]
    ja_number, ja_label = ja_title.split("｜", 1)
    ja_body = ja_parts[ja_index + 1].strip()
    ja_chapters[ja_number] = {"title":ja_label,"body":ja_body,"markdown":f"## {ja_title}\n\n{ja_body}"}
assert sorted(ja_chapters) == [f'{number:02d}' for number in range(1,13)], '日语章节应为01—12／日本語版は01〜12章が必要'
parts = re.split(r"(?m)^## (.+)$", prompt)
chapters = []
for index in range(1, len(parts), 2):
    title = parts[index]
    body = parts[index + 1].strip()
    number, label = title.split("｜", 1)
    chapters.append({"id": f"s{number}", "number": number, "title": label, "markdown": f"## {title}\n\n{body}", "body": body})

navigation = "\n".join(f'<a href="#{c["id"]}"><span>{c["number"]}</span><div><b data-language="zh">{html.escape(c["title"])}</b><b data-language="ja">{html.escape(ja_chapters[c["number"]]["title"])}</b></div></a>' for c in chapters)
chapter_html = []
for c in chapters:
    jp=ja_chapters[c['number']]
    c['japaneseMarkdown']=jp['markdown']
    chapter_html.append(f'''<details class="chapter" open id="{c['id']}">
      <summary><span class="chapter-number">{c['number']}</span><h2><span data-language="zh">{html.escape(c['title'])}</span><span data-language="ja">{html.escape(jp['title'])}</span></h2><span class="chevron" aria-hidden="true">⌄</span></summary>
      <div class="chapter-body"><div class="section-actions"><button class="text-button section-copy" data-section="{c['id']}" type="button">复制本节／この章をコピー</button></div><div class="language-columns"><div data-language="zh" lang="zh-CN"><p class="language-tag">中文 · 完整正文</p>{render_markdown(c['body'])}</div><div data-language="ja" lang="ja"><p class="language-tag">日本語 · 全文</p>{render_markdown(jp['body'])}</div></div></div>
    </details>''')

payload = json.dumps({"prompt": prompt,"japanese_prompt":japanese_prompt, "chapters": [{k: c[k] for k in ["id", "markdown", "japaneseMarkdown"]} for c in chapters]}, ensure_ascii=False).replace("<", "\\u003c").replace("&", "\\u0026")

template = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="description" content="结合Manual逐步调查AI智能体工程的完整中文提示词，覆盖基本设计、详细设计、开发、单体测试和连接测试。">
<title>P002 · AI 智能体与 Manual 调查提示词</title>
<style>
:root{--bg:#f4f6f8;--paper:#fff;--ink:#172a3a;--muted:#5c6e7c;--line:#dce4ea;--accent:#086a66;--accent-soft:#e7f3ef;--nav:#142c3b;--nav-muted:#a7bbc6;--amber:#785014;--amber-bg:#fbf4e6;--radius:17px}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:26px}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.85 "Segoe UI","Microsoft YaHei",system-ui,sans-serif}button,input,select{font:inherit}button,a,input,select{-webkit-tap-highlight-color:transparent}button{cursor:pointer}a{color:var(--accent)}button:focus-visible,a:focus-visible,summary:focus-visible,input:focus-visible,select:focus-visible,.table-wrap:focus-visible{outline:3px solid #d99d38;outline-offset:4px}button:disabled{cursor:default}::selection{background:#c8e8df} .app{display:grid;grid-template-columns:278px minmax(0,1fr);min-height:100vh}
.sidebar{position:sticky;top:0;height:100vh;overflow-y:auto;background:var(--nav);padding:32px 23px;color:#fff}.brand{font-weight:700;font-size:17px;letter-spacing:.02em;line-height:1.4}.brand small{display:block;color:var(--nav-muted);font-size:11px;font-weight:500;letter-spacing:.15em;margin-top:8px}.nav-caption{font-size:11px;color:var(--nav-muted);letter-spacing:.14em;margin:35px 12px 12px}.nav{display:grid;gap:4px}.nav a{display:flex;align-items:flex-start;gap:10px;text-decoration:none;color:#d9e3e9;padding:9px 10px;border-radius:8px;line-height:1.55;font-size:12px}.nav a span{font:11px/1.8 Consolas,monospace;opacity:.6;flex:none}.nav a:hover,.nav a.active{background:#294352;color:#fff}.nav a.active{box-shadow:inset 3px 0 #6ed4b8}.sidebar-note{margin:29px 11px 0;padding-top:20px;border-top:1px solid #38505e;color:var(--nav-muted);font-size:11px;line-height:1.9}.sidebar-note b{color:#d9e3e9;font-weight:500}.sidebar-home{display:block;margin:28px 11px 0;color:#c7dbd8;font-size:12px;text-decoration:none}
main{min-width:0;max-width:1300px;width:100%;padding:42px 52px 72px;margin:auto}.topline{display:flex;justify-content:space-between;align-items:center;gap:16px;color:var(--muted);font-size:12px;margin-bottom:33px}.eyebrow{color:var(--accent);font-size:11px;letter-spacing:.13em;font-weight:700}.offline{display:flex;gap:8px;align-items:center}.dot{width:7px;height:7px;border-radius:50%;background:var(--accent);display:inline-block}.hero h1{font-size:clamp(30px,3.3vw,46px);line-height:1.3;letter-spacing:-.035em;margin:12px 0 18px;font-weight:700}.hero h1 em{font-style:normal;color:var(--accent)}.intro{max-width:760px;color:var(--muted);font-size:15px;line-height:1.9;margin:0}.stats{display:flex;flex-wrap:wrap;gap:20px;margin:23px 0 26px}.stats span{font-size:12px;color:var(--muted)}.stats b{font-size:16px;font-weight:700;color:var(--ink);padding-right:5px}.notice{background:var(--amber-bg);border:1px solid #eadfc6;border-left:3px solid #c39545;color:var(--amber);font-size:12px;padding:12px 16px;border-radius:8px;line-height:1.8}.phase-track{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));margin:25px 0 30px;border:1px solid var(--line);border-radius:12px;background:#fff;overflow:hidden}.phase{padding:15px 14px;position:relative}.phase+.phase{border-left:1px solid var(--line)}.phase small{display:block;font:10px/1.6 Consolas,monospace;color:var(--muted);letter-spacing:.05em}.phase b{display:block;font-size:13px;font-weight:650;margin-top:3px}.phase span{font-size:11px;color:var(--muted)}
.setup{padding:26px 28px;background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);box-shadow:0 5px 20px #19344704}.panel-head{display:flex;justify-content:space-between;gap:15px;align-items:center}.panel-head h2{margin:0;font-size:19px;line-height:1.5}.step-pill{font:10px/1.5 Consolas,monospace;color:var(--accent);background:var(--accent-soft);padding:5px 9px;border-radius:5px;white-space:nowrap}.setup-desc{margin:8px 0 21px;color:var(--muted);font-size:12px}.fields{display:grid;grid-template-columns:1fr 1fr;gap:16px 20px}.field label{display:block;margin-bottom:6px;font-size:12px;font-weight:600}.field label span{color:var(--muted);font-weight:400;font-size:11px;margin-left:5px}.field input,.field select{display:block;width:100%;border:1px solid #ccd7de;background:#fbfcfd;border-radius:7px;padding:10px 12px;color:var(--ink);font-size:12px;min-height:43px}.field input::placeholder{color:#82919c}.field input:focus,.field select:focus{border-color:var(--accent);background:#fff}.setup-actions{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:24px;padding-top:20px;border-top:1px solid var(--line);flex-wrap:wrap}.setup-actions p{color:var(--muted);font-size:11px;margin:0;max-width:380px}.primary{background:var(--accent);border:1px solid var(--accent);color:#fff;border-radius:8px;padding:11px 18px;font-size:12px;font-weight:600;line-height:1.6;box-shadow:0 3px 6px #086a6618}.primary:hover{background:#075954}.secondary{background:#fff;border:1px solid var(--line);color:var(--ink);border-radius:7px;padding:8px 13px;font-size:12px;line-height:1.6}.secondary:hover{background:#f2f6f6}.button-group{display:flex;gap:9px;align-items:center;flex-wrap:wrap}.text-button{border:0;background:transparent;color:var(--accent);padding:5px;font-size:11px}.text-button:hover{text-decoration:underline}.workflow-note{font-size:12px;color:var(--muted);padding:18px 3px 0;line-height:1.9}.workflow-note strong{color:var(--ink);font-weight:600}
.document-tools{display:flex;justify-content:space-between;align-items:center;gap:14px;margin:36px 0 16px;flex-wrap:wrap}.document-tools h2{font-size:19px;margin:0;line-height:1.6}.document-tools small{display:block;color:var(--muted);font-size:11px;font-weight:400;margin-top:3px}.search{max-width:290px;width:100%;position:relative}.search input{width:100%;padding:9px 13px 9px 33px;border:1px solid var(--line);border-radius:8px;background:#fff;font-size:12px}.search svg{position:absolute;top:13px;left:11px;width:14px;height:14px;stroke:var(--muted);fill:none;stroke-width:1.7}.filter-meta{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:13px;color:var(--muted);font-size:11px}.filter-meta .button-group{gap:12px}.chapter{background:var(--paper);border:1px solid var(--line);border-radius:13px;margin:0 0 15px;scroll-margin-top:22px;overflow:hidden}.chapter summary{list-style:none;display:flex;align-items:center;gap:13px;cursor:pointer;padding:20px 25px;min-height:76px}.chapter summary::-webkit-details-marker{display:none}.chapter summary h2{font-size:17px;line-height:1.55;margin:0;flex:1;font-weight:650}.chapter-number{font:12px/1.5 Consolas,monospace;color:var(--accent);background:var(--accent-soft);padding:5px 7px;border-radius:5px}.chevron{font-size:20px;color:#7b8c98;transition:transform .15s;line-height:1}.chapter[open] .chevron{transform:rotate(180deg)}.chapter[open] summary{border-bottom:1px solid #e6ecef}.chapter-body{padding:13px 27px 28px;font-size:13px;line-height:1.95;overflow-wrap:anywhere}.section-actions{display:flex;justify-content:flex-end;margin-bottom:8px}.chapter-body h3{font-size:15px;margin:29px 0 12px;line-height:1.6;border-left:3px solid var(--accent);padding-left:11px}.chapter-body p{margin:12px 0}.chapter-body ul,.chapter-body ol{margin:12px 0;padding-left:23px}.chapter-body li{padding-left:4px;margin:9px 0}.chapter-body code{font:11.5px/1.7 Consolas,"Microsoft YaHei",monospace;padding:2px 5px;background:#eff4f6;border:1px solid #e5ecef;border-radius:4px;color:#25495a;white-space:pre-wrap;overflow-wrap:anywhere}.table-wrap{max-width:100%;overflow:auto;border:1px solid var(--line);border-radius:8px;margin:17px 0}.table-wrap table{width:100%;border-collapse:collapse;min-width:510px;font-size:12px;line-height:1.85;text-align:left}.table-wrap th{background:#eef4f4;color:#244742;padding:12px 13px;font-weight:600;vertical-align:top;border-bottom:1px solid var(--line)}.table-wrap td{padding:12px 13px;vertical-align:top;border-bottom:1px solid #e7edf0}.table-wrap tr:last-child td{border-bottom:0}.table-wrap tbody tr:nth-child(even){background:#fafcfc}.table-wrap th:first-child,.table-wrap td:first-child{min-width:110px;width:21%;font-weight:600}.chapter[hidden]{display:none}.empty{display:none;text-align:center;padding:35px;color:var(--muted);background:#fff;border-radius:12px;border:1px dashed var(--line)}.footer{margin-top:32px;padding-top:22px;border-top:1px solid var(--line);color:var(--muted);font-size:11px;display:flex;justify-content:space-between;gap:16px;line-height:1.9}.footer a{color:var(--muted)}.toast{position:fixed;left:50%;bottom:26px;transform:translate(-50%,18px);opacity:0;background:#142c3b;color:#fff;border-radius:10px;padding:12px 19px;font-size:12px;box-shadow:0 6px 28px #17334330;pointer-events:none;transition:.18s;z-index:10;max-width:90vw;text-align:center}.toast.show{opacity:1;transform:translate(-50%,0)}dialog{border:1px solid var(--line);border-radius:14px;padding:24px;max-width:800px;width:90vw;box-shadow:0 20px 80px #122a3940}dialog::backdrop{background:#172a3a66}dialog h2{margin:0 0 10px;font-size:20px}dialog p{font-size:12px;color:var(--muted)}dialog textarea{display:block;width:100%;height:48vh;border:1px solid var(--line);border-radius:8px;padding:12px;resize:vertical;font:12px/1.7 Consolas,"Microsoft YaHei",monospace;color:var(--ink)}dialog .button-group{justify-content:flex-end;margin-top:14px}.noscript{padding:14px 20px;border:1px solid #eadfc6;background:var(--amber-bg);color:var(--amber);border-radius:8px;font-size:12px;margin-top:16px}
@media(min-width:1600px){main{padding-left:72px;padding-right:72px}.sidebar{padding-left:27px;padding-right:27px}}
@media(max-width:1100px){.app{grid-template-columns:230px minmax(0,1fr)}main{padding:30px 30px 55px}.sidebar{padding:28px 16px}.nav a{font-size:11px}.phase{padding:12px 9px}.phase span{font-size:10px}.fields{gap:14px}.setup{padding:23px}.chapter-body{padding:12px 22px 25px}.hero h1{font-size:35px}}
@media(max-width:820px){.app{display:block}.sidebar{position:relative;height:auto;padding:20px 22px}.brand{font-size:15px}.brand small{display:none}.nav-caption,.sidebar-note,.sidebar-home{display:none}.nav{display:flex;overflow-x:auto;gap:7px;margin-top:14px;padding-bottom:5px}.nav a{flex:none;white-space:nowrap;background:#233d4c;padding:8px 10px}.nav a span{display:none}main{padding:24px 22px 44px}.topline{margin-bottom:24px}.hero h1{font-size:34px}.hero h1 br{display:none}.fields{grid-template-columns:1fr 1fr}.phase span{display:none}.phase b{font-size:12px}.chapter summary{padding:17px 19px;gap:10px}.chapter summary h2{font-size:16px}.footer{flex-direction:column;gap:6px}}
@media(max-width:520px){main{padding-left:16px;padding-right:16px}.hero h1{font-size:30px}.intro{font-size:13px}.stats{gap:12px}.stats span{font-size:11px}.offline{font-size:10px}.phase-track{margin-top:19px}.phase{padding:10px 7px}.phase small{font-size:9px}.phase b{font-size:11px}.setup{padding:20px 17px}.fields{grid-template-columns:1fr;gap:13px}.setup-actions .button-group{width:100%}.setup-actions .primary{flex:1}.document-tools{gap:12px}.search{max-width:none}.chapter-body{padding:10px 17px 23px;font-size:12.5px}.chapter summary h2{font-size:15px}.chapter-number{font-size:11px}.filter-meta{font-size:10px}.notice{font-size:11px}.topline{gap:7px}.eyebrow{font-size:10px}}
@media print{@page{size:A4;margin:16mm 13mm}html{scroll-behavior:auto}body{background:#fff;font-size:10pt}.app{display:block}.sidebar,.setup,.document-tools,.filter-meta,.section-actions,.toast,dialog,.noscript,.workflow-note,.topline,.notice{display:none!important}main{max-width:none;padding:0;margin:0}.hero h1{font-size:25pt;margin-top:0}.intro{font-size:10pt}.stats{margin:12px 0}.phase-track{margin:14px 0 20px}.phase{padding:8px}.chapter{border:0;border-radius:0;overflow:visible;margin-bottom:17px}.chapter summary{padding:12px 0 7px;border-bottom:1px solid #ccc!important;break-after:avoid;min-height:0}.chapter summary h2{font-size:15pt}.chapter-number{padding:2px 5px;font-size:10pt}.chevron{display:none}.chapter-body{padding:5px 0 0;font-size:9.5pt;line-height:1.7}.chapter-body h3{font-size:11pt;break-after:avoid;margin-top:19px}.chapter-body li{margin:7px 0}.table-wrap{overflow:visible;border:0;border-radius:0}.table-wrap table{min-width:0;font-size:9pt}.table-wrap th,.table-wrap td{padding:7px;border:1px solid #ccc}.table-wrap tr{break-inside:avoid}.chapter-body code{font-size:8pt;white-space:pre-wrap}.footer{font-size:8pt}.chapter[hidden]{display:block!important}.empty{display:none!important}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
</style>
</head>
<body>
<div class="app">
<aside class="sidebar" aria-label="调查提示词目录">
  <div class="brand">AI 工程调查手册<small>PROMPT LIBRARY / P002</small></div>
  <div class="nav-caption">12 个模块 · 按顺序执行</div>
  <nav class="nav" id="nav">{{NAV}}</nav>
  <div class="sidebar-note"><b>核心调查链路</b><br>谁启动 → 读什么 → 怎么处理<br>→ 产出什么 → 谁检查 → 交给谁<br><br>每个结论都回到 Manual、代码、配置和已有运行证据。</div>
  <a class="sidebar-home" href="#setup">↑ 返回路径填写区</a>
</aside>
<main id="top">
  <div class="topline"><span class="eyebrow">INVESTIGATION PROMPT / 01</span><span class="offline"><i class="dot"></i>离线文件 · 无外部依赖</span></div>
  <header class="hero">
    <div class="eyebrow">给零基础读者的工程调查提示词</div>
    <h1>看懂每个智能体<br><em>如何一步步完成开发</em></h1>
    <p class="intro">结合 Manual，从基本设计到连接测试，查清每个智能体参照哪些资料、代码怎样实现，以及输出如何交给下一步。填写路径后，把完整提示词交给能读取公司工程的 AI 助手。</p>
    <div class="stats"><span><b>5</b>个开发阶段</span><span><b>6</b>步基础调查</span><span><b>12</b>个提示词模块</span><span><b>1</b>条真实功能链路</span></div>
  </header>
  <div class="notice"><strong>这是可执行的调查提示词，不是公司工程的调查结论。</strong> 当前目录为开发环境模板及参考资料；实际调查应在公司工程和 Manual 可访问的环境执行。无需填写或粘贴密钥。</div>
  <div class="phase-track" aria-label="五个调查阶段">
    <div class="phase"><small>01 / DESIGN</small><b>基本设计</b><span>需求如何成为设计</span></div>
    <div class="phase"><small>02 / DETAIL</small><b>详细设计</b><span>设计如何落实到模块</span></div>
    <div class="phase"><small>03 / CODE</small><b>开发</b><span>代码怎样生成与修改</span></div>
    <div class="phase"><small>04 / UNIT</small><b>单体测试</b><span>单元怎样被验证</span></div>
    <div class="phase"><small>05 / INTEGRATE</small><b>连接测试</b><span>组件怎样联接验证</span></div>
  </div>
  <section class="setup" id="setup" aria-labelledby="setup-title">
    <div class="panel-head"><h2 id="setup-title">先填写调查对象</h2><span class="step-pill">STEP 00</span></div>
    <p class="setup-desc">填写值会在复制或下载时自动替换提示词中的占位符。此页面不会读取工程、执行命令或上传数据，填写内容仅保留在当前页面内存。</p>
    <div class="fields">
      <div class="field"><label for="projectRoot">公司工程根目录<span>最重要</span></label><input id="projectRoot" type="text" autocomplete="off" spellcheck="false" placeholder="例如 D:\Company\AI-Development"></div>
      <div class="field"><label for="manualRoot">Manual／手册位置<span>可留空自动查找</span></label><input id="manualRoot" type="text" autocomplete="off" spellcheck="false" placeholder="文件路径、目录或已连接的文档链接"></div>
      <div class="field"><label for="referenceRoot">其他设计和参考资料<span>可选</span></label><input id="referenceRoot" type="text" autocomplete="off" spellcheck="false" placeholder="需求、设计书、测试规范、历史案例等位置"></div>
      <div class="field"><label for="sampleFeature">优先追踪的真实功能<span>可自动选择</span></label><input id="sampleFeature" type="text" autocomplete="off" spellcheck="false" placeholder="需求编号、任务编号或一个具体功能名称"></div>
      <div class="field"><label for="outputRoot">调查报告保存目录<span>可留空使用工程下的“调查结果”</span></label><input id="outputRoot" type="text" autocomplete="off" spellcheck="false" placeholder="例如 D:\Company\AI-Development\调查结果"></div>
      <div class="field"><label for="outputFormat">让调查助手交付的阅读版<span>不是当前文件格式</span></label><select id="outputFormat"><option value="HTML">HTML（默认，另附 MD 和 JSON）</option><option value="Excel">Excel（另附 MD 和 JSON）</option><option value="HTML 和 Excel 两者">HTML 和 Excel 两者（另附 MD 和 JSON）</option></select></div>
    </div>
    <div class="setup-actions"><p>复制的是全部 12 个模块。路径留空时保留工程占位符，其余未知资料按提示词要求查找。</p><div class="button-group"><button class="secondary" type="button" id="downloadPrompt">下载 .md</button><button class="primary" type="button" id="copyPrompt">复制完整调查提示词</button></div></div>
  </section>
  <div class="workflow-note"><strong>使用顺序：</strong>填写工程路径 → 复制完整提示词 → 在公司工程可读取的环境交给 AI 助手 → 按证据编号阅读生成的调查报告。下方正文保持原始模板，复制时才替换输入值。</div>
  <noscript><div class="noscript">浏览器未启用 JavaScript。下方提示词正文仍可完整阅读和手动复制；请自行替换第01节的路径。</div></noscript>
  <div class="document-tools"><h2>完整调查提示词<small>可展开阅读 · 也可复制单节用于后续补查</small></h2><label class="search"><svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5"></circle><path d="m13 13 4.5 4.5"></path></svg><input id="search" type="search" aria-label="搜索提示词章节" placeholder="搜索章节，例如：连接测试、资料、失败"></label></div>
  <div class="filter-meta"><span id="searchStatus" aria-live="polite">显示全部 12 个模块</span><div class="button-group"><button class="text-button" type="button" id="expandAll">全部展开</button><button class="text-button" type="button" id="collapseAll">收起正文</button><button class="text-button" type="button" id="printDocument">打印／另存为 PDF</button></div></div>
  <div id="chapters">{{CHAPTERS}}</div>
  <div class="empty" id="emptyState">未找到相关模块。换一个关键词，或清空搜索框查看全部内容。</div>
  <footer class="footer"><span>P002 · 版本 1.0 · 2026-11-01<br>完整正文约 {{COUNT}} 字符 · 以同名 Markdown 为维护来源</span><span>默认只读调查 · 事实与推断分开<br><a href="#top">返回顶部 ↑</a></span></footer>
</main>
</div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<dialog id="copyDialog" aria-labelledby="copy-title"><h2 id="copy-title">手动复制提示词</h2><p>浏览器未允许自动复制。下方已选中全部内容，请按 Ctrl+C（macOS 按 ⌘C），然后粘贴给调查助手。</p><textarea id="manualCopy" readonly aria-label="完整提示词文本"></textarea><div class="button-group"><button class="secondary" type="button" id="closeCopyDialog">关闭</button></div></dialog>
<script type="application/json" id="promptData">{{DATA}}</script>
<script>
'use strict';
const data = JSON.parse(document.getElementById('promptData').textContent);
const chapters = [...document.querySelectorAll('.chapter')];
const byId = id => document.getElementById(id);
const valueOf = id => byId(id).value.trim();
let toastTimer;
function notify(message) {
  byId('toast').textContent = message;
  byId('toast').classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => byId('toast').classList.remove('show'), 3400);
}
function configuredPrompt(text) {
  const root = valueOf('projectRoot');
  const output = valueOf('outputRoot') || (root ? root.replace(/[\\/]+$/, '') + (root.includes('\\') ? '\\' : '/') + '调查结果' : '【填写：输出目录】');
  const replacements = [
    ['【填写：公司工程根目录】', root || '【填写：公司工程根目录】'],
    ['【填写：Manual位置；不知道则自动查找】', valueOf('manualRoot') || '自动查找与此工程版本对应的 Manual／手册'],
    ['【填写：补充资料位置；没有则自动查找关联引用】', valueOf('referenceRoot') || '自动查找工程实际关联的设计、规范、样例和其他引用'],
    ['【填写：样例功能；没有则从工程选择一个】', valueOf('sampleFeature') || '从工程选择一个资料较完整的真实功能，并说明理由'],
    ['【填写：输出目录】', output],
    ['【填写：HTML／Excel／两者；默认HTML】', valueOf('outputFormat')]
  ];
  for (const [placeholder, replacement] of replacements) text = text.split(placeholder).join(replacement.replaceAll('|', '／').replace(/[\r\n]+/g, ' '));
  return text;
}
async function copyText(text) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch (_) { /* file: 页面可能不授予 Clipboard API 权限，继续本地回退 */ }
  const field = document.createElement('textarea');
  field.value = text; field.style.position = 'fixed'; field.style.opacity = '0';
  document.body.appendChild(field); field.focus(); field.select();
  let copied = false;
  try { copied = document.execCommand('copy'); } catch (_) { copied = false; }
  field.remove();
  if (!copied) {
    byId('manualCopy').value = text;
    byId('copyDialog').showModal();
    byId('manualCopy').focus(); byId('manualCopy').select();
  }
  return copied;
}
byId('copyPrompt').addEventListener('click', async () => {
  if (await copyText(configuredPrompt(data.prompt))) notify(valueOf('projectRoot') ? '已复制全部 12 个模块，并替换填写内容' : '已复制全部提示词；请补充公司工程根目录');
});
byId('downloadPrompt').addEventListener('click', () => {
  const blob = new Blob(['\ufeff' + configuredPrompt(data.prompt) + '\n'], {type:'text/markdown;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'AI智能体与Manual调查_已填写提示词.md';
  document.body.appendChild(anchor); anchor.click(); anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
  notify('已请求下载填写后的 Markdown 提示词');
});
document.querySelectorAll('.section-copy').forEach(button => button.addEventListener('click', async () => {
  const section = data.chapters.find(c => c.id === button.dataset.section);
  if (await copyText(configuredPrompt(section.markdown))) notify('已复制本节；首次调查请使用完整提示词');
}));
byId('closeCopyDialog').addEventListener('click', () => byId('copyDialog').close());
function filterChapters() {
  const query = byId('search').value.trim().toLocaleLowerCase();
  let count = 0;
  chapters.forEach(chapter => {
    const match = !query || chapter.textContent.toLocaleLowerCase().includes(query);
    chapter.hidden = !match;
    if (match) { count++; if (query) chapter.open = true; }
  });
  byId('searchStatus').textContent = query ? `找到 ${count} / ${chapters.length} 个相关模块` : `显示全部 ${chapters.length} 个模块`;
  byId('emptyState').style.display = count ? 'none' : 'block';
}
byId('search').addEventListener('input', filterChapters);
byId('expandAll').addEventListener('click', () => chapters.forEach(chapter => { if (!chapter.hidden) chapter.open = true; }));
byId('collapseAll').addEventListener('click', () => chapters.forEach(chapter => { if (!chapter.hidden) chapter.open = false; }));
document.querySelectorAll('a[href^="#s"]').forEach(link => link.addEventListener('click', () => {
  const target = byId(link.hash.slice(1));
  if (!target) return;
  if (byId('search').value) { byId('search').value = ''; filterChapters(); }
  if (target.classList.contains('chapter')) target.open = true;
}));
let printState = null;
function preparePrint() {
  if (printState) return;
  printState = chapters.map(chapter => ({open:chapter.open, hidden:chapter.hidden}));
  chapters.forEach(chapter => { chapter.hidden = false; chapter.open = true; });
}
function restorePrint() {
  if (!printState) return;
  chapters.forEach((chapter,index) => { chapter.open = printState[index].open; chapter.hidden = printState[index].hidden; });
  printState = null;
}
window.addEventListener('beforeprint', preparePrint);
window.addEventListener('afterprint', restorePrint);
byId('printDocument').addEventListener('click', () => { preparePrint(); window.print(); });
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    const active = entries.filter(entry => entry.isIntersecting).sort((a,b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
    if (!active) return;
    document.querySelectorAll('.nav a').forEach(link => { const selected = link.hash === '#' + active.target.id; link.classList.toggle('active', selected); if (selected) link.setAttribute('aria-current','location'); else link.removeAttribute('aria-current'); });
  }, {rootMargin:'-5% 0px -65% 0px',threshold:0});
  chapters.forEach(chapter => observer.observe(chapter));
}
</script>
</body>
</html>
'''

# 阅读和复制均可选完整中文、日文或两者。表示・コピー言語を選択できる。
ui_pairs = {
    'P002 · AI 智能体与 Manual 调查提示词':'P002 · AI 智能体与 Manual 调查／AIエージェントとManualの調査',
    'AI 工程调查手册':'AI 工程调查／AI工程の調査',
    '12 个模块 · 按顺序执行':'12 个模块／12の調査項目',
    '离线文件 · 无外部依赖':'离线可用／オフライン対応',
    '给零基础读者的工程调查提示词':'初学者调查提示词／初心者向け調査プロンプト',
    '如何一步步完成开发':'如何一步步完成开发／開発の進め方',
    '先填写调查对象':'填写调查对象／調査対象を入力',
    '公司工程根目录':'公司工程根目录／会社工程のルート',
    'Manual／手册位置':'Manual 位置／Manualの場所',
    '其他设计和参考资料':'其他资料／その他の資料',
    '优先追踪的真实功能':'真实功能／実際の機能',
    '调查报告保存目录':'报告保存目录／報告の保存先',
    '让调查助手交付的阅读版':'报告格式／調査報告の形式',
    '最重要':'必填／必須',
    '可留空自动查找':'可自动查找／自動検索可',
    '可自动选择':'可自动选择／自動選択可',
    '可选':'可选／任意',
    '可留空使用工程下的“调查结果”':'留空使用工程下的“调查结果”／未入力時は工程配下の「调查结果」',
    '不是当前文件格式':'不是当前文件格式／このHTML自体の形式ではありません',
    '下载 .md':'下载 MD／MD保存',
    '复制完整调查提示词':'全文复制／全文をコピー',
    '完整调查提示词':'完整提示词／プロンプト全文',
    '可展开阅读 · 也可复制单节用于后续补查':'中日两种语言均为全文，可独立使用／両言語とも全文で、単独使用できます',
    '全部展开':'展开／展開',
    '收起正文':'收起／折り畳む',
    '打印／另存为 PDF':'打印／印刷・PDF',
    '显示全部 12 个模块':'显示12章／全12章',
    '未找到相关模块。换一个关键词，或清空搜索框查看全部内容。':'未找到相关章节，请换关键词／該当する章がありません。検索語を変更してください。',
    '手动复制提示词':'手动复制／手動コピー',
    '浏览器未允许自动复制。下方已选中全部内容，请按 Ctrl+C（macOS 按 ⌘C），然后粘贴给调查助手。':'浏览器未允许自动复制。请按Ctrl+C复制已选内容。／自動コピーが許可されていません。選択済みの内容をCtrl+Cでコピーしてください。',
    '关闭</button>':'关闭／閉じる</button>',
    '返回顶部 ↑':'回到顶部／先頭へ ↑',
    '↑ 返回路径填写区':'↑ 路径填写／パス入力へ',
    '默认只读调查 · 事实与推断分开':'只读调查，事实与推断分开／読取り調査・事実と推測を区別',
    '完整正文约 {{COUNT}} 字符':'中文 {{COUNT}} 字符／日本語 '+f'{len(japanese_prompt):,}'+' 文字',
    '以同名 Markdown 为维护来源':'MD统一维护／同名MDから生成',
    '版本 1.0 · 2026-11-01':'中日双语版 · 2026-11-02',
    '基本设计</b>':'基本设计／基本設計</b>',
    '详细设计</b>':'详细设计／詳細設計</b>',
    '开发</b>':'开发／開発</b>',
    '单体测试</b>':'单体测试／単体テスト</b>',
    '连接测试</b>':'连接测试／結合テスト</b>',
    '已复制本节；首次调查请使用完整提示词':'已复制本节／この章をコピーしました',
    '已复制全部 12 个模块，并替换填写内容':'已复制全部12章并反映输入／全12章を入力値付きでコピーしました',
    '已复制全部提示词；请补充公司工程根目录':'已复制全文，请填写公司工程路径／全文をコピーしました。会社工程のパスを記入してください',
    '已请求下载填写后的 Markdown 提示词':'已请求下载／ダウンロードを開始しました',
    '搜索章节，例如：连接测试、资料、失败':'搜索／検索：Manual、测试、例外…',
}
for original, bilingual in ui_pairs.items():
    template = template.replace(original,bilingual)
# UI标签翻译不改变协议占位符。UI訳で置換キーを変更しない。
template=template.replace('【填写：公司工程根目录／会社工程のルート】','【填写：公司工程根目录】')
template=template.replace('<body>','<body data-mode="both">')
template=template.replace('</header>','<p class="intro" lang="ja">Manualと照らし、基本設計から結合テストまで、各エージェントの参照資料、実装、成果、確認と手戻りを調査します。中日両版は同じ依頼で、作業は一度だけ実行します。</p></header>',1)
template=template.replace('这是可执行的调查提示词，不是公司工程的调查结论。','这是调查模板，不是公司工程结论。／調査テンプレートであり、会社工程の調査結果ではありません。')
template=template.replace('当前目录为开发环境模板及参考资料；实际调查应在公司工程和 Manual 可访问的环境执行。无需填写或粘贴密钥。','实际调查需在公司工程与Manual可访问的环境执行，无需填入密钥。／会社工程とManualへアクセスできる環境で実行し、認証情報は入力しないでください。')
template=template.replace('填写值会在复制或下载时自动替换提示词中的占位符。此页面不会读取工程、执行命令或上传数据，填写内容仅保留在当前页面内存。','复制或下载时反映输入值；本页不读取、执行或上传工程。／コピー・保存時に入力値を反映します。工程の読取り・実行・送信は行わず、入力は現在のページ内だけに保持します。')
template=template.replace('复制的是全部 12 个模块。路径留空时保留工程占位符，其余未知资料按提示词要求查找。','按下方所选语言复制完整12章。／下で選んだ言語の全12章をコピーします。')
template=template.replace('填写工程路径 → 复制完整提示词 → 在公司工程可读取的环境交给 AI 助手 → 按证据编号阅读生成的调查报告。下方正文保持原始模板，复制时才替换输入值。','填写工程路径并选择语言 → 复制全文 → 在公司环境交给AI。／工程パスと言語を選択 → 全文をコピー → 会社の実行環境でAIへ渡します。本文の入力値はコピー時に反映されます。')
template=template.replace('浏览器未启用 JavaScript。下方提示词正文仍可完整阅读和手动复制；请自行替换第01节的路径。','未启用JavaScript时仍可阅读与手动复制，请自行填写路径。／JavaScript無効時も全文を読んで手動コピーできます。パスは自分で記入してください。')
language_controls='''<section class="language-controls" aria-label="阅读和复制语言／表示・コピー言語"><b>阅读与复制语言／表示・コピー言語</b><div role="group"><button type="button" data-language-mode="both" aria-pressed="true">中日对照／中日併記</button><button type="button" data-language-mode="zh" aria-pressed="false">中文</button><button type="button" data-language-mode="ja" aria-pressed="false">日本語</button></div></section>'''
template=template.replace('<div class="document-tools">',language_controls+'<div class="document-tools">',1)
language_css='''
.nav b{display:block;font-weight:400}.nav b[data-language=ja]{font-size:10px;color:#acc5ce}.language-controls{margin-top:28px;padding:17px 20px;border:1px solid var(--line);border-radius:10px;background:#fff;display:flex;justify-content:space-between;gap:15px;align-items:center;flex-wrap:wrap}.language-controls b{font-size:12px}.language-controls div{display:flex;border:1px solid #a7c5bc;border-radius:7px;overflow:hidden}.language-controls button{background:#fff;border:0;color:var(--accent);padding:9px 12px;font-size:11px}.language-controls button+button{border-left:1px solid #cdded7}.language-controls button[aria-pressed=true]{background:var(--accent);color:#fff}.chapter summary h2>span{display:block}.chapter summary h2>[data-language=ja]{font-size:13px;font-weight:500;color:var(--muted)}.language-columns{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:25px}.language-columns>div{min-width:0}.language-columns>[data-language=ja]{border-left:1px solid var(--line);padding-left:25px;font-family:"Yu Gothic","Meiryo","Segoe UI",sans-serif}.language-tag{color:var(--accent);font-size:11px;letter-spacing:.05em}.language-columns .table-wrap table{min-width:410px}body[data-mode=zh] [data-language=ja],body[data-mode=ja] [data-language=zh]{display:none!important}body:not([data-mode=both]) .language-columns{display:block}body:not([data-mode=both]) .language-columns>[data-language=ja]{border:0;padding:0}body[data-mode=ja] .chapter summary h2>[data-language=ja]{font-size:17px;color:var(--ink);font-weight:600}body[data-mode=ja] .nav b[data-language=ja]{color:#d9e3e9;font-size:12px}@media(max-width:1450px){.language-columns{display:block}.language-columns>[data-language=ja]{border-left:0;border-top:1px solid var(--line);padding:15px 0 0;margin-top:25px}}@media(max-width:820px){body[data-mode=both] .nav b[data-language=ja]{display:none}.language-controls{padding:15px}.language-controls button{padding:9px}.chapter summary h2>[data-language=ja]{font-size:11px}}@media print{.language-controls{display:none!important}.language-columns{display:block}.language-columns>[data-language=ja]{border-left:0;border-top:1px dashed #aaa;padding:12px 0 0;margin-top:15px}}
'''
template=template.replace('</style>',language_css+'</style>')
template=template.replace('configuredPrompt(data.prompt)','selectedPrompt()').replace('configuredPrompt(section.markdown)','selectedPrompt(section)')
bilingual_script=r'''
<script>
function japaneseConfigured(text){
 const root=valueOf('projectRoot');
 const output=valueOf('outputRoot')||(root?root.replace(/[\\/]+$/,'')+(root.includes('\\')?'\\':'/')+'调查结果':'{{OUTPUT_DIR}}');
 const values={PROJECT_ROOT:root||'{{PROJECT_ROOT}}',MANUAL_PATH:valueOf('manualRoot')||'工程の有効版に対応するManualを自動検索',REFERENCE_PATHS:valueOf('referenceRoot')||'実際に関係する設計・規約・例を自動検索',SAMPLE_FEATURE:valueOf('sampleFeature')||'資料の揃う実機能を選択し理由を説明',OUTPUT_DIR:output,OUTPUT_FORMAT:valueOf('outputFormat').replace('HTML 和 Excel 两者','HTML + Excel')};
 for(const [key,value] of Object.entries(values))text=text.split('{{'+key+'}}').join(value.replaceAll('|','／').replace(/[\r\n]+/g,' '));
 return text;
}
function selectedPrompt(section){
 const mode=document.body.dataset.mode||'both';
 const zh=configuredPrompt(section?section.markdown:data.prompt);
 const ja=japaneseConfigured(section?section.japaneseMarkdown:data.japanese_prompt);
 if(mode==='zh')return zh;
 if(mode==='ja')return ja;
 return '以下中文与日文是同一任务的两个版本，只执行一次；发现语言差异时请记录并确认。\n以下の中国語版と日本語版は同じ依頼です。作業は一度だけ実行し、相違があれば記録して確認してください。\n\n# 中文\n\n'+zh+'\n\n---\n\n# 日本語\n\n'+ja;
}
document.querySelectorAll('[data-language-mode]').forEach(button=>button.addEventListener('click',()=>{
 document.body.dataset.mode=button.dataset.languageMode;
 document.documentElement.lang=button.dataset.languageMode==='ja'?'ja':'zh-CN';
 document.querySelectorAll('[data-language-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
}));
</script>
'''
template=template.replace('</body>',bilingual_script+'</body>')
page = template.replace("{{NAV}}", navigation).replace("{{CHAPTERS}}", "\n".join(chapter_html)).replace("{{COUNT}}", f"{len(prompt):,}").replace("{{DATA}}", payload)
OUTPUT.write_text(page, encoding="utf-8")
print(json.dumps({"source": str(SOURCE), "output": str(OUTPUT), "chapters": len(chapters), "zh_characters": len(prompt),"ja_characters":len(japanese_prompt), "html_bytes": OUTPUT.stat().st_size}, ensure_ascii=False))
