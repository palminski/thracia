#!/usr/bin/env python3
"""Furigana readings + English word glosses for ALL of FE6's Japanese text:
the main-story chapters (data/fe6_script.json) AND the 143 support-pair
conversations (parsed fresh from source/fe6/support/*.html, same as
tools/build_fe6_supports.py does) - in one combined pass, so both sets of
pages share the same data/fe6_tokens.json / data/fe6_glossary.json and the
furigana/English toggles work identically everywhere.

Needs fugashi + unidic-lite in .venv, same as analyze.py/analyze_fe6.py.

    .venv/bin/python tools/analyze_fe6_full.py
    then: python3 tools/build_fe6.py && python3 tools/build_fe6_supports.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze  # noqa: E402
from analyze_fe6 import PROPER  # noqa: E402
from fe6_support_parser import Fe6SupportParser  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source" / "fe6" / "support"


def support_pages():
    """Same first-seen-pair dedup as tools/build_fe6_supports.py's main(), just
    returning {page_key: {"scenes": [scene]}} instead of rendering HTML."""
    pairs = {}
    for n in range(1, 55):
        path = SRC / f"st_support{n}.html"
        if not path.exists():
            continue
        p = Fe6SupportParser(path.read_text(encoding="utf-8"))
        for sc in p.scenes:
            jp1, _, jp2 = sc["title"].partition("⇔")
            if not jp2:
                continue
            key = frozenset((jp1, jp2))
            if key not in pairs:
                pairs[key] = sc
    return {f"support_{i}": {"scenes": [sc]} for i, sc in enumerate(pairs.values())}


def main():
    script = json.loads((ROOT / "data" / "fe6_script.json").read_text(encoding="utf-8"))
    script.update(support_pages())
    tmp = ROOT / "data" / ".fe6_combined_script.json"
    tmp.write_text(json.dumps(script, ensure_ascii=False), encoding="utf-8")
    try:
        analyze.run(tmp, ROOT / "data" / "fe6_tokens.json", ROOT / "data" / "fe6_glossary.json", proper=PROPER)
    finally:
        tmp.unlink()


if __name__ == "__main__":
    main()
