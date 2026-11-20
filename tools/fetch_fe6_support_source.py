#!/usr/bin/env python3
"""One-time fetch of FE6's 54 support-conversation pages from pegasusknight.com
into source/fe6/support/. Each page (st_support1..54) belongs to one playable
character and lists that character's support conversations (C/B/A ranks) with
every partner they support. Run once; re-run only if a page needs refreshing.

    python3 tools/fetch_fe6_support_source.py
"""
import time
import urllib.request
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent / "source" / "fe6" / "support"
BASE = "https://www.pegasusknight.com/mb/fe6/"
UA = {"User-Agent": "thracia-fansite-build/0.1 (personal fan project)"}


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for n in range(1, 55):
        slug = f"st_support{n}"
        out = DEST / f"{slug}.html"
        if out.exists():
            print("skip (exists)", slug)
            continue
        req = urllib.request.Request(BASE + slug + "/", headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        out.write_bytes(data)
        print("fetched", slug, len(data), "bytes")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
