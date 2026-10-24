#!/usr/bin/env python3
"""Download Thracia 776 portraits (48x64 PNG) into img/portraits/.

Source: Fire Emblem Wiki (https://fireemblemwiki.org), files named
"Portrait_<name>_fe05.png". Each is saved under the Japanese speaker name the
site looks for. Run tools/build.py afterwards.

    python3 tools/fetch_portraits.py
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import en  # noqa: E402

DEST = Path(__file__).resolve().parent.parent / "public" / "img" / "portraits"
API = "https://fireemblemwiki.org/w/api.php"
UA = {"User-Agent": "thracia-fansite-build/0.1 (personal fan project)"}

# Speakers whose wiki file name isn't just the lower-cased name in en.NAMES.
OVERRIDES = {
    "ミュラー": "mueller", "グスタフ": "gustaf", "ラインコック": "linecock", "マーロック": "merlock",
    "コッダ": "codda", "ザイル": "zyle", "ワイズマン": "weismann", "バラート": "baráth", "ディーン": "deen",
    "コルホ": "cullough",
    # speakers that never appear in a heading, so they aren't in en.NAMES
    "ドリアス": "dryas", "ドボルザーク": "dvorak", "トラバント": "travant", "マンフロイ": "manfroy",
    "レヴィン": "lewyn", "ブルーム": "bloom",
    # recoloured generics: the base portrait stands in for the palette swap
    "赤ウォルフ": "wolf", "橙ウォルフ": "wolf", "緑マクロイ": "mccloy", "紫パウルス": "paulus",
    "青ルーメイ": "rumei",
    # Unnamed townspeople. The transcript only says "citizen (man)" etc., and the game has
    # several villager faces, so these are a best match by description, not exact per scene.
    "市民(男)": "villager_09", "市民(女)": "villager_02", "市民(おばさん)": "villager_07",
    "市民(おじいさん)": "villager_01", "村長(おじいさん)": "villager_15", "市民(女の子)": "villager_11",
    "市民(男の子)": "villager_10", "市民(おばあさん)": "villager_06", "市民(おじさん)": "villager_08",
    "店の親父": "vendor", "闘技場の兄貴": "fightmonger",
}


def api(**params):
    url = API + "?" + urllib.parse.urlencode({"format": "json", **params})
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA)))


def main():
    wanted = {jp: name.lower() for jp, name in en.NAMES.items()}
    wanted.update(OVERRIDES)
    files = {f"File:Portrait {w} fe05.png": jp for jp, w in wanted.items()}
    by_file = {}
    for jp, w in wanted.items():
        by_file.setdefault(f"File:Portrait {w} fe05.png", []).append(jp)

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
