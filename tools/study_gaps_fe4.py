#!/usr/bin/env python3
"""List content words in an FE4 chapter's bubbles not yet covered by its
study notes file. Read-only reporting tool (no --apply / accept.txt side),
same spirit as tools/study_gaps_fe6.py - surfaces candidates fast so a
chapter's vocab tags can be checked against the whole window set at once.

    .venv/bin/python tools/study_gaps_fe4.py ch01 ch02 ...
"""
import json
import re
import sys
from pathlib import Path

import fugashi

ROOT = Path(__file__).resolve().parent.parent
CONTENT = {"名詞", "動詞", "形容詞", "副詞", "代名詞", "連体詞", "形状詞", "接続詞", "感動詞", "接尾辞", "接頭辞"}
# Character/place names (katakana surface forms) - grows chapter by chapter
# as new named characters/places show up, same role as analyze_fe6.PROPER.
NAMES = {
    "シグルド", "エルトシャン", "キュアン", "アイラ", "アゼル", "エーディン", "ディアドラ",
    "フィン", "ラケシス", "レックス", "バトゥ", "ミデェール", "ジャムカ", "マンフロイ",
    "ガンドルフ", "サンディマ", "キンボイス", "エスリン", "エリオット", "デュー",
    "ヴェルダン", "グランベル", "アグストリア", "イザーク", "シレジア", "ロプト",
    "バルド", "ティルフィング", "ウル", "アンドレイ", "デマ", "ジオ", "ゼル",
    "ゲラルド", "ノイッシュ", "アレク", "オイフェ", "アーダン", "ノディオン", "ユン",
    "シア", "ルフィ", "ブリギッド", "イチイ", "バル", "ヴェルト", "マー", "アルヴィス",
    "エス", "リン", "リターン", "マーファ", "クロス", "ナイツ", "アグ", "スティ",
    "ワープ", "バー", "ハラ", "サイレス", "ジャム",

}
SKIP = {
    "する", "こと", "そう", "それ", "この", "たち", "いう", "ある", "お", "おまえ",
    "ない", "どう", "その", "いる", "あの", "なん", "さま", "もの", "よう", "ここ",
    "これ", "何", "こう", "ご", "ら", "ども", "とも", "ゆえ", "くっ",
}

script = json.loads((ROOT / "data" / "fe4_script.json").read_text(encoding="utf-8"))
tagger = fugashi.Tagger()
slugs = sys.argv[1:]
cands = {}
for slug in slugs:
    boxes = [i for s in script[slug]["scenes"] for i in s["items"] if i["t"] == "box"]
    path = ROOT / "study" / "fe4" / f"{slug}.txt"
    rows = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            parts = line.split("|")
            n, v, g = parts[0], parts[1], parts[2] if len(parts) > 2 else ""
            rows[int(n)] = ([w for w in v.split(",") if w], g)
    for n, box in enumerate(boxes, 1):
        lines = ["".join(v for _, v in l) for l in box["lines"]]
        text = "".join(lines)
        words, g = rows.get(n, ([], ""))
        covered = []
        for w in words:
            s = w.split(">")[0].split("#")[0]
            i = text.find(s)
            if i >= 0:
                covered.append((i, i + len(s)))
        pos = 0
        for line in lines:
            for t in tagger(line):
                a = text.find(t.surface, pos)
                b = a + len(t.surface)
                pos = b
                f = t.feature
                base = f.orthBase or t.surface
                if f.pos1 not in CONTENT or t.surface in NAMES or re.fullmatch(r"[・！？…ー\W\d０-９A-Za-zA-Z]+", t.surface):
                    continue
                if base in SKIP:
                    continue
                if any(a < e and s < b for s, e in covered):
                    continue
                c = cands.setdefault(base, [0, f.pos1, f.lemma, f"{slug}#{n}: {line}"])
                c[0] += 1

for base, (cnt, pos, lemma, ctx) in sorted(cands.items(), key=lambda kv: -kv[1][0]):
    print(f"{base}\t{cnt}\t{pos}\t{lemma}\t{ctx}")
print(len(cands), "uncovered base forms", file=sys.stderr)
