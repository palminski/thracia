#!/usr/bin/env python3
"""Analyse every script line: furigana readings + English word glosses.

Writes data/tokens.json (line -> words) and data/glossary.json (dictionary entries).
Needs the tokenizer in the project virtualenv (fugashi + unidic-lite); downloads the
JMdict dictionary into .cache/ on first run.

    .venv/bin/python tools/analyze.py      # then: python3 tools/build.py

Everything here is machine output: the tokenizer guesses word boundaries and readings,
and the gloss is the JMdict entry that best fits. It is usually right and sometimes
wrong, especially where the game writes a word in kana that has homophones.
Fix individual cases in OVERRIDES / COMPOUNDS / GLOSS_FIXES below and re-run.

Dictionary: JMdict, (c) Electronic Dictionary Research and Development Group,
CC BY-SA 4.0 - https://www.edrdg.org/jmdict/j_jmdict.html
"""
import gzip
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import fugashi

sys.path.insert(0, str(Path(__file__).parent))
import en  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
JMDICT = ROOT / ".cache" / "JMdict_e.gz"
JMDICT_URL = "http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz"
KANJI = r"[\u3400-\u9fff\uf900-\ufaff々〆ヶ]"
HAS_KANJI = re.compile(KANJI)

# word as the tokenizer splits it -> reading (hiragana)
OVERRIDES = {
    "私": "わたし",
    "金": "かね",
}

# phrases the tokenizer reads wrongly -> fixed segmentation
COMPOUNDS = {
    "父上": [("父", "ちち"), ("上", "うえ")], "母上": [("母", "はは"), ("上", "うえ")],
    "兄上": [("兄", "あに"), ("上", "うえ")], "姉上": [("姉", "あね"), ("上", "うえ")],
    "妹君": [("妹", "いもうと"), ("君", "ぎみ")], "お頭": [("お", ""), ("頭", "かしら")],
    "御心": [("御", "み"), ("心", "こころ")], "御霊": [("御", "み"), ("霊", "たま")],
    "暗黒神": [("暗黒", "あんこく"), ("神", "しん")], "ロプト神": [("ロプト", ""), ("神", "しん")],
    "かけ金": [("かけ", ""), ("金", "きん")],
}

# dictionary form -> gloss, where the automatic choice is wrong or missing
GLOSS_FIXES = {
}

# Proper nouns that are not in en.NAMES (those are added automatically).
PROPER = {
    "トラキア": "Thracia", "レンスター": "Leonster", "マンスター": "Munster", "アルスター": "Ulster",
    "コノート": "Connacht", "ターラ": "Tahra", "フィアナ": "Fiana", "グランベル": "Grannvale",
    "フリージ": "Friege", "ユグドラル": "Jugdral", "イザーク": "Isaach", "シレジア": "Silesse",
    "バーハラ": "Belhalla", "ミーズ": "Meath", "ロプト": "Loptous", "ケルベス": "Kelves",
    "ダキア": "Dakia", "ノルデン": "Norden", "ダンドラム": "Dandrum", "メルフィーユ": "Melfiye",
    "イード": "Yied", "ブラギ": "Bragi", "ダイン": "Dain", "ノヴァ": "Nova (Njorun)", "キア": "Kia",
    "ランスリッター": "Lanzenritter", "マギ": "Magi", "イス": "Ith", "ノエル": "Noel",
    "ドリアス": "Dorias", "トラバント": "Travant", "マンフロイ": "Manfroy", "レヴィン": "Lewyn",
    "ブルーム": "Bloom", "ドボルザーク": "Dvorak", "シグルド": "Sigurd", "ラケシス": "Lachesis",
    "ベオウルフ": "Beowolf", "ブリギッド": "Brigid", "アルヴィス": "Arvis", "ヘイム": "Heim",
    "バルド": "Baldr", "ゲイボルグ": "Gae Bolg", "グングニル": "Gungnir", "フォルセティ": "Forseti",
}

