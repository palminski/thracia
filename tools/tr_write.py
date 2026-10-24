#!/usr/bin/env python3
"""Helper: read "N|English" lines on stdin and save them as translations/<slug>.txt."""
import sys
from pathlib import Path
slug = sys.argv[1]
rows = [l.rstrip("\n") for l in sys.stdin if "|" in l and l.split("|", 1)[0].strip().isdigit()]
nums = [int(r.split("|", 1)[0]) for r in rows]
assert nums == list(range(1, len(nums) + 1)), f"numbering gap near {next((i+1 for i,n in enumerate(nums) if n != i+1), '?')}"
out = Path(__file__).resolve().parent.parent / "translations" / f"{slug}.txt"
out.write_text("\n".join(r.replace("|", "\t", 1) for r in rows) + "\n", encoding="utf-8")
print(slug, len(rows))
