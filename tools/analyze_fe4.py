#!/usr/bin/env python3
"""Furigana readings + English word glosses for the FE4 script.

Same engine as tools/analyze.py/analyze_fe6.py, pointed at data/fe4_script.json.
FE4 (Genealogy of the Holy War) is Thracia 776's prequel in the same world, so
this reuses analyze.py's default proper-noun list (en.NAMES + its own PROPER of
Jugdral place names) rather than a separate one - most FE4 character names are
katakana anyway and don't need furigana either way.
Needs fugashi + unidic-lite in .venv, same as analyze.py.

    .venv/bin/python tools/analyze_fe4.py      # then: python3 tools/build_fe4.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    return analyze.run(
        ROOT / "data" / "fe4_script.json",
        ROOT / "data" / "fe4_tokens.json",
        ROOT / "data" / "fe4_glossary.json",
    )


if __name__ == "__main__":
    main()
