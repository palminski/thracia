#!/usr/bin/env python3
"""Build the static Thracia 776 script site.

Reads the dialogue transcriptions in source/ (Shift_JIS HTML, saved from the
Pegasus Knight "Master Bible" 会話集) and writes index.html + chapters/*.html.

    python3 tools/build.py

Nothing in the dialogue is written by hand here: every line of game text comes
straight out of the source files.
"""
import html
import json
import re
import sys
from pathlib import Path

import en

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source"
WEB = ROOT / "public"      # what the web server serves (Laravel Forge: web directory /public)
OUT = WEB / "chapters"
SOURCE_URL = "https://www.pegasusknight.com/mb/fe5/st_index.html"

# (source file stem, output slug, short label, chapter title)
# Chapter titles: https://rrpg.jp/fe_thracia/ (攻略 pages).
PAGES = [
    ("st_opening", "opening", "オープニング", ""),
    ("st_sce01", "ch01", "第１章", "フィアナの戦士"),
    ("st_sce02", "ch02", "第２章", "イスの海岸"),
    ("st_sce02a", "ch02x", "第２章外伝", "海賊島"),
    ("st_sce03", "ch03", "第３章", "ケルベスの門"),
    ("st_sce04", "ch04", "第４章", "地下牢獄"),
    ("st_sce04a", "ch04x", "第４章外伝", "風の勇者"),
    ("st_sce05", "ch05", "第５章", "母と娘"),
    ("st_sce06", "ch06", "第６章", "脱出"),
    ("st_sce07", "ch07", "第７章", "トラキアの盾"),
    ("st_sce08", "ch08", "第８章", "紫竜山"),
    ("st_sce08a", "ch08x", "第８章外伝", "ダグダの館"),
    ("st_sce09", "ch09", "第９章", "ノヴァの紋章"),
    ("st_sce10", "ch10", "第１０章", "ノエル渓谷"),
    ("st_sce11", "ch11", "第１１章", "ダンドラム要塞"),
    ("st_sce11a", "ch11x", "第１１章外伝", "マーダーホレス"),
    ("st_sce12", "ch12", "第１２章", "ダキアの盗賊"),
    ("st_sce12a", "ch12x", "第１２章外伝", "ダンディライオン"),
    ("st_sce13", "ch13", "第１３章", "城塞都市"),
    ("st_sce14", "ch14", "第１４章", "総攻撃"),
    ("st_sce14a", "ch14x", "第１４章外伝", "自由を求めて"),
    ("st_sce15", "ch15", "第１５章", "二つの道"),
    ("st_sce16a", "ch16a", "第１６章Ａ", "ノルデンライン"),
    ("st_sce17a", "ch17a", "第１７章Ａ", "レンスターゲイト"),
    ("st_sce16b", "ch16b", "第１６章Ｂ", "暗黒の森"),
    ("st_sce17b", "ch17b", "第１７章Ｂ", "５月の雨"),
    ("st_sce18", "ch18", "第１８章", "王都解放"),
    ("st_sce19", "ch19", "第１９章", "帝国の反撃"),
    ("st_sce20", "ch20", "第２０章", "光の公子"),
    ("st_sce21", "ch21", "第２１章", "解放戦争"),
    ("st_sce21a", "ch21x", "第２１章外伝", "捕虜収容所"),
    ("st_sce22", "ch22", "第２２章", "渡河作戦"),
    ("st_sce23", "ch23", "第２３章", "魔王の城"),
    ("st_sce24", "ch24", "第２４章", "黒衣の男爵"),
    ("st_sce24a", "ch24x", "第２４章外伝", "ロプトの祭壇"),
    ("st_sce25", "ch25", "最終章", "誓いの剣"),
    ("st_ending", "ending", "エンディング", ""),
    ("st_escape", "escape", "去り際の言葉", ""),
    ("st_death", "death", "散り際の言葉", ""),
    ("st_shop", "shop", "ショップ", ""),
    ("st_others", "others", "その他", ""),
]
EXTRA_FROM = "ending"  # pages from here on are listed under "その他" on the index

TOKEN = re.compile(r"<[^>]*>|[^<]+")
# Headings like 「ワイズマン初戦時」: the unlabelled quote belongs to that unit.
QUOTE_HEADING = re.compile(r"^(.+?)(初戦時|打倒時|解放時|捕獲時)")


# ---------------------------------------------------------------- parsing --

