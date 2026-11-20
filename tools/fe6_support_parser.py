"""Parser for FE6's 54 support-conversation pages (pegasusknight.com). Same
underlying markup as the main-story pages (see fe6_parser.py's docstring),
plus two extra wrinkles specific to these pages:

  <h1>会話集/支援会話/ロイ</h1>                 <- page owner's name
  <h2 id="IDXn">ロイ⇔マーカス</h2>              <- one scene per support PAIR
  <h3>支援レベルC</h3>                          <- rank marker, C/B/A in order
  ... dialogue, same <p class="face_name">/<span class="keywait"> pattern ...

Fe6Parser already treats <h2> as a scene boundary, which is exactly right
here (one scene per pair). <h3> isn't handled by the base parser at all, so
this subclass adds it as a "rank" item marking where each C/B/A section
starts within the pair's scene.
"""
import re

from fe6_parser import Fe6Parser, TOKEN, TAG, CLASS

OWNER = re.compile(r"会話集/支援会話/([^<]+)</h1>")


class Fe6SupportParser(Fe6Parser):
    def __init__(self, text):
        m = OWNER.search(text)
        self.owner = m.group(1).strip() if m else None
        super().__init__(text)

    def tag(self, name, closing, attrs, selfclose):
        if self.capture is not None and self.capture[0] == "h3":
            if closing and name == "h3":
                text = "".join(self.capture[1]).strip()
                self.capture = None
                # Normally "支援レベルC/B/A"; one pair (Bors<->Wendy) uses "会話C/B"
                # for its first two ranks instead, same meaning, different label.
                label = re.sub(r"^(支援レベル|会話)", "", text).strip()
                self.emit({"t": "rank", "label": label})
            return
        if name == "h3" and not closing:
            self.flush_window()
            self.capture = ("h3", [])
            return
        super().tag(name, closing, attrs, selfclose)
