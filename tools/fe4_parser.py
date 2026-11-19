"""Parser for the FE4 (Genealogy of the Holy War) Master Bible pages
(pegasusknight.com's current Astro-based site). Page shape is the same as
FE6's st_map pages (see fe6_parser.py's docstring) - this is a thin
adaptation, not a rewrite:

  <h2 id="IDXn">scene title</h2>
  <p class="note">stage direction / condition</p>
  <p><span class="face_name">NAME</span>first bit of their line</p>
  more text directly, <br/>, more text, <span class="keywait">…</span>  <- window boundary
  <br/>more text<span class="keywait">…</span>                          <- next window, same speaker
  <op code="…"/> <effect eye="1"/>                                     <- inert engine codes, dropped
  <p class="gotomenu"><a href="#">…</a></p>                             <- end-of-scene nav link, dropped

One difference from FE6: FE4's screen-position marker after a speaker's name
is (上)/(下) ("top"/"bottom"), not FE6's (右)/(左端)/etc. - same purpose
(strip it, it's not something they say), different glyphs, so POS_TAG covers
both sets.

One quirk unique to this source: st_map7 has two scenes (recruiting/defeating
Tinny) each followed by a giant garbage <table class="dataview">...</table>
block - a template bug on pegasusknight's end that dumps ~1MB of unrelated
ending-narration XML as fake table rows. It's cut before tokenizing, same as
the page-footer Cloudflare beacon script.
"""
import html
import re

TOKEN = re.compile(r"<[^>]*>|[^<]+")
TAG = re.compile(r"<\s*(/?)\s*([A-Za-z0-9]+)([^>]*)>")
CLASS = re.compile(r'class="([^"]*)"')
DATAVIEW_TABLE = re.compile(r'<table class="dataview">.*?</table>', re.S)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
# Screen-position note right after a speaker's name starts: FE6 uses e.g. " (右)",
# " (中央左)", " (左端)", " (画面外)"; FE4 uses " (上)"/" (下)". Strip it, don't display it.
POS_TAG = re.compile(r"^\s*[\(（](?:(?:中央)?[右左](?:端)?|上|下|画面外)[\)）]")

# tag that must close for each capture label
_CLOSES = {"h2": "h2", "note": "p", "name": "span", "discard": "p", "keywait": "span", "script": "script"}


class Fe4Parser:
    def __init__(self, text):
        self.scenes = []
        self.scene = None
        self.speaker = None
        self.lines = []
        self.buf = []
        self.capture = None  # (label, [text pieces])
        self.keywait_count = 0
        self.expect_pos_tag = False
        text = DATAVIEW_TABLE.sub("", text)
        text = HTML_COMMENT.sub("", text)
        main = re.search(r"<main.*?</main>", text, re.S)
        body = main.group(0) if main else text
        start = body.find("<h2")
        body = body[start:] if start != -1 else ""
        end = body.find("</body>")
        if end != -1:
            body = body[:end]
        self.run(body)
        self.flush_window()
        if self.keywait_count == 0:
            self.split_unpaced_narration()

    def split_unpaced_narration(self):
        for scene in self.scenes:
            new_items = []
            for item in scene["items"]:
                if item["t"] == "box" and len(item["lines"]) > 1:
                    for line in item["lines"]:
                        new_items.append({"t": "box", "speaker": item["speaker"], "tag": "", "lines": [line]})
                else:
                    new_items.append(item)
            scene["items"] = new_items

    def new_scene(self, title):
        self.flush_window()
        self.scene = {"title": title, "sub": "", "items": []}
        self.scenes.append(self.scene)
        self.speaker = None

    def emit(self, item):
        if self.scene is None:
            self.new_scene("")
        self.scene["items"].append(item)

    def flush_line(self):
        if self.buf:
            self.lines.append(self.buf)
            self.buf = []

    def flush_window(self):
        self.flush_line()
        lines = [l for l in self.lines if any(v.strip() for _, v in l)]
        self.lines = []
        if lines:
            self.emit({"t": "box", "speaker": self.speaker, "tag": "", "lines": lines})

    def add_text(self, text):
        text = text.replace("\r", "").replace("\n", "")
        if self.expect_pos_tag:
            self.expect_pos_tag = False
            text = POS_TAG.sub("", text, count=1)
        if text:
            self.buf.append(("text", text))

    def run(self, body):
        for tok in TOKEN.findall(body):
            if tok.startswith("<"):
                m = TAG.match(tok)
                if not m:
                    continue
                closing, name, attrs = m.group(1) == "/", m.group(2).lower(), m.group(3)
                selfclose = tok.endswith("/>")
                self.tag(name, closing, attrs, selfclose)
            else:
                text = html.unescape(tok)
                if self.capture is not None:
                    self.capture[1].append(text)
                else:
                    self.add_text(text)

    def tag(self, name, closing, attrs, selfclose):
        if self.capture is not None:
            label = self.capture[0]
            if closing and name == _CLOSES[label]:
                text = "".join(self.capture[1]).strip()
                self.capture = None
                if label == "h2":
                    self.new_scene(text)
                elif label == "note" and text:
                    kind = "cond" if text.startswith("※") else "dir"
                    self.emit({"t": "note", "kind": kind, "text": text})
                elif label == "name":
                    self.speaker = text.strip("[]")
                    self.expect_pos_tag = True
                elif label == "keywait":
                    self.flush_window()
            return
        cls = (CLASS.search(attrs) or [None, None])[1]
        if name == "h2" and not closing:
            self.capture = ("h2", [])
        elif name == "p" and cls == "note" and not closing:
            self.flush_window()
            self.capture = ("note", [])
        elif name == "p" and cls == "gotomenu" and not closing:
            self.capture = ("discard", [])
        elif name == "script" and not closing:
            self.capture = ("script", [])
        elif name == "span" and cls == "face_name" and not closing:
            self.flush_window()
            self.capture = ("name", [])
        elif name == "span" and cls == "keywait" and not closing:
            self.keywait_count += 1
            self.capture = ("keywait", [])
        elif name == "br":
            self.flush_line()