class Parser:
    """Turns one source page into a list of scenes.

    scene = {"title", "sub", "items"}; items are a flat stream of
      {"t": "open"} / {"t": "close"}             nested block (<DIV class=b>)
      {"t": "note", "kind": cond|dir|mark|ref, "text"}   editorial annotation
      {"t": "box", "speaker", "tag", "lines"}    one in-game text window
    """

    def __init__(self, text):
        self.scenes = []
        self.scene = None
        self.speaker = None
        self.stack = []          # speaker saved at each block open
        self.in_p = False
        self.p_class = None
        self.parts = []          # pieces of the paragraph being read
        self.skip = None         # tag whose contents are being dropped
        self.skip_depth = 0
        self.capture = None      # ("h2"|"h4"|"b"|"td", [text])
        self.row = None
        self.page_title = ""
        self.run(text)

    # -- helpers
    def new_scene(self, title):
        m = re.match(r"^(.*?)（(.*)）$", title)
        base, sub = (m.group(1), m.group(2)) if m and m.group(1) else (title, "")
        self.scene = {"title": base, "sub": sub, "items": []}
        self.scenes.append(self.scene)
        self.speaker = None
        self.stack = []
        qm = QUOTE_HEADING.match(base)
        self.default_speaker = qm.group(1) if qm else None

    def emit(self, item):
        if self.scene is None:
            self.new_scene("")
        self.scene["items"].append(item)

    def open_p(self, cls=None):
        self.close_p()
        self.in_p, self.p_class, self.parts = True, cls, []

    def close_p(self):
        if not self.in_p:
            return
        self.in_p = False
        parts, self.parts = self.parts, []
        # A paragraph that is only a bold annotation is an editor's note.
        solid = [p for p in parts if p[0] != "br" and not (p[0] == "text" and not p[1].strip())]
        if self.p_class == "m":
            text = "".join(p[1] for p in parts if p[0] in ("text", "b")).strip()
            if text:
                self.emit({"t": "note", "kind": "mark", "text": text})
            return
        if len(solid) == 1 and solid[0][0] == "b":
            self.note_from_bold(solid[0][1])
            return
        tag = ""
        if solid and solid[0][0] == "b" and re.fullmatch(r"\[.*\]", solid[0][1].strip()):
            self.speaker = solid[0][1].strip()[1:-1]
            i = parts.index(solid[0])
            parts = parts[i + 1:]
            # 「[店の親父]（上）」: window position noted after the name
            if parts and parts[0][0] == "text" and re.fullmatch(r"（.*）", parts[0][1].strip()):
                tag = parts[0][1].strip()
                parts = parts[1:]
        lines, cur, trailing = [], [], []
        for kind, val in parts:
            if kind == "br":
                lines.append(cur)
                cur = []
            elif kind == "b" and not cur and re.fullmatch(r"（.*）", val.strip()):
                trailing.append(val.strip())   # stage direction on its own line
            else:
                cur.append((kind, val))
        lines.append(cur)
        lines = [l for l in lines if any(v.strip() for _, v in l)]
        if any("情報提供して頂きました" in v for l in lines for _, v in l):
            return                       # the transcriber's thank-you note, not game text
        if lines:
            self.emit({"t": "box", "speaker": self.speaker or self.default_speaker,
                       "tag": tag, "lines": lines})
        for d in trailing:
            self.emit({"t": "note", "kind": "dir", "text": d})

    def note_from_bold(self, text):
        text = text.strip()
        self.emit({"t": "note", "kind": "cond" if text.startswith("※") else "dir", "text": text})

    def add_text(self, text):
        text = text.replace("\r", "").replace("\n", "")
        if not self.in_p:
            if not text.strip():
                return
            self.open_p()
        self.parts.append(("text", text))

    # -- main loop
    def run(self, text):
        for tok in TOKEN.findall(text):
            if tok.startswith("<"):
                m = re.match(r"<\s*(/?)\s*([A-Za-z0-9]+)([^>]*)>", tok)
                if not m:
                    continue
                closing, name, attrs = m.group(1) == "/", m.group(2).lower(), m.group(3)
                self.tag(name, closing, attrs)
            elif self.skip:
                continue
            elif self.capture:
                self.capture[1].append(html.unescape(tok))
            elif self.row is None or self.capture:
                self.add_text(html.unescape(tok))
        self.close_p()

    def tag(self, name, closing, attrs):
        if self.skip:
            if name == self.skip:
                self.skip_depth += -1 if closing else 1
                if self.skip_depth == 0:
                    self.skip = None
            return
        cls = (re.search(r'class="([^"]*)"', attrs) or [None, None])[1]
        if name in ("script", "font", "head") or (name == "div" and cls in ("c", "s")) or \
                (name == "a" and "href" in attrs and self.capture is None and self.row is None and not self.in_p):
            if not closing:
                self.skip, self.skip_depth = name, 1   # footer links, ▼ markers, commentary
            return
        if name in ("h2", "h4"):
            if not closing:
                self.close_p()
                self.capture = (name, [])
            elif self.capture:
                text = "".join(self.capture[1]).strip()
                self.capture = None
                if name == "h2":
                    self.page_title = text
                elif text.lstrip("■") and not text.startswith("Thanks"):
                    self.new_scene(text.lstrip("■"))
                else:
                    self.skip_rest = True
                    self.scene = {"title": "", "sub": "", "items": []}  # discard credits
            return
        if name == "div":
            self.close_p()
            if closing:
                if self.stack:
                    self.speaker = self.stack.pop()
                    self.emit({"t": "close"})
            else:
                self.stack.append(self.speaker)
                self.emit({"t": "open"})
            return
        if name == "tr":
            self.row = None if closing else []
            if closing and self.pending_row:
                self.table_row(self.pending_row)
            self.pending_row = [] if not closing else None
            return
        if name in ("td", "th"):
            if not closing:
                self.capture = (name, [])
            elif self.capture:
                if name == "td" and self.pending_row is not None:
                    self.pending_row.append("".join(self.capture[1]))
                self.capture = None
            return
        if name == "br":
            if self.capture:
                self.capture[1].append("\n")
            elif self.in_p:
                self.parts.append(("br", ""))
            return
        if self.capture and self.capture[0] != "b":
            return                      # ignore inline tags inside headings/cells
        if name == "p":
            if closing:
                self.close_p()
            else:
                self.open_p(cls)
            return
        if name == "b":
            if not closing:
                self.capture = ("b", [])
            elif self.capture:
                text = "".join(self.capture[1])
                self.capture = None
                if self.in_p:
                    self.parts.append(("b", text))
                else:
                    self.note_from_bold(text)
            return

    pending_row = None
    default_speaker = None

    def table_row(self, cells):
        """去り際 / 散り際 tables: chapter | name | quote."""
        if len(cells) != 3:
            return
        chap, name, quote = (c.replace("\r", "").strip() for c in cells)
        lines, refs = [], []
        for line in quote.split("\n"):
            line = line.strip()
            if not line:
                continue
            (refs if line.startswith("（→") else lines).append(line)
        self.emit({"t": "open"})
        self.emit({"t": "note", "kind": "mark", "text": f"{name}（登場章：{chap}）"})
        if lines:
            self.emit({"t": "box", "speaker": name, "tag": "", "lines": [[("text", l)] for l in lines]})
        for r in refs:
            self.emit({"t": "note", "kind": "ref", "text": r})
        self.emit({"t": "close"})


