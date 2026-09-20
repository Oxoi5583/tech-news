#!/usr/bin/env python3
"""Build a static reading notebook. Requires Python 3.10+, Markdown and PyYAML."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
import hashlib
from html import escape, unescape
from html.parser import HTMLParser
import math
import json
import os
from pathlib import Path, PurePosixPath
import re
from string import Template
import sys
from urllib.parse import quote, unquote, urlsplit, urlunsplit

try:
    import markdown
    import yaml
except ImportError:
    sys.exit("缺少依賴，請先執行：python -m pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent
MANIFEST = ".tech-news-manifest.json"
LABELS = {"rendering": "渲染", "simulation": "模擬", "animation": "動畫",
          "ai": "人工智能", "systems": "系統與引擎架構", "technology": "科技",
          "game-design": "遊戲設計", "culture": "文化與創作",
          "society": "社會", "philosophy": "哲學與思想"}
TYPES = {"paper": "技術論文", "article": "深度文章"}
RESERVED = {"tags", "types", "_static"}


def relative_url(target: Path, page: Path) -> str:
    return quote(Path(os.path.relpath(target, page.parent)).as_posix(), safe="/.-_")


def tag_path(tag: str) -> Path:
    slug = tag if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", tag) else (
        "tag-" + hashlib.sha256(tag.encode("utf-8")).hexdigest()[:16])
    return Path("tags") / slug / "index.html"


def load_entry(path: Path, source: Path) -> dict:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path}: 缺少 YAML metadata（開頭必須是 ---）")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise ValueError(f"{path}: YAML metadata 缺少結束的 ---")
    try:
        meta = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as exc:
        raise ValueError(f"{path}: YAML 格式錯誤：{exc}") from exc
    if not isinstance(meta, dict):
        raise ValueError(f"{path}: metadata 必須是欄位對照表")
    kind = meta.setdefault("type", "article" if source.name == "articles" else "paper")
    if not isinstance(kind, str) or kind not in TYPES:
        raise ValueError(f"{path}: type 必須是 paper（技術論文）或 article（深度文章）")
    for key in ("title", "summary"):
        if not isinstance(meta.get(key), str) or not meta[key].strip():
            raise ValueError(f"{path}: {key} 必須是非空字串")
    # Older notes remain buildable while their plain-language introduction is added.
    one_liner = meta.setdefault("one_liner", meta["summary"])
    if not isinstance(one_liner, str) or not one_liner.strip():
        raise ValueError(f"{path}: one_liner 必須是非空字串")
    for key in ("published", "added"):
        value = str(meta.get(key, ""))
        if key == "published" and kind == "article" and not value:
            meta[key] = ""
            continue
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValueError()
            meta[key] = date.fromisoformat(value).isoformat()
        except ValueError as exc:
            raise ValueError(f"{path}: {key} 必須是有效的 YYYY-MM-DD 日期") from exc
    for key in ("authors", "tags"):
        value = meta.setdefault(key, [])
        if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
            raise ValueError(f"{path}: {key} 必須是非空字串的清單（可以用 [] 留空）")
        meta[key] = list(dict.fromkeys(x.strip() for x in value))
    for key in ("venue", "paper_url", "source_url", "code_url"):
        value = meta.setdefault(key, "")
        if not isinstance(value, str):
            raise ValueError(f"{path}: {key} 必須是字串")
        if key.endswith("_url") and value:
            url = urlsplit(value)
            if url.scheme not in ("http", "https") or not url.netloc:
                raise ValueError(f"{path}: {key} 必須是完整的 HTTP(S) URL")
    # Existing paper_url fields keep working; new notes can use source_url.
    meta["source_url"] = meta["source_url"] or meta["paper_url"]
    rel = path.relative_to(source)
    if len(rel.parts) < 2 or rel.parts[0] in RESERVED:
        raise ValueError(f"{path}: 請放在主題資料夾內；tags、types、_static 為保留名稱")
    return {"meta": meta, "path": path, "output": rel.with_suffix(".html"),
            "category": rel.parts[0], "body": "\n".join(lines[end + 1:])}


class LinkRewriter(HTMLParser):
    """Rewrite actual href attributes, never text inside code blocks."""

    def __init__(self, paper: dict, pages: dict[Path, Path]):
        super().__init__(convert_charrefs=False)
        self.paper, self.pages, self.parts = paper, pages, []

    def start(self, tag, attrs, closed=False):
        result = []
        for key, value in attrs:
            if key == "href" and value:
                url = urlsplit(value)
                if not url.scheme and not url.netloc and url.path.lower().endswith(".md"):
                    if url.path.startswith("/"):
                        raise ValueError(f"{self.paper['path']}: Markdown 連結必須使用相對路徑：{value}")
                    target = (self.paper["path"].parent / unquote(url.path)).resolve()
                    if target not in self.pages:
                        raise ValueError(f"{self.paper['path']}: 找不到連結的 Markdown：{value}")
                    value = urlunsplit(("", "", relative_url(self.pages[target], self.paper["output"]),
                                        url.query, url.fragment))
            result.append(key if value is None else f'{key}="{escape(value, quote=True)}"')
        self.parts.append("<" + tag + (" " + " ".join(result) if result else "") + (" />" if closed else ">"))

    def handle_starttag(self, tag, attrs):
        self.start(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self.start(tag, attrs, True)

    def handle_endtag(self, tag):
        self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append(f"&{name};")

    def handle_charref(self, name):
        self.parts.append(f"&#{name};")

    def handle_comment(self, data):
        self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.parts.append(f"<!{decl}>")


def build(source: Path | list[Path], output: Path) -> int:
    sources = [source] if isinstance(source, Path) else source
    sources = list(dict.fromkeys(p.expanduser().resolve() for p in sources))
    output = output.expanduser().resolve()
    if not sources:
        raise ValueError("至少需要一個來源目錄")
    for src in sources:
        if not src.is_dir():
            raise ValueError(f"來源目錄不存在：{src}")
        if src == output or src in output.parents or output in src.parents:
            raise ValueError("來源和輸出目錄不能相同，也不能互相包含")
        if any(other in src.parents for other in sources if other != src):
            raise ValueError("多個來源目錄不能互相包含")
    if output == ROOT or output in ROOT.parents or ROOT / "web" == output or ROOT / "web" in output.parents:
        raise ValueError("輸出目錄不能覆寫專案或 web 版型目錄")
    for protected in (ROOT / "papers", ROOT / "articles", ROOT / "templates"):
        if output == protected or protected in output.parents:
            raise ValueError(f"輸出目錄不能寫入內容或範本目錄：{protected}")
    files = [(p, src) for src in sources for p in sorted(src.rglob("*"))]
    if any(p.is_symlink() for p, _ in files):
        raise ValueError("來源目錄包含符號連結；請改用實際檔案")
    entries = [load_entry(p, src) for p, src in files if p.is_file() and p.suffix.lower() == ".md"]
    entries.sort(key=lambda p: (p["meta"]["added"], p["meta"]["published"], p["output"].as_posix()), reverse=True)
    pages = {p["path"]: p["output"] for p in entries}
    categories = sorted({p.name for src in sources for p in src.iterdir()
                         if p.is_dir() and not p.name.startswith(".")})
    if any(c in RESERVED for c in categories):
        raise ValueError("來源分類不能使用保留名稱 tags、types 或 _static")
    template = Template((ROOT / "web/page.html").read_text(encoding="utf-8"))
    generated: dict[Path, bytes] = {}
    generated_names: set[str] = set()

    def add(path: Path, content: str | bytes):
        # Case-insensitive collisions would break a Windows deployment.
        name = path.as_posix().casefold()
        if name in generated_names:
            raise ValueError(f"輸出路徑衝突：{path}")
        generated_names.add(name)
        generated[path] = content.encode("utf-8") if isinstance(content, str) else content

    category_counts = {c: sum(p["category"] == c for p in entries) for c in categories}
    type_counts = {kind: sum(p["meta"]["type"] == kind for p in entries) for kind in TYPES}
    tag_counts = defaultdict(int)
    for entry in entries:
        body = entry["body"]
        cjk = len(re.findall(r"[\u3400-\u9fff]", body))
        words = len(re.findall(r"[A-Za-z0-9]+", body))
        entry["minutes"] = max(1, math.ceil(cjk / 400 + words / 220))
        for tag in entry["meta"]["tags"]:
            tag_counts[tag] += 1

    def tags_html(tags, page):
        return '<div class="tags">' + "".join(
            f'<a class="tag" href="{relative_url(tag_path(t), page)}">{escape(t)}</a>' for t in tags) + "</div>"

    def type_link(kind, path):
        return (f'<a class="type-badge type-{kind}" href="{relative_url(Path("types") / kind / "index.html", path)}">'
                f'{TYPES[kind]}</a>')

    def page(path, title, description, content, page_class="listing-page", active_category=None, active_type=None):
        def nav_link(target, label, count, active=False):
            current = ' aria-current="page"' if active else ""
            return f'<a href="{relative_url(target, path)}"{current}>{escape(label)}<span class="nav-count">{count:02d}</span></a>'
        primary = nav_link(Path("index.html"), "全部收錄", len(entries), path == Path("index.html"))
        primary += "".join(nav_link(Path("types") / kind / "index.html", label, type_counts[kind], kind == active_type)
                           for kind, label in TYPES.items())
        def subject(c):
            active = ' aria-current="page"' if c == active_category else ""
            return (f'<li><a href="{relative_url(Path(c) / "index.html", path)}"{active}>'
                    f'<span>{escape(LABELS.get(c, c))}</span><small>{category_counts[c]:02d}</small></a></li>')
        populated = [c for c in categories if category_counts[c]]
        empty_categories = [c for c in categories if not category_counts[c]]
        nav = ('<div class="nav-section"><p class="nav-label">主題索引 / SUBJECTS</p><ul class="subject-list">'
               + "".join(subject(c) for c in populated) + '</ul>')
        if empty_categories:
            opened = " open" if active_category in empty_categories else ""
            nav += (f'<details class="empty-subjects"{opened}><summary>其他主題</summary><ul class="subject-list">'
                    + "".join(subject(c) for c in empty_categories) + '</ul></details>')
        nav += '</div>'
        if tag_counts:
            tags = sorted(tag_counts, key=lambda t: (-tag_counts[t], t))[:8]
            nav += ('<div class="nav-section"><p class="nav-label">常見標籤 / TOPICS</p><div class="tag-cloud">'
                    + "".join(f'<a class="tag" href="{relative_url(tag_path(t), path)}">{escape(t)}</a>' for t in tags)
                    + '</div></div>')
        nav += '<div class="sidebar-note"><strong>一份持續生長的閱讀筆記</strong>從白話重點開始，循著方法與觀點，讀懂值得留下的內容。</div>'
        add(path, template.substitute(title=escape(title), description=escape(description, quote=True),
            stylesheet=relative_url(Path("_static/style.css"), path),
            script=relative_url(Path("_static/site.js"), path),
            favicon=relative_url(Path("_static/favicon.svg"), path),
            search_url=relative_url(Path("search.html"), path), page_class=page_class,
            home=relative_url(Path("index.html"), path), primary_navigation=primary, navigation=nav, content=content))

    def card(entry, path, number=0, featured=False, heading="h2"):
        m = entry["meta"]
        target = relative_url(entry["output"], path)
        label = "一句話用途" if m["type"] == "paper" else "一句話重點"
        search = " ".join([m["title"], m["one_liner"], m["summary"], m["venue"],
                           LABELS.get(entry["category"], entry["category"]), *m["tags"], *m["authors"]])
        extra_class = " featured" if featured else ""
        serial = "最新收錄 / " if featured else ""
        text = (f'<article class="entry-card{extra_class}" data-type="{m["type"]}" data-search="{escape(search, quote=True)}">'
                f'<div class="card-top">{type_link(m["type"], path)}'
                f'<a class="card-category" href="{relative_url(Path(entry["category"]) / "index.html", path)}">'
                f'{escape(LABELS.get(entry["category"], entry["category"]))}</a>'
                f'<span class="card-index">{serial}{number:02d}</span></div>'
                f'<span class="summary-label">{label}</span>'
                f'<{heading}><a href="{target}">{escape(m["one_liner"])}</a></{heading}>'
                f'<p class="original-title"><a href="{target}">{escape(m["title"])}</a></p>')
        if featured and m["summary"] != m["one_liner"]:
            text += f'<div class="card-summary"><p>{escape(m["summary"])}</p></div>'
        text += tags_html(m["tags"], path)
        text += (f'<div class="card-footer"><span>收錄 <time datetime="{m["added"]}">{m["added"].replace("-", ".")}</time>'
                 f' · 約 {entry["minutes"]} 分鐘</span><a href="{target}" aria-label="閱讀：{escape(m["title"], quote=True)}">'
                 '閱讀筆記 <span aria-hidden="true">↗</span></a></div></article>')
        return text

    def listing(path, title, selected, active_category=None, active_type=None):
        home = path == Path("index.html")
        if home:
            content = ('<section class="home-intro"><div><p class="eyebrow">A READING ARCHIVE · BY OX</p>'
                       '<h1>探索技術，<br><span>理解更大的世界。</span></h1>'
                       '<p class="intro-text">從一個清楚的問題出發，讀懂方法與觀點。</p></div>'
                       f'<dl class="archive-stats"><div><dd>{len(entries):02d}</dd><dt>篇收錄</dt></div>'
                       f'<div><dd>{sum(n > 0 for n in category_counts.values()):02d}</dd><dt>個主題</dt></div></dl></section>')
        else:
            descriptions = {"paper": "從用途出發，理解技術如何運作，以及可以走多遠。",
                            "article": "讀懂作者的問題、觀點與推理，留下自己的思考。"}
            description = descriptions.get(active_type, "沿著同一條線索，繼續探索值得理解的內容。")
            if path == Path("search.html"):
                description = "搜尋標題、摘要、標籤、作者與來源，找到下一篇想讀的內容。"
            content = (f'<header class="list-intro"><p class="eyebrow">READING INDEX</p><h1>{escape(title)}</h1>'
                       f'<p class="intro-text">{description}</p></header>')
        if selected:
            content += ('<form class="archive-search enhanced-only" role="search" aria-label="搜尋此列表">'
                        '<label class="search-field"><svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true">'
                        '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></svg>'
                        '<span class="sr-only">搜尋標題、摘要或標籤</span><input name="q" type="search" '
                        'placeholder="搜尋標題、摘要或標籤…" autocomplete="off"></label>'
                        '<label class="sr-only" for="type-filter">內容類型</label><select name="type" id="type-filter">'
                        '<option value="">所有類型</option><option value="paper">技術論文</option>'
                        '<option value="article">深度文章</option></select><button class="clear-search" type="button">清除</button></form>')
        section_title = "最新筆記" if home else "收錄內容"
        content += (f'<div class="section-heading"><h2>{section_title}</h2>'
                    f'<p><span class="result-count" role="status" aria-live="polite">共 {len(selected)} 篇</span> · 最近收錄優先</p></div>')
        content += '<div class="entry-grid">' + "".join(card(p, path, i, home and i == 1) for i, p in enumerate(selected, 1)) + '</div>'
        if not selected:
            content += (f'<section class="empty-state"><h2>這裡的筆記，正等待下一次發現。</h2><p>目前尚未收錄內容。</p>'
                        f'<a href="{relative_url(Path("index.html"), path)}">先逛逛全部收錄 →</a></section>')
        content += ('<section class="empty-state search-empty" hidden><h2>沒有找到符合的內容</h2>'
                    '<p>試試較短的關鍵字，或清除類型篩選。</p><button type="button">清除篩選</button></section>')
        page(path, title, f"{title}，共 {len(selected)} 篇閱讀筆記。", content,
             "home-page" if home else "listing-page", active_category, active_type)

    listing(Path("index.html"), "探索技術，理解更大的世界", entries)
    listing(Path("search.html"), "找一篇值得讀的內容", entries)
    for kind, label in TYPES.items():
        listing(Path("types") / kind / "index.html", label, [p for p in entries if p["meta"]["type"] == kind], active_type=kind)
    for category in categories:
        listing(Path(category) / "index.html", LABELS.get(category, category),
                [p for p in entries if p["category"] == category], active_category=category)
    tagged = defaultdict(list)
    for p in entries:
        m, path = p["meta"], p["output"]
        converter = markdown.Markdown(extensions=["extra", "toc", "sane_lists"], output_format="html5")
        rendered = converter.convert(p["body"])
        # Move an existing Markdown title into the article header while retaining its anchor.
        first_heading = re.match(r"\s*<h1\b([^>]*)>.*?</h1>", rendered, re.DOTALL)
        title_id = "entry-title"
        if first_heading:
            anchor = re.search(r'id="([^"]*)"', first_heading.group(1))
            if anchor:
                title_id = anchor.group(1)
            rendered = rendered[first_heading.end():]
        # The generated reading rail replaces [TOC], including in older notes.
        if converter.toc.strip():
            rendered = rendered.replace(converter.toc.strip(), "")
        rewrite = LinkRewriter(p, pages)
        rewrite.feed(rendered)
        rewrite.close()
        headings = []
        def collect_headings(tokens):
            for token in tokens:
                if token["level"] in (2, 3):
                    sub = ' class="toc-sub"' if token["level"] == 3 else ""
                    headings.append(f'<li{sub}><a href="#{escape(token["id"], quote=True)}">{escape(unescape(token["name"]))}</a></li>')
                collect_headings(token["children"])
        collect_headings(converter.toc_tokens)
        source_label = "閱讀原始論文 ↗" if m["type"] == "paper" else "閱讀原文 ↗"
        links = "".join(f'<a href="{escape(m[k], quote=True)}">{label}</a>'
                        for k, label in (("source_url", source_label), ("code_url", "程式碼 ↗")) if m[k])
        breadcrumb = (f'<nav class="breadcrumbs" aria-label="文章路徑"><a href="{relative_url(Path("index.html"), path)}">全部收錄</a>'
                      f'<span aria-hidden="true">/</span><a href="{relative_url(Path("types") / m["type"] / "index.html", path)}">{TYPES[m["type"]]}</a>'
                      f'<span aria-hidden="true">/</span><a href="{relative_url(Path(p["category"]) / "index.html", path)}">'
                      f'{escape(LABELS.get(p["category"], p["category"]))}</a></nav>')
        byline = " · ".join(value for value in ("、".join(m["authors"]), m["venue"]) if value)
        content = (breadcrumb + f'<header class="article-header">{type_link(m["type"], path)}'
                   f'<h1 id="{escape(title_id, quote=True)}">{escape(m["title"])}</h1><div class="article-meta">'
                   f'<span>發表 {m["published"] or "日期未詳"}</span><span>收錄 {m["added"]}</span>'
                   f'<span>約 {p["minutes"]} 分鐘閱讀</span></div>'
                   + (f'<p class="article-byline">{escape(byline)}</p>' if byline else "") + '</header>')
        label = "一句話用途" if m["type"] == "paper" else "一句話重點"
        lead = (f'<section class="article-lead" aria-label="{label}"><span class="summary-label">{label}</span>'
                f'<p class="one-liner">{escape(m["one_liner"])}</p>')
        if m["summary"] != m["one_liner"]:
            lead += f'<p class="summary-detail">{escape(m["summary"])}</p>'
        if links:
            lead += f'<div class="source-links">{links}</div>'
        lead += '</section>'
        content += ('<div class="article-layout"><div class="article-main">' + lead
                    + '<article class="prose">' + "".join(rewrite.parts) + '</article>'
                    + '<div class="article-end"><p class="nav-label">繼續探索</p>' + tags_html(m["tags"], path) + '</div></div>')
        if headings:
            content += '<details class="article-toc" open><summary>本篇目錄</summary><ol>' + "".join(headings) + '</ol></details>'
        content += '</div>'
        related = [other for other in entries if other != p and
                   (set(m["tags"]) & set(other["meta"]["tags"]) or other["category"] == p["category"])]
        related.sort(key=lambda other: len(set(m["tags"]) & set(other["meta"]["tags"])), reverse=True)
        if related:
            content += ('<section class="related-reading"><div class="section-heading"><h2>沿著這個問題，繼續讀</h2>'
                        '<p>相關主題與標籤</p></div><div class="entry-grid">'
                        + "".join(card(other, path, i, heading="h3") for i, other in enumerate(related[:2], 1)) + '</div></section>')
        page(path, m["title"], m["summary"], content, "article-page", p["category"], m["type"])
        for tag in m["tags"]:
            tagged[tag].append(p)
    for tag in sorted(tagged):
        listing(tag_path(tag), f"標籤 / {tag}", tagged[tag])
    for asset_name in ("style.css", "site.js", "favicon.svg"):
        add(Path("_static") / asset_name, (ROOT / "web" / asset_name).read_bytes())
    add(Path(".nojekyll"), "")
    for asset, src in files:
        rel = asset.relative_to(src)
        if asset.is_file() and "assets" in rel.parts[:-1] and asset.suffix.lower() != ".md":
            if not any(part.startswith(".") for part in rel.parts):
                add(rel, asset.read_bytes())

    def destination(name: str) -> Path:
        rel = PurePosixPath(name)
        if not name or rel.is_absolute() or ".." in rel.parts or "\\" in name or ":" in name or name == MANIFEST:
            raise ValueError(f"無效的生成檔案路徑：{name}")
        target = output.joinpath(*rel.parts)
        if target == output or output not in target.resolve().parents:
            raise ValueError(f"輸出路徑超出網站目錄：{name}")
        if any(p.is_symlink() for p in (target, *target.parents) if p != output and output in p.parents):
            raise ValueError(f"輸出路徑包含符號連結：{name}")
        return target

    manifest = output / MANIFEST
    if manifest.is_symlink():
        raise ValueError("生成記錄不能是符號連結")
    previous = []
    if manifest.exists():
        previous = json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(previous, list) or any(not isinstance(p, str) for p in previous):
            raise ValueError(f"生成記錄格式錯誤：{manifest}")
    previous_set = set(previous)
    current = {p.as_posix() for p in generated}
    for name in previous_set | current:
        target = destination(name)
        if target.exists() and (not target.is_file() or name not in previous_set):
            raise ValueError(f"拒絕覆寫非本腳本管理的檔案或目錄：{target}")
        if any(parent.exists() and not parent.is_dir() for parent in target.parents):
            raise ValueError(f"輸出路徑的父層不是目錄：{target}")
    # All parsing, rendering, link validation and collision checks finish before writing.
    output.mkdir(parents=True, exist_ok=True)
    for rel, content in generated.items():
        target = destination(rel.as_posix())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    for name in previous_set - current:
        destination(name).unlink(missing_ok=True)
    manifest.write_text(json.dumps(sorted(current), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(entries)


def main() -> int:
    parser = argparse.ArgumentParser(description="將技術論文與深度文章的 Markdown 筆記轉成靜態 HTML 網站")
    parser.add_argument("--source", type=Path, action="append", help="Markdown 來源目錄，可重複指定（預設：腳本旁的 papers 和 articles）")
    parser.add_argument("--output", type=Path, default=ROOT / "site", help="HTML 輸出目錄（預設：腳本旁的 site）")
    args = parser.parse_args()
    try:
        output = args.output.expanduser().resolve()
        count = build(args.source if args.source is not None else [ROOT / "papers", ROOT / "articles"], output)
    except (OSError, ValueError, KeyError) as exc:
        print(f"生成失敗：{exc}", file=sys.stderr)
        return 1
    print(f"已生成 {count} 篇內容：{output / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
