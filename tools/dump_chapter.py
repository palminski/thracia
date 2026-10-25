#!/usr/bin/env python3
"""Dump one chapter's text windows with the exact window numbers build.py assigns them.

    python3 tools/dump_chapter.py <slug>      # e.g. ch04, ch04x, opening, ending, shop

For each window prints: number, scene heading (if any), speaker, and the Japanese
text with the game's own line breaks shown as " / ". Also shows the existing English
translation (translations/<slug>.txt) when present. This is a reading aid for writing
study/<slug>.txt by hand; it changes nothing on disk.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

slug = sys.argv[1]
stem = next(s for s, sl, *_ in build.PAGES if sl == slug)
raw = (build.SRC / f"{stem}.html").read_text(encoding="cp932")
scenes = [s for s in build.Parser(raw).scenes if any(i["t"] in ("box", "note") for i in s["items"])]
scenes = [s for s in scenes if s["title"] or any(i["t"] == "box" for i in s["items"])]
english = build.load_translations(slug)

n = 0
for s in scenes:
    if s["title"]:
        print(f'\n=== {s["title"]}{(" / " + s["sub"]) if s.get("sub") else ""} ===')
    for it in s["items"]:
        if it["t"] == "note":
            print(f'  [{it["kind"]}] {it["text"]}')
        elif it["t"] == "box":
            n += 1
            text = " / ".join("".join(v for _, v in line) for line in it["lines"])
            print(f'#{n} ({it["speaker"]}): {text}')
            if n in english:
                print(f'    EN: {english[n]}')
print(f"\n[{slug}: {n} windows total]")
