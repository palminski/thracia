#!/usr/bin/env python3
"""List content words in a chapter's bubbles that its study file doesn't cover yet.

    .venv/bin/python tools/study_gaps.py ch01 ch02 ...          # print candidates
    .venv/bin/python tools/study_gaps.py --apply ch01 ch02 ...  # add those found in study/accept.txt

The tokenizer is only used to *find* uncovered words. Meanings still come from
study/vocab.txt; study/accept.txt maps "tokenizer base form | vocab key" for words to add
("-" as the key means "never add this one").
"""
import json, re, sys
from pathlib import Path
import fugashi
sys.path.insert(0, str(Path(__file__).parent))
import en, analyze

ROOT = Path(__file__).resolve().parent.parent
CONTENT = {"名詞", "動詞", "形容詞", "副詞", "代名詞", "連体詞", "形状詞", "接続詞", "感動詞", "接尾辞", "接頭辞"}
NAMES = set(en.NAMES) | set(analyze.PROPER)
apply = "--apply" in sys.argv
slugs = [a for a in sys.argv[1:] if not a.startswith("--")]
script = json.loads((ROOT / "data" / "script.json").read_text(encoding="utf-8"))
tagger = fugashi.Tagger()
accept = {}
p = ROOT / "study" / "accept.txt"
if p.exists():
    for line in p.read_text(encoding="utf-8").splitlines():
        parts = [x.strip() for x in line.split("|")]
        if len(parts) == 2 and not line.startswith("#"):
            accept[parts[0]] = parts[1]
cands = {}
for slug in slugs:
    boxes = [i for s in script[slug]["scenes"] for i in s["items"] if i["t"] == "box"]
    path = ROOT / "study" / f"{slug}.txt"
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        n, v, g = line.split("|")
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
        pos, new = 0, []
        for line in lines:
            for t in tagger(line):
                a = text.find(t.surface, pos); b = a + len(t.surface); pos = b
                f = t.feature
                base = f.orthBase or t.surface
                if f.pos1 not in CONTENT or t.surface in NAMES or re.fullmatch(r"[・！？…ー\W\d０-９A-Za-zＡ-Ｚ]+", t.surface):
                    continue
                if any(a < e and s < b for s, e in covered):
                    continue
                if accept.get(base) == "-":
                    continue
                if base in accept:
                    new.append((a, f"{t.surface}>{accept[base]}" if t.surface != accept[base] else t.surface))
                    covered.append((a, b))
                else:
                    c = cands.setdefault(base, [0, f.pos1, f.lemma, line])
                    c[0] += 1
        if apply and new:
            allw = [(text.find(w.split(">")[0].split("#")[0]), w) for w in words] + new
            rows[n] = ([w for _, w in sorted(allw, key=lambda x: x[0])], g)
    if apply:
        path.write_text("".join(f"{n}|{','.join(rows[n][0])}|{rows[n][1]}\n" for n in sorted(rows)), encoding="utf-8")
for base, (cnt, pos, lemma, ctx) in sorted(cands.items(), key=lambda kv: -kv[1][0]):
    print(f"{base}\t{cnt}\t{pos}\t{lemma}\t{ctx}")
print(len(cands), "uncovered base forms", file=sys.stderr)
