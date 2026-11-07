"""Parser for the FE6 Master Bible pages (pegasusknight.com's current Astro-based
site, not the old Shift_JIS table format Thracia's source/ was saved from).

Page shape, from inspecting source/fe6/st_map1.html's structure:
  <h2 id="IDXn">scene title</h2>
  <p class="note">stage direction / condition</p>
  <p><span class="face_name">NAME</span>first bit of their line</p>
  more text directly, <br/>, more text, <span class="keywait">…</span>  <- window boundary
  <br/>more text<span class="keywait">…</span>                          <- next window, same speaker
  <op code="…"/> <effect eye="1"/>                                     <- inert engine codes, dropped
  <p class="gotomenu"><a href="#">…</a></p>                             <- end-of-scene nav link, dropped

A text window ends at a <span class="keywait"> (the game's "press a button to
continue" point) OR whenever a new <span class="face_name"> or <p class="note">
starts (so the last line before a speaker/scene change, which doesn't always
get its own keywait marker, still closes out as its own window).
"""
import html
import re

TOKEN = re.compile(r"<[^>]*>|[^<]+")
TAG = re.compile(r"<\s*(/?)\s*([A-Za-z0-9]+)([^>]*)>")
CLASS = re.compile(r'class="([^"]*)"')
# Screen-position note right after a speaker's name starts, e.g. " (右)", " (中央左)",
# " (左端)" - where their portrait sits, not something they say. Strip it, don't display it.
POS_TAG = re.compile(r"^\s*[\(（](?:(?:中央)?[右左](?:端)?|画面外)[\)）]")

# tag that must close for each capture label
_CLOSES = {"h2": "h2", "note": "p", "name": "span", "discard": "p", "keywait": "span", "script": "script"}


class Fe6Parser:
    def __init__(self, text):
        self.scenes = []
        self.scene = None
        self.speaker = None
        self.lines = []
        self.buf = []
        self.capture = None  # (label, [text pieces])
        self.keywait_count = 0
        self.expect_pos_tag = False
        main = re.search(r"<main.*?</main>", text, re.S)
        body = main.group(0) if main else text
        start = body.find("<h2")
        body = body[start:] if start != -1 else ""
        # Pages embed a Cloudflare beacon <script> plus a last-updated/credits <dl> block
        # after the real content, both still inside </main> - cut at the first stray
        # </body> that marks the end of the actual transcription.
        end = body.find("</body>")
        if end != -1:
            body = body[:end]
        self.run(body)
        self.flush_window()
        if self.keywait_count == 0:
            self.split_unpaced_narration()

    def split_unpaced_narration(self):
        """A handful of pages (the opening crawl, the tech demo) have no
        <span class="keywait"> at all anywhere, so each scene's whole narration
        lands in one box with many lines - there's no real pacing data to go on.
        Only for THOSE pages, split every multi-line box into one box per line
        instead of showing it as a single huge bubble. Pages that do use keywait
        keep their real window grouping untouched, multi-line windows included."""
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
                # "discard" (gotomenu): nothing to do, just drop the text
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
            self.capture = ("script", [])  # inert CDN/analytics boilerplate, not game text
        elif name == "span" and cls == "face_name" and not closing:
            self.flush_window()  # a new named speaker closes whatever came before
            self.capture = ("name", [])
        elif name == "span" and cls == "keywait" and not closing:
            self.keywait_count += 1
            self.capture = ("keywait", [])  # swallow the "press a button" glyph; closing it ends the window
        elif name == "br":
            self.flush_line()
        # op/effect (self-closing engine codes), a, ul, li, img, hr, plain p/div: no-op
