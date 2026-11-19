#!/usr/bin/env python3
"""Emit N\\t<japanese bubble text> for every window in an FE4 chapter, in
build_fe4.py's exact numbering, as a safe starting point for translation
(prevents hand-numbering drift - only the text after the tab is edited).

    python3 tools/gen_fe4_template.py ch06 > /tmp/ch06_ja.txt
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_fe4 as build  # noqa: E402

slug = sys.argv[1]
stem = next(s for s, sl, *_ in build.PAGES if sl == slug)
raw = (build.SRC / f"{stem}.html").read_text(encoding="utf-8")
scenes = [s for s in build.Fe4Parser(raw).scenes if s["items"]]

n = 0
for s in scenes:
    for it in s["items"]:
        if it["t"] == "box":
            n += 1
            text = " / ".join("".join(v for _, v in line) for line in it["lines"])
            print(f"{n}\t{text}")
print(f"[{slug}: {n} windows total]", file=sys.stderr)
