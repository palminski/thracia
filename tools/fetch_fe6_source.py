#!/usr/bin/env python3
"""One-time fetch of the FE6 Master Bible script pages into source/fe6/.

Pulls the main-story pages (not the 54 support conversations, not the
class/unit stat tables) from pegasusknight.com, verbatim, UTF-8 this time
(their site has moved off the old Shift_JIS static-HTML format Thracia's
source/ was saved from). Run once; re-run only if a page needs refreshing.

    python3 tools/fetch_fe6_source.py
"""
import time
import urllib.request
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent / "source" / "fe6"
BASE = "https://www.pegasusknight.com/mb/fe6/"
UA = {"User-Agent": "thracia-fansite-build/0.1 (personal fan project)"}

SLUGS = (
    ["st_opening", "st_demo"]
    + ["st_map1", "st_map2", "st_map3", "st_map4", "st_map5", "st_map6", "st_map7",
       "st_map8", "st_map8x", "st_map9", "st_map10a", "st_map10b", "st_map11a",
       "st_map11b", "st_map12", "st_map12x", "st_map13", "st_map14", "st_map14x",
       "st_map15", "st_map16", "st_map16x", "st_map17a", "st_map17b", "st_map18a",
       "st_map18b", "st_map19a", "st_map19b", "st_map20a", "st_map20b", "st_map20xa",
       "st_map20xb", "st_map21", "st_map21x", "st_map22", "st_map23", "st_map24",
       "st_map25"]
    + ["st_death", "st_ending1", "st_ending2"]
)


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for slug in SLUGS:
        out = DEST / f"{slug}.html"
        if out.exists():
            print("skip (exists)", slug)
            continue
        req = urllib.request.Request(BASE + slug, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        out.write_bytes(data)
        print("fetched", slug, len(data), "bytes")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
