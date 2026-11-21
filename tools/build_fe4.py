#!/usr/bin/env python3
"""Build the FE4 (Genealogy of the Holy War) script site: public/fe4/.

Reads source/fe4/*.html (UTF-8, saved from pegasusknight.com's current
Master Bible pages, see fe4_parser.py) and writes public/fe4/index.html +
chapters/*.html. Same mechanism as tools/build_fe6.py: no central
vocab/grammar reference pages for now, per-bubble study notes if present
show vocab + grammar the same way.

    python3 tools/build_fe4.py
"""
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import en  # noqa: E402
from fe4_parser import Fe4Parser  # noqa: E402
from sidebar import render_sidebar  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source" / "fe4"
STUDY = ROOT / "study" / "fe4"
WEB = ROOT / "public" / "fe4"
OUT = WEB / "chapters"
SOURCE_URL = "https://www.pegasusknight.com/mb/fe4/st_index"

# (source file stem, output slug, short label, English title)
PAGES = [
    ("st_map0", "prologue", "序章", "Birth of a Holy Knight"),
    ("st_map1", "ch01", "第1章", "Lady of the Forest"),
    ("st_map2", "ch02", "第2章", "Turmoil in Agustria"),
    ("st_map3", "ch03", "第3章", "Eldigan the Lionheart"),
    ("st_map4", "ch04", "第4章", "Dancing in the Sky"),
    ("st_map5", "ch05", "第5章", "Gate of Destiny"),
    ("st_map6", "ch06", "第6章", "Successor of Light"),
    ("st_map7", "ch07", "第7章", "Beyond the Desert"),
    ("st_map8", "ch08", "第8章", "Dragon Knights of Thracia"),
    ("st_map9", "ch09", "第9章", "For Whose Sake"),
    ("st_map10", "ch10", "第10章", "Light and Dark"),
    ("st_map11", "ch11", "終章", "The Final Holy War"),
    ("st_ending", "ending", "エンディング", "Ending"),
]


def sidebar(current_href, at_root):
    prefix = "chapters/" if at_root else ""
    chapters = [(f"{prefix}{slug}.html", f"{label} {title}") for stem, slug, label, title in PAGES]
    return render_sidebar(chapters, current_href)


BOX_NO = [0]


def esc(s):
    return html.escape(s, quote=True)


def tr(fn, text):
    try:
        return fn(text)
    except en.Unknown:
        return text