# Grammar words get a short hand-written note instead of a long dictionary entry.
PARTICLES = {
    "は": "topic marker", "が": "subject marker; but", "を": "object marker",
    "に": "to, at, in, by (target / time / place)", "で": "at, in; by means of, with",
    "と": "and, with; quotation marker; if/when", "も": "also, too; even", "の": "of, 's; (nominaliser / explanatory)",
    "へ": "to, toward", "から": "from; because", "まで": "until, up to, as far as", "より": "than; from",
    "や": "and (among other things)", "か": "question marker; or", "ね": "right?, isn't it (seeking agreement)",
    "よ": "emphasis (telling the listener)", "な": "emphasis; don't (prohibition)", "ぞ": "strong emphasis",
    "ぜ": "emphasis (rough, masculine)", "わ": "soft emphasis", "さ": "casual assertion",
    "て": "te-form connector (and, then; request)", "で": "at, in; by means of, with", "ば": "if",
    "けれど": "but, although", "けど": "but, although", "けれども": "but, although", "のに": "although, even though",
    "ので": "because, since", "し": "and (giving reasons)", "たり": "doing things like",
    "ながら": "while (doing)", "だけ": "only, just", "しか": "only (with negative)", "ほど": "to the extent of, about",
    "くらい": "about, to the extent of", "ぐらい": "about, to the extent of", "など": "and so on, such as",
    "こそ": "emphasis (it is precisely...)", "さえ": "even", "でも": "but; even", "って": "casual quotation / topic marker",
    "なら": "if, in the case of", "とも": "even if; both", "ばかり": "only, just; about", "ずつ": "each, at a time",
    "かしら": "I wonder", "だって": "even; because", "なんて": "things like (surprise / disdain)", "じゃ": "then, well (= では)",
    "つつ": "while", "すら": "even", "のみ": "only", "やら": "and; I wonder", "とか": "and, or (among other things)",
}
AUXILIARIES = {
    "た": "past tense / completed", "だ": "is, am, are (copula)", "です": "is, am, are (polite)",
    "ます": "polite verb ending", "ない": "not", "ぬ": "not (older negative)", "ん": "not (contracted negative)",
    "れる": "passive / can / honorific", "られる": "passive / can / honorific", "せる": "make/let (causative)",
    "させる": "make/let (causative)", "たい": "want to", "う": "let's; will (volitional)", "よう": "let's; will (volitional)",
    "らしい": "seems, apparently", "べし": "should, must", "まい": "will not; probably not",
    "ちゃう": "end up doing (= てしまう)", "てる": "is doing (= ている)", "じゃ": "is (= では)", "や": "is (dialect copula)",
    "たり": "doing things like", "ず": "without, not", "ござる": "to be (formal)", "なり": "is (classical copula)",
    "たる": "being (classical)", "そう": "looks like; I hear", "みたい": "like, seems", "やる": "do (for someone)",
}

POS_HINT = {"動詞": "verb", "形容詞": "adjective", "名詞": "noun", "副詞": "adverb", "代名詞": "pronoun",
            "接続詞": "conjunction", "感動詞": "interjection", "連体詞": "pre-noun", "形状詞": "adjectival",
            "接尾辞": "suffix", "接頭辞": "prefix", "助詞": "particle"}
SKIP_POS = {"補助記号", "記号", "空白"}
MERGE_POS = {"名詞", "接頭辞", "接尾辞", "代名詞"}


def hira(s):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def split_okurigana(surface, reading):
    """「取り戻せ」+「とりもどせ」 -> [(取,と),(り,""),(戻,もど),(せ,"")]"""
    parts = re.findall(f"{KANJI}+|[^\u3400-\u9fff\uf900-\ufaff々〆ヶ]+", surface)
    if len(parts) == 1:
        return [[surface, reading]]
    pattern = "".join("(.+?)" if HAS_KANJI.match(p) else re.escape(hira(p)) for p in parts)
    m = re.fullmatch(pattern, reading)
    if not m:
        return [[surface, reading]]
    groups = iter(m.groups())
    return [[p, next(groups)] if HAS_KANJI.match(p) else [p, ""] for p in parts]


# ------------------------------------------------------------------ JMdict --

