#!/usr/bin/env python3
"""Dump one FE6 chapter's text windows with build_fe6.py's exact window numbers.

    python3 tools/dump_fe6_chapter.py ch01

Reading aid for writing study/fe6/<slug>.txt and translations/fe6/<slug>.txt by
hand; changes nothing on disk.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_fe6 as build  # noqa: E402

slug = sys.argv[1]
stem = next(s for s, sl, *_ in build.PAGES if sl == slug)
raw = (build.SRC / f"{stem}.html").read_text(encoding="utf-8")
scenes = [s for s in build.Fe6Parser(raw).scenes if s["items"]]
english = build.load_translations(slug)

n = 0
for s in scenes:
    if s["title"]:
        print(f'\n=== {s["title"]} ===')
    for it in s["items"]:
        if it["t"] == "note":
            print(f'  [{it["kind"]}] {it["text"]}')
        elif it["t"] == "box":
            n += 1
            text = " / ".join("".join(v for _, v in line) for line in it["lines"])
            sp = f" ({it['speaker']})" if it["speaker"] else ""
            print(f'#{n}{sp}: {text}')
            if n in english:
                print(f'    EN: {english[n]}')
print(f"\n[{slug}: {n} windows total]")
