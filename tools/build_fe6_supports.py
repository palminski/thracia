#!/usr/bin/env python3
"""Build FE6's support-conversation pages: public/fe6/supports/.

Reads source/fe6/support/st_support1..54.html (fetched by
tools/fetch_fe6_support_source.py) and writes:
  public/fe6/supports/index.html              - grid of all 54 characters
  public/fe6/supports/char/<slug>.html         - one character + their partners
  public/fe6/supports/pair/<slug>-<slug>.html  - one pair's C/B/A conversation

Same vocab/grammar study-notes mechanism as the main chapters, sharing the
same central study/fe6/vocab.txt and study/fe6/grammar.txt. Per-pair
translations and study notes live in their own files:
  translations/fe6/supports/<slug>-<slug>.txt
  study/fe6/supports/<slug>-<slug>.txt

    python3 tools/build_fe6_supports.py
"""
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import en  # noqa: E402
from fe6_support_parser import Fe6SupportParser  # noqa: E402
from fetch_fe6_portraits import NAMES  # noqa: E402  (JP name -> English slug)
from sidebar import render_sidebar  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source" / "fe6" / "support"
STUDY = ROOT / "study" / "fe6"
SUPPORT_STUDY = STUDY / "supports"
SUPPORT_TR = ROOT / "translations" / "fe6" / "supports"
WEB = ROOT / "public" / "fe6"
OUT = WEB / "supports"
SOURCE_URL = "https://www.pegasusknight.com/mb/fe6/st_index"

# Mirrors tools/build_fe6.py's PAGES (slug -> JP chapter label -> English
# title), just for the sidebar shown on every support page too. Duplicated
# rather than imported to avoid a circular import (build_fe6.py already
# imports from this module for the character-grid helpers below) - FE6's
# story content is finished, so this should rarely need updating; keep it
# in sync with PAGES if it ever does.
FE6_CHAPTERS = [
    ("ch01", "第1章", "Breath of Fate"), ("ch02", "第2章", "The Princess of Bern"),
    ("ch03", "第3章", "The Latecomer"), ("ch04", "第4章", "Collapse of the Alliance"),
    ("ch05", "第5章", "The Crest of Flame"), ("ch06", "第6章", "The Trap is Set"),
    ("ch07", "第7章", "The Ostia Rebellion"), ("ch08", "第8章", "Reunion"),
    ("ch08x", "第8章外伝", "The Blazing Blade"), ("ch09", "第9章", "The Mist-Shrouded Isle"),
    ("ch10a", "第10章A", "Those Who Resist"), ("ch10b", "第10章B", "Caught Between Conflict"),
    ("ch11a", "第11章A", "Hero of the West"), ("ch11b", "第11章B", "Escape to Freedom"),
    ("ch12", "第12章", "The True Enemy"), ("ch12x", "第12章外伝", "The Thunder Axe"),
    ("ch13", "第13章", "Rescue Operation"), ("ch14", "第14章", "Utopia"),
    ("ch14x", "第14章外伝", "The Reason of Hellfire"), ("ch15", "第15章", "Daughter of the Dragon"),
    ("ch16", "第16章", "Reclaiming the Capital"), ("ch16x", "第16章外伝", "The Supreme Light"),
    ("ch17a", "第17章A", "Teachings of the Priest"), ("ch18a", "第18章A", "The Law of Sacae"),
    ("ch19a", "第19章A", "The Battle for Bulgar"), ("ch20a", "第20章A", "The Grey Wolf"),
    ("ch20xa", "第20章外伝A", "The Gale Bow"), ("ch17b", "第17章B", "The Sea Route"),
    ("ch18b", "第18章B", "The Frozen River"), ("ch19b", "第19章B", "General Winter"),
    ("ch20b", "第20章B", "Liberation of Ilia"), ("ch20xb", "第20章外伝B", "The Ice Lance"),
    ("ch21", "第21章", "The Binding Blade"), ("ch21x", "第21章外伝", "Darkness of Revelation"),
    ("ch22", "第22章", "An Unending Dream"), ("ch23", "第23章", "The Ghost of Bern"),
    ("ch24", "第24章", "The Truth of Legend"), ("ch25", "終章", "Beyond the Darkness"),
]
FE6_BONUS = [
    ("demo", "デモ", "Demo"), ("opening", "オープニング", "Opening"), ("death", "散り際の台詞", "Death Quotes"),
    ("ending1", "エンディング", "Ending (after the Final Chapter)"), ("ending2", "エンディング", "Ending (after Chapter 22)"),
]