class Dictionary:
    def __init__(self):
        if not JMDICT.exists():
            JMDICT.parent.mkdir(exist_ok=True)
            print("downloading JMdict ...")
            urllib.request.urlretrieve(JMDICT_URL, JMDICT)
        self.by_kanji, self.by_kana = {}, {}
        for _, el in ET.iterparse(gzip.open(JMDICT), events=("end",)):
            if el.tag != "entry":
                continue
            kebs = [k.text for k in el.iter("keb")]
            rebs = [r.text for r in el.iter("reb")]
            common = any(True for _ in el.iter("ke_pri")) or any(True for _ in el.iter("re_pri"))
            senses, pos = [], []
            for s in el.iter("sense"):
                pos = [p.text for p in s.findall("pos")] or pos     # pos carries over between senses
                senses.append((" ".join(pos).lower(), [m.text for m in s.findall("misc")],
                               [g.text for g in s.findall("gloss")]))
            entry = (kebs, rebs, common, senses)
            for k in kebs:
                self.by_kanji.setdefault(k, []).append(entry)
            for r in rebs:
                self.by_kana.setdefault(r, []).append(entry)
            el.clear()

    def lookup(self, form, lemma, reading, pos1):
        """Best entry for a word -> (dictionary form, reading, gloss) or None."""
        hint = POS_HINT.get(pos1, "")
        for word in dict.fromkeys((form, lemma)):
            if not word:
                continue
            kanji = bool(HAS_KANJI.search(word))
            cands = (self.by_kanji if kanji else self.by_kana).get(word) or \
                    (self.by_kana.get(hira(word)) if not kanji else None)
            if not cands:
                continue
            def score(e):
                kebs, rebs, common, senses = e
                s = 3 if common else 0
                if kanji:
                    s += 4 if reading in rebs else 0
                else:
                    s += 5 if lemma in kebs else 0
                    s += 3 if any("usually written using kana" in m for m in senses[0][1]) else 0
                    s += 2 if not kebs else 0
                s += 3 if hint and any(hint in p for p, _, _ in senses) else 0
                return s
            best = max(cands, key=score)
            kebs, rebs, _, senses = best
            ordered = sorted(senses, key=lambda x: hint not in x[0]) if hint else senses
            gloss = " / ".join("; ".join(g[:3]) for _, _, g in ordered[:2] if g)
            rd = reading if reading in rebs else rebs[0]
            return word, rd, gloss
        return None

    def has_kanji_word(self, word):
        return word in self.by_kanji


# ---------------------------------------------------------------- analysis --

