#!/usr/bin/env python3
"""Download FE6 portraits (PNG) into public/fe6/img/portraits/.

Source: Fire Emblem Wiki (https://fireemblemwiki.org), files named
"Portrait_<name>_fe06.png". Each is saved under the Japanese speaker name
build_fe6.py looks for. Run tools/build_fe6.py afterwards.

    python3 tools/fetch_fe6_portraits.py
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent / "public" / "fe6" / "img" / "portraits"
API = "https://fireemblemwiki.org/w/api.php"
UA = {"User-Agent": "thracia-fansite-build/0.1 (personal fan project)"}

# Japanese speaker name (as it appears in the transcript) -> wiki file-name slug.
# Grows chapter by chapter as new named characters show up.
NAMES = {
    "ヘニング": "henning", "スコット": "scott", "セシリア": "cecilia", "ギネヴィア": "guinivere",
    "フィル": "fir", "シン": "sin", "ノア": "noah", "スー": "sue",
    "ロイ": "roy", "リリーナ": "lilina", "エリウッド": "eliwood", "ランス": "lance",
    "アレン": "alen", "ボールス": "bors", "マーカス": "marcus", "ウォルト": "wolt",
    "ダマス": "damas", "レイガンス": "legance", "ゼロット": "zelot", "トレック": "trec",
    "ミレディ": "melady", "ルード": "ruud", "エレン": "elen", "ディーク": "dieck",
    "シャニー": "shanna", "ワード": "ward", "ロット": "lot", "ブルーニャ": "brunnya",
    "ゼフィール": "zephiel", "ヘクトル": "hector", "ドリー": "dory", "ヨーデル": "yodel",
    "ドロシー": "dorothy", "サウル": "saul", "チャド": "chad", "ルゥ": "lugh",
    "ナーシェン": "narcian", "スレーター": "slater", "エリック": "erik", "クラリーネ": "clarine",
    "ルトガー": "rutger", "キャス": "cath", "ワグナー": "wagner", "アストール": "astolfo",
    "バース": "barthe", "ウェンディ": "gwendolyn", "パーシバル": "perceval",
    "ノード": "nord", "ギース": "geese", "ゴンザレス": "gonzalez", "ララム": "larum",
    "エルフィン": "elffin", "ゲイル": "galle",
    "オロ": "orlo", "クレイン": "klein", "エキドナ": "echidna", "スコーラン": "scollan",
    "ティト": "thea",
    "バアトル": "bartre", "アルカルド": "arcardo",
    "フレアー": "flaer", "アイン": "ein", "レイ": "raigh",
    "ゲレロ": "guerrero", "ソフィーヤ": "sophia",
    "ファ": "fae", "イグレーヌ": "igrene", "ランディ": "randy", "ツァイス": "zeiss",
    "ローズ": "rose", "マギー": "maggie",
    "オーツ": "oates",
    "ダグラス": "douglas", "ガレット": "garret", "レイス": "raith",
}


def api(**params):
    url = API + "?" + urllib.parse.urlencode({"format": "json", **params})
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA)))


def main():
    files = {f"File:Portrait {w} fe06.png": jp for jp, w in NAMES.items()}
    by_file = {}
    for jp, w in NAMES.items():
        by_file.setdefault(f"File:Portrait {w} fe06.png", []).append(jp)

    urls, titles = {}, list(by_file)
    for i in range(0, len(titles), 40):
        d = api(action="query", titles="|".join(titles[i:i + 40]), prop="imageinfo", iiprop="url")
        norm = {n["to"]: n["from"] for n in d["query"].get("normalized", [])}
        for page in d["query"]["pages"].values():
            if "imageinfo" in page:
                urls[norm.get(page["title"], page["title"])] = page["imageinfo"][0]["url"]
        time.sleep(0.3)

    DEST.mkdir(parents=True, exist_ok=True)
    got, missing = 0, []
    for title, jps in by_file.items():
        if title not in urls:
            missing += jps
            continue
        data = urllib.request.urlopen(urllib.request.Request(urls[title], headers=UA)).read()
        for jp in jps:
            (DEST / f"{jp}.png").write_bytes(data)
            got += 1
        time.sleep(0.2)
    print(f"saved {got} portraits")
    if missing:
        print("not on the wiki:", " ".join(sorted(missing)))


if __name__ == "__main__":
    main()