# -------------------------------------------------------------- rendering --

MISSING = set()


def tr(fn, text):
    """English for an editorial label; falls back to the Japanese (and reports it)."""
    try:
        return fn(text)
    except en.Unknown:
        MISSING.add(text)
        return text


def jp(s):
    return f'<span lang="ja">{esc(s)}</span>'


def esc(s):
    return html.escape(s, quote=True)


def portrait_key(speaker):
    """File name (without .png) looked up in img/portraits/ for a speaker."""
    s = speaker.replace("（", "(").replace("）", ")")
    m = re.search(r"\((.+?)顔\)$", s)      # 「兵士(アイヒマン顔)」 uses アイヒマン's face
    if m:
        return m.group(1)
    return s.replace("/", "／").replace("?", "？")


def portrait_src(key):
    """Portrait if img/portraits/<key>.png exists at build time, else the placeholder."""
    if (WEB / "img" / "portraits" / f"{key}.png").exists():
        return f"../img/portraits/{key}.png"
    return "../img/placeholder.svg"


# Word analysis made by tools/analyze.py (optional: without it pages have plain text).
TOKENS, GLOSSARY = {}, []
if (ROOT / "data" / "tokens.json").exists():
    TOKENS = json.loads((ROOT / "data" / "tokens.json").read_text(encoding="utf-8"))
    GLOSSARY = json.loads((ROOT / "data" / "glossary.json").read_text(encoding="utf-8"))