def load_table(name, width=3):
    path, out = STUDY / f"{name}.txt", {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == width and not line.startswith("#"):
                out[parts[0]] = parts[1:]
    return out


VOCAB = load_table("vocab")
GRAMMAR = load_table("grammar", 4)
STUDY_PROBLEMS = []


def load_study(slug, texts):
    path = STUDY / f"{slug}.txt"
    if not path.exists():
        return None
    boxes, vocab, grammar = {}, {}, {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("|")
        if len(parts) != 3 or not parts[0].strip().isdigit():
            continue
        n = int(parts[0])
        words = []
        for item in filter(None, (w.strip() for w in parts[1].split(","))):
            surface, _, key = item.partition(">")
            key = key or surface
            if key not in VOCAB:
                STUDY_PROBLEMS.append(f"{slug} #{n}: no vocab entry for {key}")
                continue
            if surface.split("#")[0] not in texts.get(n, ""):
                STUDY_PROBLEMS.append(f"{slug} #{n}: {surface} is not in the bubble text")
            vocab[key] = [key.split("#")[0]] + VOCAB[key]
            words.append([surface.split("#")[0], key])
        points = []
        for gid in filter(None, (g.strip() for g in parts[2].split(","))):
            if gid not in GRAMMAR:
                STUDY_PROBLEMS.append(f"{slug} #{n}: no grammar entry for {gid}")
                continue
            grammar[gid] = GRAMMAR[gid]
            points.append(gid)
        boxes[n] = [words, points]
    return {"v": vocab, "g": grammar, "b": boxes}


def load_translations(slug):
    path, out = ROOT / "translations" / "fe4" / f"{slug}.txt", {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            n, _, text = line.partition("\t")
            if n.strip().isdigit() and text.strip():
                out[int(n)] = text.strip()
    return out


CURRENT_EN = {}

TOKENS, GLOSSARY = {}, []
if (ROOT / "data" / "fe4_tokens.json").exists():
    TOKENS = json.loads((ROOT / "data" / "fe4_tokens.json").read_text(encoding="utf-8"))
    GLOSSARY = json.loads((ROOT / "data" / "fe4_glossary.json").read_text(encoding="utf-8"))
USED_GLOSS = set()


def ruby(text):
    words = TOKENS.get(text)
    if not words:
        return esc(text)
    out = []
    for surface, segs, gid in words:
        inner = esc(surface) if not segs else "".join(
            f"<ruby>{esc(s)}<rt>{esc(r)}</rt></ruby>" if r else esc(s) for s, r in segs)
        if gid is None:
            out.append(inner)
        else:
            USED_GLOSS.add(gid)
            out.append(f'<span class="w" data-g="{gid}">{inner}</span>')
    return "".join(out)


def portrait_key(speaker):
    return speaker.replace("（", "(").replace("）", ")").replace("/", "／").replace("?", "？")


def portrait_src(key):
    if (WEB / "img" / "portraits" / f"{key}.png").exists():
        return f"../img/portraits/{key}.png"
    return "../img/placeholder.svg"


def render_lines(lines):
    out = []
    for line in lines:
        buf = "".join(ruby(v) for _, v in line)
        out.append(f'<span class="ln">{buf}</span>')
    return "<br>\n".join(out)


def box_html(b):
    BOX_NO[0] += 1
    etext = CURRENT_EN.get(BOX_NO[0])
    en_html = f'<span class="box-en" lang="en">{esc(etext)}</span>' if etext else ""
    return (f'<p class="box" data-n="{BOX_NO[0]}" tabindex="0">'
            f'<span class="jp">{render_lines(b["lines"])}</span>{en_html}</p>')


def render_scene(scene, portraits):
    out, i, items = [], 0, scene["items"]
    sides, last_side = {}, "r"
    while i < len(items):
        it = items[i]
        if it["t"] == "note":
            fn = {"cond": en.cond}.get(it["kind"], en.direction)
            out.append(f'<p class="note note-{it["kind"]}">{esc(tr(fn, it["text"]))}</p>')
            i += 1
            continue
        j = i
        while j < len(items) and items[j]["t"] == "box" and items[j]["speaker"] == it["speaker"]:
            j += 1
        boxes = "\n".join(box_html(b) for b in items[i:j])
        sp = it["speaker"]
        if sp is None:
            out.append(f'<div class="turn narration" lang="ja"><div class="bubbles">{boxes}</div></div>')
        else:
            side = sides.get(sp)
            if side is None or side == last_side:
                side = "l" if last_side == "r" else "r"
            sides[sp] = last_side = side
            key = portrait_key(sp)
            portraits[key] = portraits.get(key, 0) + 1
            out.append(
                f'<div class="turn {side}" data-speaker="{esc(sp)}">'
                f'<figure class="who"><img src="{esc(portrait_src(key))}" data-portrait="{esc(key)}" alt="" '
                f'width="96" height="128" decoding="async">'
                f'<figcaption lang="ja">{esc(sp)}</figcaption></figure>'
                f'<div class="bubbles" lang="ja">{boxes}</div></div>')
        i = j
    return "\n".join(out)


PAGE = """<!DOCTYPE HTML>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Genealogy of the Holy War Script</title>
<link rel="stylesheet" href="{rel}css/style.css">
<script>try {{
  if (localStorage.getItem("furigana") === "1") document.documentElement.classList.add("furi");
  if (localStorage.getItem("english") === "1") document.documentElement.classList.add("eng");
}} catch (e) {{}}</script>
</head>
<body>
<header class="site">
<div class="bar">
<a class="all-games" href="{rel}../index.html">← All games</a>
<span class="title-group"><a class="site-title" href="{rel}../index.html">Fire Emblem</a><span class="title-sep">-</span><a class="game-name" href="{rel}index.html">Genealogy of the Holy War<span class="orig" lang="ja">聖戦の系譜</span></a></span>
<nav class="tools">{tools}</nav>
</div>
</header>
<div class="layout">
{sidebar}
<div class="main-col">
{body}
</div>
</div>
{scripts}
<footer class="site">
<p>Dialogue source: <a href="{source}"><span lang="ja">ファイアーエムブレム 聖戦の系譜・マスターバイブル 会話集</span></a> (Pegasus Knight).</p>
<p>English translations of the dialogue and chapter titles are unofficial and written for this site.</p>
<p>Fire Emblem: Genealogy of the Holy War © Nintendo / Intelligent Systems. Unofficial fan site.</p>
</footer>
</body>
</html>
"""

TOGGLES = ('<button type="button" class="furi-toggle" aria-pressed="false" '
           'title="Show readings above kanji"><span class="knob"></span>Furigana</button>'
           '<button type="button" class="en-toggle" aria-pressed="false" '
           'title="Show the English translation instead of the Japanese text">'
           '<span class="knob"></span>English</button>')


def nav(idx, pages):
    lab = lambda i: pages[i][3]
    prev = f'<a class="prev" href="{pages[idx-1][1]}.html">← {lab(idx-1)}</a>' if idx else "<span></span>"
    nxt = f'<a class="next" href="{pages[idx+1][1]}.html">{lab(idx+1)} →</a>' if idx + 1 < len(pages) else "<span></span>"
    return f'<nav class="pager">{prev}<a class="up" href="../index.html">Contents</a>{nxt}</nav>'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (WEB / "img" / "portraits").mkdir(parents=True, exist_ok=True)
    stats, studied, portraits, script_data = [], [], {}, {}
    for idx, (stem, slug, label, title) in enumerate(PAGES):
        BOX_NO[0] = 0
        USED_GLOSS.clear()
        english = load_translations(slug)
        CURRENT_EN.clear()
        CURRENT_EN.update(english)
        raw_path = SRC / f"{stem}.html"
        if not raw_path.exists():
            print(f"MISSING source: {stem}.html")
            continue
        raw = raw_path.read_text(encoding="utf-8")
        scenes = [s for s in Fe4Parser(raw).scenes if s["items"]]
        boxes = sum(1 for s in scenes for i in s["items"] if i["t"] == "box")
        stats.append((slug, len(scenes), boxes))
        script_data[slug] = {"label": label, "title": title, "scenes": scenes}

        toc = "\n".join(f'<li><a href="#s{n}">{esc(tr(en.title, s["title"]))}</a></li>'
                         for n, s in enumerate(scenes, 1))
        h1 = f'<span class="num">{esc(label)}</span>{esc(title)}'
        parts = [nav(idx, PAGES), f"<h1>{h1}</h1>",
                 f'<details class="toc"><summary>Scenes ({len(scenes)})</summary><ol>{toc}</ol></details>',
                 "<main>"]
        for n, s in enumerate(scenes, 1):
            parts.append(f'<section class="scene" id="s{n}">')
            if s["title"]:
                parts.append(f'<h2><a href="#s{n}">{esc(tr(en.title, s["title"]))}</a></h2>')
            parts.append(render_scene(s, portraits))
            parts.append("</section>")
        parts += ["</main>", nav(idx, PAGES),
                  '<div class="gloss-backdrop" hidden></div>'
                  '<aside class="gloss" aria-live="polite" hidden><div class="gloss-head"><span>Translation</span>'
                  '<button type="button" class="gloss-close" aria-label="Close">×</button></div>'
                  '<div class="gloss-body"><p class="gloss-hint">Click a speech bubble to see its '
                  'translation and vocabulary.</p></div></aside>']

        texts, k = {}, 0
        for s in scenes:
            for it in s["items"]:
                if it["t"] == "box":
                    k += 1
                    texts[k] = "".join(v for line in it["lines"] for _, v in line)
        study = load_study(slug, texts)
        if study:
            studied.append(slug)

        (OUT / "gloss").mkdir(exist_ok=True)
        (OUT / "gloss" / f"{slug}.js").write_text(
            "window.GLOSS=" + json.dumps({g: GLOSSARY[g] for g in sorted(USED_GLOSS)},
                                         ensure_ascii=False, separators=(",", ":")) + ";\n"
            "window.EN=" + json.dumps(english, ensure_ascii=False, separators=(",", ":")) + ";\n"
            + ("window.STUDY=" + json.dumps(study, ensure_ascii=False, separators=(",", ":")) + ";\n"
               if study else ""),
            encoding="utf-8")
        scripts = f'<script src="gloss/{slug}.js"></script>\n<script src="../js/site.js"></script>'
        (OUT / f"{slug}.html").write_text(
            PAGE.format(title=title, rel="../", tools=TOGGLES, scripts=scripts,
                        body="\n".join(parts), source=SOURCE_URL,
                        sidebar=sidebar(f"{slug}.html", at_root=False)),
            encoding="utf-8")

    toc_rows = "\n".join(
        f'<li><a href="chapters/{slug}.html"><span class="num">{esc(label)}</span>'
        f'<span class="title">{esc(title)}</span></a></li>'
        for stem, slug, label, title in PAGES
    )
    body = ('<h1><span class="num">Fire Emblem</span>Genealogy of the Holy War Japanese Script'
            '<span class="orig"><span lang="ja">ファイアーエムブレム　聖戦の系譜</span></span></h1>'
            '<p class="lead">Every chapter\'s dialogue in the original Japanese. '
            'Hand-written study notes and English translations are in progress, chapter by chapter.</p>'
            f'<ol class="chapters">{toc_rows}</ol>')
    (WEB / "index.html").write_text(
        PAGE.format(title="Contents", rel="", tools="", scripts="", body=body, source=SOURCE_URL,
                    sidebar=sidebar(None, at_root=True)),
        encoding="utf-8")

    (ROOT / "data" / "fe4_script.json").write_text(
        json.dumps(script_data, ensure_ascii=False, indent=1), encoding="utf-8")

    placeholder = WEB / "img" / "placeholder.svg"
    if not placeholder.exists():
        thracia_placeholder = ROOT / "public" / "thracia" / "img" / "placeholder.svg"
        placeholder.write_text(thracia_placeholder.read_text(encoding="utf-8"), encoding="utf-8")
    rows = sorted(portraits.items(), key=lambda kv: (-kv[1], kv[0]))
    (WEB / "img" / "portraits" / "README.txt").write_text(
        "Drop portraits here as <name>.png (3:4, e.g. 48x64 or 96x128).\n"
        "Then re-run: python3 tools/build_fe4.py\n"
        "Any missing file falls back to img/placeholder.svg.\n\n"
        "file name\ttimes used\n" + "\n".join(f"{k}.png\t{v}" for k, v in rows) + "\n", encoding="utf-8")

    for slug, scenes, boxes in stats:
        print(f"{slug:10} scenes={scenes:3} boxes={boxes:4}")
    print("hand-written vocabulary + grammar notes:", " ".join(studied) or "none")
    if STUDY_PROBLEMS:
        for p in STUDY_PROBLEMS:
            print("STUDY:", p)


if __name__ == "__main__":
    main()
