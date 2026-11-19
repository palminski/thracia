#!/usr/bin/env python3
"""One-time fetch of the FE4 (Genealogy of the Holy War) Master Bible script
pages into source/fe4/.

Pulls the main-story pages from pegasusknight.com, verbatim UTF-8, same
spirit as tools/fetch_fe6_source.py. Run once; re-run only if a page needs
refreshing.

    python3 tools/fetch_fe4_source.py
"""
import time
import urllib.request
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent / "source" / "fe4"
BASE = "https://www.pegasusknight.com/mb/fe4/"
UA = {"User-Agent": "thracia-fansite-build/0.1 (personal fan project)"}

SLUGS = ["st_map0", "st_map1", "st_map2", "st_map3", "st_map4", "st_map5",
         "st_map6", "st_map7", "st_map8", "st_map9", "st_map10", "st_map11",
         "st_ending"]


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for slug in SLUGS:
        out = DEST / f"{slug}.html"
        if out.exists():
            print("skip (exists)", slug)
            continue
        # pegasusknight redirects the no-slash form to a trailing-slash URL
        req = urllib.request.Request(BASE + slug + "/", headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        out.write_bytes(data)
        print("fetched", slug, len(data), "bytes")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
