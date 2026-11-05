#!/usr/bin/env python3
"""Furigana readings + English word glosses for the FE6 script.

Same engine as tools/analyze.py (fugashi + JMdict), just pointed at
data/fe6_script.json (written by tools/build_fe6.py) instead of Thracia's.
Needs fugashi + unidic-lite in .venv, same as analyze.py.

    .venv/bin/python tools/analyze_fe6.py      # then: python3 tools/build_fe6.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Character/place names known so far (grows as more chapters are added).
PROPER = {
    "ロイ": "Roy", "リリーナ": "Lilina", "エリウッド": "Eliwood", "ランス": "Lance",
    "アレン": "Allen", "ボールス": "Bors", "マーカス": "Marcus", "ウォルト": "Wolt",
    "ダマス": "Damas", "スコーラン": "Scorlan", "マリナス": "Marinus",
    "ベルン": "Bern", "オスティア": "Ostia", "リキア": "Lycia", "ファ": "Fa",
    "ゼフィール": "Zephiel", "イドゥン": "Idoun",
}


def main():
    an = analyze.run(
        ROOT / "data" / "fe6_script.json",
        ROOT / "data" / "fe6_tokens.json",
        ROOT / "data" / "fe6_glossary.json",
        proper=PROPER,
    )
    return an


if __name__ == "__main__":
    main()