USED_GLOSS = set()      # glossary ids used by the page being rendered
BOX_NO = [0]            # running number of the text window on the page being rendered


def box_html(b):
    BOX_NO[0] += 1
    return f'<p class="box" data-n="{BOX_NO[0]}" tabindex="0">{render_lines(b["lines"])}</p>'


def load_table(name):
    """study/<name>.txt: "key | a | b" lines -> {key: [a, b]}  (lines starting with # are comments)"""
    path, out = ROOT / "study" / f"{name}.txt", {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 3 and not line.startswith("#"):
                out[parts[0]] = parts[1:]
    return out


VOCAB = load_table("vocab")        # key -> [reading, meaning]
GRAMMAR = load_table("grammar")    # id  -> [pattern, explanation]
STUDY_PROBLEMS = []


def load_study(slug, texts):
    """study/<slug>.txt: "window | word,word>key,... | grammar ids" -> data for the page.

    Returns None when the chapter has no hand-written notes (the page then falls back to the
    automatic dictionary list). `texts` maps window number -> its Japanese text, for checking.
    """
    path = ROOT / "study" / f"{slug}.txt"
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
    """translations/<slug>.txt: one "<window number><TAB><English>" per line -> {n: text}"""
    path = ROOT / "translations" / f"{slug}.txt"
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            n, _, text = line.partition("\t")
            if n.strip().isdigit() and text.strip():
                out[int(n)] = text.strip()
    return out


def ruby(text):
    """Script text with each word wrapped for lookup and <ruby> readings on kanji."""
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


def render_lines(lines):
    out = []
    for line in lines:
        buf = "".join(f'<b lang="en">{esc(tr(en.direction, v))}</b>' if k == "b" else ruby(v) for k, v in line)
        out.append(f'<span class="ln">{buf}</span>')
    return "<br>\n".join(out)


def render_scene(scene, portraits):
    out, i, items = [], 0, scene["items"]
    sides, last_side = {}, "r"
    while i < len(items):
        it = items[i]
        if it["t"] == "open":
            prev = items[i - 1] if i else None
            branch = prev is not None and prev["t"] == "note" and prev["kind"] == "cond"
            out.append(f'<div class="block{" branch" if branch else ""}">')
        elif it["t"] == "close":
            out.append("</div>")
        elif it["t"] == "note":
            fn = {"cond": en.cond, "mark": en.mark}.get(it["kind"], en.direction)
            out.append(f'<p class="note note-{it["kind"]}">{esc(tr(fn, it["text"]))}</p>')
        else:
            # gather consecutive windows from the same speaker into one turn
            j = i
            while j < len(items) and items[j]["t"] == "box" and \
                    items[j]["speaker"] == it["speaker"] and items[j]["tag"] == it["tag"]:
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
                tag = f' <span class="tag" lang="en">{esc(tr(en.direction, it["tag"]))}</span>' if it["tag"] else ""
                out.append(
                    f'<div class="turn {side}" data-speaker="{esc(sp)}">'
                    f'<figure class="who"><img src="{esc(portrait_src(key))}" data-portrait="{esc(key)}" alt="" '
                    f'width="96" height="128" decoding="async">'
                    f'<figcaption lang="ja">{esc(sp)}{tag}</figcaption></figure>'
                    f'<div class="bubbles" lang="ja">{boxes}</div></div>')
            i = j
            continue
        i += 1
    return "\n".join(out)


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Thracia 776 Script</title>
<link rel="stylesheet" href="{rel}css/style.css">
<script>try {{ if (localStorage.getItem("furigana") === "1") document.documentElement.classList.add("furi"); }} catch (e) {{}}</script>
</head>
<body>
<header class="site"><div class="bar">
<a href="{rel}index.html">Fire Emblem: Thracia 776 <span>Japanese Script</span></a>
<nav class="tools"><a href="{rel}grammar.html">Grammar</a><a href="{rel}vocab.html">Vocabulary</a>{tools}</nav>
</div></header>
{body}
{scripts}
<footer class="site">
<p>Dialogue source: <a href="{source}"><span lang="ja">ファイアーエムブレム トラキア776・マスターバイブル 会話集</span></a> (Pegasus Knight).</p>
<p>English translations of the dialogue are unofficial and written for this site. Word meanings: <a href="https://www.edrdg.org/jmdict/j_jmdict.html">JMdict</a> © Electronic Dictionary Research and Development Group, CC BY-SA 4.0. Readings and word matching are automatic and can be wrong.</p>
<p>Fire Emblem: Thracia 776 © Nintendo / INTELLIGENT SYSTEMS. Unofficial fan site.</p>
</footer>
</body>
</html>
"""


FURI_TOGGLE = ('<button type="button" class="furi-toggle" aria-pressed="false" '
               'title="Show readings above kanji"><span class="knob"></span>Furigana</button>')


def nav(idx, pages):
    lab = lambda i: esc(en.CHAPTERS[pages[i][1]][0])
    prev = f'<a class="prev" href="{pages[idx-1][1]}.html">← {lab(idx-1)}</a>' if idx else "<span></span>"
    nxt = f'<a class="next" href="{pages[idx+1][1]}.html">{lab(idx+1)} →</a>' if idx + 1 < len(pages) else "<span></span>"
    return f'<nav class="pager">{prev}<a class="up" href="../index.html">Contents</a>{nxt}</nav>'


def write_reference_pages(studied):
    """grammar.html and vocab.html: everything in study/grammar.txt and study/vocab.txt."""
    done = ", ".join(en.CHAPTERS[s][0] for s in studied) or "no chapters yet"
    rows = "\n".join(
        f'<section class="ref" id="{esc(gid)}"><h2 lang="ja">{esc(pat)}</h2><p>{esc(expl)}</p></section>'
        for gid, (pat, expl) in GRAMMAR.items())
    body = ('<h1><span class="num">Reference</span>Grammar points</h1>\n'
            f'<p class="lead">Every grammar note used in the per-bubble notes so far ({esc(done)}). '
            'Click a speech bubble in a chapter to see which ones apply to it.</p>\n<main>' + rows + '</main>')
    (WEB / "grammar.html").write_text(
        PAGE.format(title="Grammar points", rel="", body=body, source=SOURCE_URL, tools="", scripts=""),
        encoding="utf-8")
    rows = "\n".join(
        f'<tr><td lang="ja">{esc(key.split("#")[0])}</td><td lang="ja">{esc(rd)}</td><td>{esc(mean)}</td></tr>'
        for key, (rd, mean) in VOCAB.items())
    body = ('<h1><span class="num">Reference</span>Vocabulary</h1>\n'
            f'<p class="lead">Every word glossed in the per-bubble notes so far ({esc(done)}), '
            'in order of first appearance.</p>\n<main><table class="vocab"><thead><tr><th>Word</th>'
            '<th>Reading</th><th>Meaning</th></tr></thead><tbody>' + rows + '</tbody></table></main>')
    (WEB / "vocab.html").write_text(
        PAGE.format(title="Vocabulary", rel="", body=body, source=SOURCE_URL, tools="", scripts=""),
        encoding="utf-8")


def main():
    OUT.mkdir(exist_ok=True)
    portraits, stats, data, translated, studied = {}, [], {}, {}, []
    for idx, (stem, slug, label, title) in enumerate(PAGES):
        USED_GLOSS.clear()
        BOX_NO[0] = 0
        raw = (SRC / f"{stem}.html").read_text(encoding="cp932")
        scenes = [s for s in Parser(raw).scenes if any(i["t"] in ("box", "note") for i in s["items"])]
        scenes = [s for s in scenes if s["title"] or any(i["t"] == "box" for i in s["items"])]
        boxes = sum(1 for s in scenes for i in s["items"] if i["t"] == "box")
        stats.append((slug, len(scenes), boxes))
        data[slug] = {"label": label, "title": title, "scenes": scenes}

        en_label, en_title = en.CHAPTERS[slug]

        def heading(s):
            head = tr(en.title, s["title"]) if s["title"] else en_label
            return head + (f' ({tr(en.sub, s["sub"])})' if s["sub"] else "")

        toc = "\n".join(
            f'<li><a href="#s{n}">{esc(heading(s))}</a></li>' for n, s in enumerate(scenes, 1))
        h1 = f'<span class="num">{esc(en_label)}</span>{esc(en_title)}'
        if title:
            h1 += f'<span class="orig">{jp(label + "　" + title)}</span>'
        parts = [nav(idx, PAGES),
                 f'<h1>{h1}</h1>',
                 f'<details class="toc"><summary>Scenes ({len(scenes)})</summary><ol>{toc}</ol></details>',
                 "<main>"]
        for n, s in enumerate(scenes, 1):
            sub = f' <small>{esc(tr(en.sub, s["sub"]))}</small>' if s["sub"] else ""
            parts.append(f'<section class="scene" id="s{n}">')
            if s["title"]:
                parts.append(f'<h2><a href="#s{n}">{esc(tr(en.title, s["title"]))}</a>{sub}</h2>')
            parts.append(render_scene(s, portraits))
            parts.append("</section>")
        parts += ["</main>", nav(idx, PAGES),
                  '<div class="gloss-backdrop" hidden></div>'
                  '<aside class="gloss" aria-live="polite" hidden><div class="gloss-head"><span>Translation</span>'
                  '<button type="button" class="gloss-close" aria-label="Close">×</button></div>'
                  '<div class="gloss-body"><p class="gloss-hint">Click a speech bubble to see its '
                  'translation and vocabulary.</p></div></aside>']
        english = load_translations(slug)
        texts, k = {}, 0
        for s in scenes:
            for it in s["items"]:
                if it["t"] == "box":
                    k += 1
                    texts[k] = "".join(v for line in it["lines"] for _, v in line)
        study = load_study(slug, texts)
        if study:
            studied.append(slug)
        extra = sorted(n for n in english if n > BOX_NO[0])
        if extra:
            print(f"WARNING {slug}: translation lines beyond window {BOX_NO[0]}: {extra[:5]}")
        translated[slug] = (len([n for n in english if n <= BOX_NO[0]]), BOX_NO[0])
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
            PAGE.format(title=f"{en_label} {en_title}".strip(), rel="../", tools=FURI_TOGGLE, scripts=scripts, body="\n".join(parts), source=SOURCE_URL),
            encoding="utf-8")

    # index
    split = next(i for i, p in enumerate(PAGES) if p[1] == EXTRA_FROM)
    def li(p):
        en_label, en_title = en.CHAPTERS[p[1]]
        t = f'<span class="title">{esc(en_title)}</span>' if en_title else ""
        orig = p[2] + ("　" + p[3] if p[3] else "")
        cls = ' class="gaiden"' if p[1].endswith("x") else ""
        return (f'<li{cls}><a href="chapters/{p[1]}.html"><span class="num">{esc(en_label)}</span>{t}'
                f'<span class="orig">{jp(orig)}</span></a></li>')
    body = (
        '<h1><span class="num">Fire Emblem</span>Thracia 776 Japanese Script'
        '<span class="orig"><span lang="ja">ファイアーエムブレム トラキア776 会話集</span></span></h1>\n'
        '<p class="lead">Every chapter\'s dialogue in the original Japanese, with the game\'s own line breaks '
        'and text-window breaks.</p>\n'
        '<h2 class="idx">Main story</h2>\n<ol class="chapters">\n' + "\n".join(li(p) for p in PAGES[:split]) + "\n</ol>\n"
        '<h2 class="idx">Ending &amp; extras</h2>\n<ol class="chapters">\n' + "\n".join(li(p) for p in PAGES[split:]) + "\n</ol>")
    (WEB / "index.html").write_text(
        PAGE.format(title="Contents", rel="", tools="", scripts="", body=body, source=SOURCE_URL), encoding="utf-8")

    # machine-readable copy of the script (handy for the translation feature later)
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "script.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    # list of portrait files the pages look for
    rows = sorted(portraits.items(), key=lambda kv: -kv[1])
    (WEB / "img" / "portraits" / "README.txt").write_text(
        "Drop portraits here as <name>.png (3:4, e.g. 48x64 or 96x128).\n"
        "Then re-run: python3 tools/build.py\n"
        "Any missing file falls back to img/placeholder.svg.\n\n"
        "file name\ttimes used\n" + "\n".join(f"{k}.png\t{v}" for k, v in rows) + "\n", encoding="utf-8")

    for slug, ns, nb in stats:
        print(f"{slug:8} scenes={ns:3} boxes={nb:4}")
    for m in sorted(MISSING):
        print("UNTRANSLATED:", m)
    write_reference_pages(studied)
    for p in STUDY_PROBLEMS:
        print("STUDY:", p)
    print("hand-written vocabulary + grammar notes:", " ".join(studied) or "none")
    print("translated windows:", sum(a for a, _ in translated.values()), "/", sum(b for _, b in translated.values()),
          "| chapters incomplete:", " ".join(s for s, (a, b) in translated.items() if a < b) or "none")
    print("total boxes:", sum(s[2] for s in stats), "| portrait keys:", len(portraits))


if __name__ == "__main__":
    sys.exit(main())
