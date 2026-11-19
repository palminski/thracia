#!/usr/bin/env python3
"""Download FE4 portraits (PNG) into public/fe4/img/portraits/.

Source: Fire Emblem Wiki (https://fireemblemwiki.org), files named
"Portrait_<name>_fe04.png". Each is saved under the Japanese speaker name
build_fe4.py looks for. Run tools/build_fe4.py afterwards.

    python3 tools/fetch_fe4_portraits.py
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent / "public" / "fe4" / "img" / "portraits"
API = "https://fireemblemwiki.org/w/api.php"
UA = {"User-Agent": "thracia-fansite-build/0.1 (personal fan project)"}

# Japanese speaker name (as it appears in the transcript) -> wiki file-name slug.
# Grows chapter by chapter as new named characters show up.
NAMES = {
    "シグルド": "sigurd", "エーディン": "edain", "キュアン": "quan", "アイラ": "ayra",
    "アゼル": "azelle", "ディアドラ": "deirdre", "フィン": "finn_01", "ラケシス": "lachesis",
    "レックス": "lex", "エルトシャン": "eldigan", "アルヴィス": "arvis_01",
    "エスリン": "ethlyn", "ミデェール": "midir", "ガンドルフ": "munnir",
    "アレク": "alec", "アーダン": "arden", "ノイッシュ": "naoise",
    "オイフェ（少年）": "oifey_02", "キンボイス": "cimbaeth", "ゲラルド": "gerrard",
    "デマジオ": "dimaggio",
    "アイラ": "ayra", "エスリン": "ethlyn", "エルトシャン": "eldigan",
    "シャナン（少年）": "shannan_01", "デュー": "dew", "バトゥ": "batu",
    "ボルドー": "bordeaux", "エリオット": "elliot", "フィリップ": "philip",
    "マクベス": "macbeth", "クレメント": "clement", "ベオウルフ": "beowolf",
    "シルヴィア": "silvia", "ザイン": "zane", "フィラート": "filat",
    "レヴィン": "lewyn_01", "マンフロイ": "manfroy", "イーヴ": "eve",
    "クロード": "claud", "ティルテュ": "tailtiu", "トラバント": "travant_01",
    "パピヨン": "papilio", "ランゴバルト": "lombard", "ブリギッド": "brigid",
    "レプトール": "reptor", "アンドレイ": "andrey", "ドノバン": "donovan",
    "パメラ": "pamela", "ラーナ": "lahna", "マーニャ": "annand",
    "アイーダ": "aida", "アズムール": "azmur", "バイロン": "byron",
    "ヴァハ": "vaja", "ジャムカ": "jamke",
    "ダナン": "danann", "スカサハ": "scáthach", "ラクチェ": "larcei",
    "ロドルバン": "dalvin", "ラドネイ": "creidne", "オイフェ": "oifey_01",
    "レスター": "lester", "デルムッド": "diarmuid", "ヨハン": "iuchar",
    "ヨハルヴァ": "iucharba", "レヴィン（軍師）": "lewyn_02", "ユリア": "julia",
    "ラナ": "nanna", "ディムナ": "deimne", "マナ": "muirne", "フィー": "fee",
    "アーサー": "arthur", "フェミナ": "hermina", "スレイダー": "slayder schmidt",
    "ハロルド": "harold",
    "セリス": "seliph", "シャナン": "shannan 02", "リーフ": "leif", "ナンナ": "nanna",
    "ブルーム": "bloom", "パティ": "patty", "クトゥーゾフ": "kutuzov dagon",
    "イシュトー": "ishtore", "ライザ": "liza", "ブラムセル": "bramsel",
    "ジャバロー": "javarro", "リーン": "lene", "アレス": "ares",
    "トリスタン": "tristan", "ジャンヌ": "jeanne", "ティニー": "tine",
    "ファバル": "febail", "コルータ": "coulter", "セティ": "ced", "ホーク": "hawk",
    "アリオーン": "arion", "アルテナ": "altena", "アミッド": "amid", "リンダ": "linda",
    "オーヴォ": "ovo", "オーヴァ": "ovo",
    "ハンニバル": "hannibal", "コープル": "coirpre", "ジュダ": "judah",
    "カナッツ": "kanatz", "アサエロ": "asaello", "シャルロー": "charlot",
    "ムーサー": "musar", "レイリア": "laylea",
    "ユリウス": "julius", "イシュタル": "ishtar", "ヒルダ": "hilda", "ザガム": "zagam",
    "パルマーク（灰）": "palmarch", "シグルド（幽霊）": "sigurd", "ディアドラ（幽霊）": "deirdre",
}


def api(**params):
    url = API + "?" + urllib.parse.urlencode({"format": "json", **params})
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA)))


def main():
    files = {f"File:Portrait {w} fe04.png": jp for jp, w in NAMES.items()}
    by_file = {}
    for jp, w in NAMES.items():
        by_file.setdefault(f"File:Portrait {w} fe04.png", []).append(jp)

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