class Analyzer:
    def __init__(self):
        self.tagger = fugashi.Tagger()
        self.dic = Dictionary()
        self.proper = {jp: name for jp, name in en.NAMES.items()}
        self.proper.update(PROPER)
        fixed = sorted(list(self.proper) + list(COMPOUNDS), key=len, reverse=True)
        self.fixed_re = re.compile("(" + "|".join(map(re.escape, fixed)) + ")")
        self.glossary, self.gloss_ids = [], {}

    def gid(self, form, reading, gloss):
        gloss = GLOSS_FIXES.get(form, gloss)
        key = (form, reading, gloss)
        if key not in self.gloss_ids:
            self.gloss_ids[key] = len(self.glossary)
            self.glossary.append(list(key))
        return self.gloss_ids[key]

    def line(self, text):
        """-> list of [surface, ruby segments or None, glossary id or None]"""
        # Known names/phrases are cut out as single words, but the tokenizer still sees the
        # whole line, so neighbours keep their context (レンスター城 -> じょう, not しろ).
        spans = [(m.start(), m.end()) for m in self.fixed_re.finditer(text)]
        toks = self.tokens(text)
        pos, placed = 0, []
        for t in toks:
            placed.append((pos, pos + len(t["s"]), t))
            pos += len(t["s"])
        if pos != len(text) or any(a < e and s < b and not (s <= a and b <= e)
                                   for a, b, _ in placed for s, e in spans):
            return self.line_by_chunks(text)      # a token straddles a name: fall back
        out, group, i = [], [], 0
        for a, b, t in placed:
            span = next(((s, e) for s, e in spans if s <= a and b <= e), None)
            if span:
                if a == span[0]:
                    out.extend(self.merge(group))
                    group = []
                    out.append(self.fixed(text[span[0]:span[1]]))
                continue
            group.append(t)
        out.extend(self.merge(group))
        return out

    def line_by_chunks(self, text):
        out = []
        for chunk in self.fixed_re.split(text):
            if not chunk:
                continue
            if chunk in self.proper or chunk in COMPOUNDS:
                out.append(self.fixed(chunk))
            else:
                out.extend(self.merge(self.tokens(chunk)))
        return out

    def fixed(self, chunk):
        if chunk in self.proper:
            return [chunk, None, self.gid(chunk, "", self.proper[chunk] + " (name)")]
        reading = "".join(r or s for s, r in COMPOUNDS[chunk])
        hit = self.dic.lookup(chunk, chunk, reading, "名詞")
        segs = [[s, r] for s, r in COMPOUNDS[chunk]]
        return [chunk, segs, self.gid(chunk, reading, hit[2]) if hit else None]

    def tokens(self, text):
        toks = []
        for w in self.tagger(text):
            if w.white_space:
                toks.append({"s": w.white_space, "skip": True})
            f = w.feature
            toks.append({"s": w.surface, "pos": f.pos1, "lemma": (f.lemma or "").split("-")[0],
                         "form": f.orthBase or w.surface, "kana": hira(f.kana or ""),
                         "kbase": hira(f.kanaBase or ""), "skip": f.pos1 in SKIP_POS})
        return toks

    def merge(self, toks):
        """Tokens -> words, joining neighbours that form one dictionary word."""
        out, i = [], 0
        while i < len(toks):
            t = toks[i]
            if t["skip"] or re.fullmatch(r"[０-９0-9A-Za-zＡ-Ｚａ-ｚ'.,:&/-]+", t["s"]):
                out.append([t["s"], None, None])
                i += 1
                continue
            # join neighbouring nouns/affixes that form one dictionary word (支配+権 -> 支配権)
            merged = None
            for n in (3, 2):
                group = toks[i:i + n]
                if len(group) == n and all(not g["skip"] and g.get("pos") in MERGE_POS for g in group):
                    word = "".join(g["s"] for g in group)
                    if HAS_KANJI.search(word) and self.dic.has_kanji_word(word):
                        merged = (word, group)
                        break
            if merged:
                word, group = merged
                reading = "".join(OVERRIDES.get(g["s"]) or g["kana"] for g in group)
                form, rd, gloss = self.dic.lookup(word, word, reading, "名詞")
                if rd == reading:
                    segs = [seg for g in group for seg in self.ruby(g["s"], OVERRIDES.get(g["s"]) or g["kana"])]
                else:
                    segs = self.ruby(word, rd)
                out.append([word, segs, self.gid(form, rd, gloss)])
                i += len(group)
                continue
            out.append(self.word(t))
            i += 1
        return out

    def ruby(self, surface, reading):
        if not HAS_KANJI.search(surface) or not reading or reading == "*":
            return [[surface, ""]]
        return split_okurigana(surface, reading)

    def word(self, t):
        s, pos = t["s"], t["pos"]
        reading = OVERRIDES.get(s) or t["kana"]
        segs = self.ruby(s, reading) if HAS_KANJI.search(s) else None
        if segs and not any(r for _, r in segs):
            segs = None
        if pos == "助詞" and (t["form"] in PARTICLES or s in PARTICLES):
            return [s, segs, self.gid(s, "", PARTICLES.get(t["form"]) or PARTICLES[s])]
        if pos == "助動詞" and t["lemma"] in AUXILIARIES:
            return [s, segs, self.gid(t["lemma"], "", AUXILIARIES[t["lemma"]])]
        base_reading = OVERRIDES.get(t["form"]) or t["kbase"]
        hit = self.dic.lookup(t["form"], t["lemma"], base_reading, pos)
        if hit:
            form, rd, gloss = hit
            return [s, segs, self.gid(form, rd if rd != form else "", gloss)]
        return [s, segs, self.gid(t["form"], "", "")]       # no dictionary entry


def main():
    script = json.loads((ROOT / "data" / "script.json").read_text(encoding="utf-8"))
    an = Analyzer()
    result, bad = {}, 0
    for page in script.values():
        for scene in page["scenes"]:
            for item in scene["items"]:
                if item["t"] != "box":
                    continue
                for line in item["lines"]:
                    for kind, text in line:
                        if kind != "text" or text in result:
                            continue
                        toks = an.line(text)
                        if "".join(t[0] for t in toks) != text:      # never alter the script
                            bad += 1
                            continue
                        result[text] = toks
    (ROOT / "data" / "tokens.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    (ROOT / "data" / "glossary.json").write_text(json.dumps(an.glossary, ensure_ascii=False), encoding="utf-8")
    old = ROOT / "data" / "furigana.json"
    if old.exists():
        old.unlink()
    nogloss = sum(1 for g in an.glossary if not g[2])
    print(f"{len(result)} lines, {bad} skipped; {len(an.glossary)} glossary entries, {nogloss} without a gloss")


if __name__ == "__main__":
    main()
