#!/usr/bin/env python3
"""Build a static paper notebook. Requires Python 3.10+, Markdown and PyYAML."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
import hashlib
from html import escape
from html.parser import HTMLParser
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
          "ai": "人工智能", "systems": "系統與引擎架構"}


def relative_url(target: Path, page: Path) -> str:
    return quote(Path(os.path.relpath(target, page.parent)).as_posix(), safe="/.-_")


def tag_path(tag: str) -> Path:
    slug = tag if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", tag) else (
        "tag-" + hashlib.sha256(tag.encode("utf-8")).hexdigest()[:16])
    return Path("tags") / slug / "index.html"


def load_paper(path: Path, source: Path) -> dict:
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
    for key in ("title", "summary"):
        if not isinstance(meta.get(key), str) or not meta[key].strip():
            raise ValueError(f"{path}: {key} 必須是非空字串")
    for key in ("published", "added"):
        value = str(meta.get(key, ""))
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
    for key in ("venue", "paper_url", "code_url"):
        value = meta.setdefault(key, "")
        if not isinstance(value, str):
            raise ValueError(f"{path}: {key} 必須是字串")
        if key.endswith("_url") and value:
            url = urlsplit(value)
            if url.scheme not in ("http", "https") or not url.netloc:
                raise ValueError(f"{path}: {key} 必須是完整的 HTTP(S) URL")
    rel = path.relative_to(source)
    if len(rel.parts) < 2 or rel.parts[0] in ("tags", "_static"):
        raise ValueError(f"{path}: 請放在主題資料夾內；tags、_static 為保留名稱")
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


def build(source: Path, output: Path) -> int:
    if not source.is_dir():
        raise ValueError(f"來源目錄不存在：{source}")
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("來源和輸出目錄不能相同，也不能互相包含")
    if output == ROOT or output in ROOT.parents or ROOT / "web" == output or ROOT / "web" in output.parents:
        raise ValueError("輸出目錄不能覆寫專案或 web 版型目錄")
    files = sorted(source.rglob("*"))
    if any(p.is_symlink() for p in files):
        raise ValueError("來源目錄包含符號連結；請改用實際檔案")
    papers = [load_paper(p, source) for p in files if p.is_file() and p.suffix.lower() == ".md"]
    papers.sort(key=lambda p: (p["meta"]["added"], p["meta"]["published"], p["output"].as_posix()), reverse=True)
    pages = {p["path"]: p["output"] for p in papers}
    categories = sorted(p.name for p in source.iterdir() if p.is_dir() and not p.name.startswith("."))
    if any(c in ("tags", "_static") for c in categories):
        raise ValueError("來源分類不能使用保留名稱 tags 或 _static")
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

    def tags_html(tags, page):
        return '<div class="tags">' + "".join(
            f'<a class="tag" href="{relative_url(tag_path(t), page)}">{escape(t)}</a>' for t in tags) + "</div>"

    def page(path, title, description, content):
        nav = '<p><strong>技術分類</strong></p><ul>' + "".join(
            f'<li><a href="{relative_url(Path(c) / "index.html", path)}">{escape(LABELS.get(c, c))}</a></li>'
            for c in categories) + "</ul>"
        add(path, template.substitute(title=escape(title), description=escape(description, quote=True),
            stylesheet=relative_url(Path("_static/style.css"), path),
            home=relative_url(Path("index.html"), path), navigation=nav, content=content))

    def listing(path, title, entries):
        content = f"<h1>{escape(title)}</h1><p class=\"meta\">共 {len(entries)} 篇 · 按收錄日期排序</p>"
        if not entries:
            content += "<p>尚未收錄論文。</p>"
        for p in entries:
            m = p["meta"]
            content += (f'<article class="paper-card"><h2><a href="{relative_url(p["output"], path)}">'
                        f'{escape(m["title"])}</a></h2><p class="meta">發表 {m["published"]} · '
                        f'收錄 {m["added"]} · {escape(LABELS.get(p["category"], p["category"]))}</p>'
                        f'<p>{escape(m["summary"])}</p>{tags_html(m["tags"], path)}</article>')
        page(path, title, f"{title}，共 {len(entries)} 篇技術論文筆記。", content)

    listing(Path("index.html"), "最新收錄", papers)
    for category in categories:
        listing(Path(category) / "index.html", LABELS.get(category, category),
                [p for p in papers if p["category"] == category])
    tagged = defaultdict(list)
    for p in papers:
        m = p["meta"]
        converter = markdown.Markdown(extensions=["extra", "toc", "sane_lists"], output_format="html5")
        rendered = converter.convert(p["body"])
        rewrite = LinkRewriter(p, pages)
        rewrite.feed(rendered)
        rewrite.close()
        links = " · ".join(f'<a href="{escape(m[k], quote=True)}">{label}</a>'
                           for k, label in (("paper_url", "原始論文"), ("code_url", "程式碼")) if m[k])
        details = (f'<section class="paper-info" aria-label="論文資料"><p>{escape(m["summary"])}</p>'
                   f'<p class="meta">發表 {m["published"]} · 收錄 {m["added"]}<br>'
                   f'{escape("、".join(m["authors"]))} · {escape(m["venue"])}</p>'
                   f'<p>{links}</p>{tags_html(m["tags"], p["output"])}</section>')
        page(p["output"], m["title"], m["summary"], details + '<article class="paper">' + "".join(rewrite.parts) + "</article>")
        for tag in m["tags"]:
            tagged[tag].append(p)
    for tag in sorted(tagged):
        listing(tag_path(tag), f"標籤：{tag}", tagged[tag])
    add(Path("_static/style.css"), (ROOT / "web/style.css").read_bytes())
    add(Path(".nojekyll"), "")
    for asset in files:
        rel = asset.relative_to(source)
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
    return len(papers)


def main() -> int:
    parser = argparse.ArgumentParser(description="將技術論文 Markdown 轉成靜態 HTML 網站")
    parser.add_argument("--source", type=Path, default=ROOT / "papers", help="Markdown 來源目錄（預設：腳本旁的 papers）")
    parser.add_argument("--output", type=Path, default=ROOT / "site", help="HTML 輸出目錄（預設：腳本旁的 site）")
    args = parser.parse_args()
    try:
        output = args.output.expanduser().resolve()
        count = build(args.source.expanduser().resolve(), output)
    except (OSError, ValueError, KeyError) as exc:
        print(f"生成失敗：{exc}", file=sys.stderr)
        return 1
    print(f"已生成 {count} 篇論文：{output / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