def sidebar(current_href, chapter_prefix, supports_href, extra_current=True):
    chapters = [(f"{chapter_prefix}{slug}.html", f"{label} {title}") for slug, label, title in FE6_CHAPTERS]
    bonus = [(f"{chapter_prefix}{slug}.html", f"{label} {title}") for slug, label, title in FE6_BONUS]
    return render_sidebar(chapters, current_href, bonus=bonus,
                           extra=(supports_href, "Support Conversations"), extra_current=extra_current)


BOX_NO = [0]
CURRENT_EN = {}
STUDY_PROBLEMS = []


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

TOKENS, GLOSSARY = {}, []
if (ROOT / "data" / "fe6_tokens.json").exists():
    TOKENS = json.loads((ROOT / "data" / "fe6_tokens.json").read_text(encoding="utf-8"))
    GLOSSARY = json.loads((ROOT / "data" / "fe6_glossary.json").read_text(encoding="utf-8"))
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


def portrait_src(key, depth=2):
    rel = "../" * depth
    if (WEB / "img" / "portraits" / f"{key}.png").exists():
        return f"{rel}img/portraits/{key}.png"
    return f"{rel}img/placeholder.svg"


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


def slug_for(jp_name):
    return NAMES.get(jp_name, jp_name)


def load_translations(slug):
    path, out = SUPPORT_TR / f"{slug}.txt", {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            n, _, text = line.partition("\t")
            if n.strip().isdigit() and text.strip():
                out[int(n)] = text.strip()
    return out


def load_study(slug, texts):
    path = SUPPORT_STUDY / f"{slug}.txt"
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
                STUDY_PROBLEMS.append(f"support/{slug} #{n}: no vocab entry for {key}")
                continue
            if surface.split("#")[0] not in texts.get(n, ""):
                STUDY_PROBLEMS.append(f"support/{slug} #{n}: {surface} is not in the bubble text")
            vocab[key] = [key.split("#")[0]] + VOCAB[key]
            words.append([surface.split("#")[0], key])
        points = []
        for gid in filter(None, (g.strip() for g in parts[2].split(","))):
            if gid not in GRAMMAR:
                STUDY_PROBLEMS.append(f"support/{slug} #{n}: no grammar entry for {gid}")
                continue
            grammar[gid] = GRAMMAR[gid]
            points.append(gid)
        boxes[n] = [words, points]
    return {"v": vocab, "g": grammar, "b": boxes}


def render_items(items, portraits):
    """Group items by rank (C/B/A) and wrap each rank's dialogue in a
    collapsible <details> so a long pair page doesn't show all three ranks
    at once. All three share data-acc="rank" (see site.js), so opening one
    closes the others. The first rank starts open."""
    groups, current = [], None
    for it in items:
        if it["t"] == "rank":
            current = (it["label"], [])
            groups.append(current)
            continue
        if current is None:
            current = (None, [])
            groups.append(current)
        current[1].append(it)

    out = []
    for idx, (label, group_items) in enumerate(groups):
        inner = render_group(group_items, portraits)
        if label is None:
            out.append(inner)
            continue
        open_attr = " open" if idx == 0 else ""
        out.append(
            f'<details class="rank-acc" data-acc="rank" id="rank-{esc(label)}"{open_attr}>'
            f'<summary>Support Rank {esc(label)}</summary>{inner}</details>')
    return "\n".join(out)


def render_group(items, portraits):
    out, i = [], 0
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
<title>{title} | Binding Blade Script</title>
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
<span class="title-group"><a class="site-title" href="{rel}../index.html">Fire Emblem<span>Fan Translations</span></a><a class="game-name" href="{rel}index.html">Binding Blade<span class="orig" lang="ja">封印の剣</span></a></span>
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
<p>Dialogue source: <a href="{source}"><span lang="ja">ファイアーエムブレム 封印の剣・マスターバイブル 支援会話</span></a> (Pegasus Knight).</p>
<p>English translations of the dialogue are unofficial and written for this site.</p>
<p>Fire Emblem: The Binding Blade © Nintendo / Intelligent Systems. Unofficial fan site.</p>
</footer>
</body>
</html>
"""

TOGGLES = ('<button type="button" class="furi-toggle" aria-pressed="false" '
           'title="Show readings above kanji"><span class="knob"></span>Furigana</button>'
           '<button type="button" class="en-toggle" aria-pressed="false" '
           'title="Show the English translation instead of the Japanese text">'
           '<span class="knob"></span>English</button>')


def char_grid(entries, base_rel):
    """entries: list of (jp_name, slug, href_or_None, status_label_or_None)"""
    cells = []
    for jp_name, slug, href, status in entries:
        key = portrait_key(jp_name)
        img = f'<img src="{esc(portrait_src(key, depth=base_rel))}" alt="" width="96" height="128" decoding="async">'
        label = f'<span class="name" lang="ja">{esc(jp_name)}</span>'
        st = f'<span class="status">{esc(status)}</span>' if status else ""
        inner = f'<figure class="char-card">{img}{label}{st}</figure>'
        if href:
            cells.append(f'<li><a href="{href}">{inner}</a></li>')
        else:
            cells.append(f'<li class="todo">{inner}</li>')
    return f'<ul class="char-grid">{"".join(cells)}</ul>'


def parse_all():
    """Parse all 54 support source pages once. Returns (owners, char_scenes, pairs),
    shared by main() here and by build_fe6.py (for the character grid on its own
    index page)."""
    owners = {}          # n -> jp name
    char_scenes = {}      # jp name -> list of partner jp names
    pairs = {}             # frozenset({jp1,jp2}) -> (jp1, jp2, scene)  first-seen wins

    for n in range(1, 55):
        path = SRC / f"st_support{n}.html"
        if not path.exists():
            print(f"MISSING source: st_support{n}.html")
            continue
        raw = path.read_text(encoding="utf-8")
        p = Fe6SupportParser(raw)
        owners[n] = p.owner
        char_scenes.setdefault(p.owner, [])
        for sc in p.scenes:
            jp1, _, jp2 = sc["title"].partition("⇔")
            if not jp2:
                continue
            # A pair's full transcript lives on only ONE of the two characters'
            # pages (whichever is listed first on pegasusknight); the other's
            # page just links to it. Record the relationship on BOTH character
            # pages regardless of which page actually carried the transcript.
            char_scenes.setdefault(jp1, []).append(jp2)
            char_scenes.setdefault(jp2, []).append(jp1)
            key = frozenset((jp1, jp2))
            if key not in pairs:
                pairs[key] = (jp1, jp2, sc)
    return owners, char_scenes, pairs


def character_entries(owners, char_scenes, href_prefix=""):
    """entries for the top-level character grid - reused by build_fe6.py's own
    index page (href_prefix="supports/") and by this module's own supports
    index (href_prefix="")."""
    entries = []
    for n in sorted(owners):
        jp_name = owners[n]
        if not char_scenes.get(jp_name):
            continue  # e.g. マリナス (Merlinus), who genuinely has no supports at all
        slug = slug_for(jp_name)
        entries.append((jp_name, slug, f"{href_prefix}char/{slug}.html", None))
    return entries


def main():
    (OUT / "char").mkdir(parents=True, exist_ok=True)
    (OUT / "pair").mkdir(parents=True, exist_ok=True)
    (OUT / "pair" / "gloss").mkdir(parents=True, exist_ok=True)
    SUPPORT_STUDY.mkdir(parents=True, exist_ok=True)
    SUPPORT_TR.mkdir(parents=True, exist_ok=True)

    owners, char_scenes, pairs = parse_all()
    portraits = {}

    # --- per-pair conversation pages ---
    pair_stats = []
    pair_data = {}
    for key, (jp1, jp2, scene) in sorted(pairs.items(), key=lambda kv: tuple(sorted(slug_for(n) for n in kv[0]))):
        s1, s2 = sorted((slug_for(jp1), slug_for(jp2)))
        pslug = f"{s1}-{s2}"
        BOX_NO[0] = 0
        USED_GLOSS.clear()
        english = load_translations(pslug)
        CURRENT_EN.clear()
        CURRENT_EN.update(english)

        texts, k, rank, windows = {}, 0, None, []
        for it in scene["items"]:
            if it["t"] == "rank":
                rank = it["label"]
            elif it["t"] == "box":
                k += 1
                text = "".join(v for line in it["lines"] for _, v in line)
                texts[k] = text
                windows.append({"n": k, "speaker": it["speaker"], "text": text, "rank": rank})
        pair_data[pslug] = {"jp1": jp1, "jp2": jp2, "windows": windows}
        study = load_study(pslug, texts)
        has_study = study is not None
        boxes = sum(1 for it in scene["items"] if it["t"] == "box")
        pair_stats.append((pslug, boxes, has_study))

        local_portraits = {}
        body_items = render_items(scene["items"], local_portraits)
        portraits.update({k: portraits.get(k, 0) + v for k, v in local_portraits.items()})

        title = f"{jp1}⇔{jp2} Support"
        h1 = f'<span class="num">Support</span>{esc(jp1)}<span lang="ja">⇔</span>{esc(jp2)}'
        body = (f'<nav class="pager"><a class="up" href="../index.html">All Supports</a>'
                f'<a class="up" href="../char/{s1}.html">{esc(jp1)}</a>'
                f'<a class="up" href="../char/{s2}.html">{esc(jp2)}</a></nav>'
                f'<h1>{h1}</h1><main><section class="scene">{body_items}</section></main>'
                '<div class="gloss-backdrop" hidden></div>'
                '<aside class="gloss" aria-live="polite" hidden><div class="gloss-head"><span>Translation</span>'
                '<button type="button" class="gloss-close" aria-label="Close">×</button></div>'
                '<div class="gloss-body"><p class="gloss-hint">Click a speech bubble to see its '
                'translation and vocabulary.</p></div></aside>')
        (OUT / "pair" / "gloss" / f"{pslug}.js").write_text(
            "window.GLOSS=" + json.dumps({g: GLOSSARY[g] for g in sorted(USED_GLOSS)},
                                          ensure_ascii=False, separators=(",", ":")) + ";\n"
            "window.EN=" + json.dumps(english, ensure_ascii=False, separators=(",", ":")) + ";\n"
            + ("window.STUDY=" + json.dumps(study, ensure_ascii=False, separators=(",", ":")) + ";\n"
               if study else ""),
            encoding="utf-8")
        scripts = f'<script src="gloss/{pslug}.js"></script>\n<script src="../../js/site.js"></script>'
        (OUT / "pair" / f"{pslug}.html").write_text(
            PAGE.format(title=title, rel="../../", tools=TOGGLES, scripts=scripts, body=body, source=SOURCE_URL,
                        sidebar=sidebar(None, "../../chapters/", "../index.html")),
            encoding="utf-8")

    # --- per-character partner-index pages ---
    for n in sorted(owners):
        jp_name = owners[n]
        slug = slug_for(jp_name)
        partners = char_scenes.get(jp_name, [])
        entries = []
        for partner in partners:
            s1, s2 = sorted((slug, slug_for(partner)))
            pslug = f"{s1}-{s2}"
            entries.append((partner, slug_for(partner), f"../pair/{pslug}.html", None))
        grid = char_grid(entries, base_rel=2) if entries else '<p class="lead">No support conversations.</p>'
        body = (f'<nav class="pager"><a class="up" href="../index.html">All Supports</a></nav>'
                f'<h1><span class="num">Support Partners</span><span lang="ja">{esc(jp_name)}</span></h1>'
                f'{grid}')
        (OUT / "char" / f"{slug}.html").write_text(
            PAGE.format(title=f"{jp_name} Supports", rel="../../", tools="", scripts="", body=body, source=SOURCE_URL,
                        sidebar=sidebar(None, "../../chapters/", "../index.html")),
            encoding="utf-8")

    # --- top-level support index ---
    entries = character_entries(owners, char_scenes)
    grid = char_grid(entries, base_rel=1)
    translated_pairs = sum(1 for _, _, done in pair_stats if done)
    body = (f'<nav class="pager"><a class="up" href="../index.html">Contents</a></nav>'
            '<h1><span class="num">Fire Emblem</span>Support Conversations'
            '<span class="orig"><span lang="ja">支援会話</span></span></h1>'
            f'<p class="lead">All 54 characters, {len(pairs)} support pairs. '
            f'{translated_pairs} of {len(pairs)} translated so far. Click a character to see their '
            'support partners.</p>'
            f'{grid}')
    (OUT / "index.html").write_text(
        PAGE.format(title="Support Conversations", rel="../", tools="", scripts="", body=body, source=SOURCE_URL,
                    sidebar=sidebar(None, "../chapters/", "index.html")),
        encoding="utf-8")

    (ROOT / "data" / "fe6_supports.json").write_text(
        json.dumps(pair_data, ensure_ascii=False, indent=1), encoding="utf-8")

    rows = sorted(portraits.items(), key=lambda kv: (-kv[1], kv[0]))
    missing = [k for k, _ in rows if not (WEB / "img" / "portraits" / f"{k}.png").exists()]
    print(f"support pairs: {len(pairs)}  translated: {translated_pairs}")
    if missing:
        print("missing portraits:", " ".join(missing))
    if STUDY_PROBLEMS:
        for p in STUDY_PROBLEMS:
            print("STUDY:", p)


if __name__ == "__main__":
    main()
