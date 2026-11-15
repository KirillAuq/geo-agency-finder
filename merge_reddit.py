#!/usr/bin/env python3
"""One-off: merge Reddit sweep JSON (name + threads) into agencies.json.

Every agency gets a `reddit` object with the check date; threads only where found.
Thread URLs must be reddit.com links; anything else is dropped with a warning.
"""
import json
import pathlib
import sys
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).parent
CHECKED = "November 2026"
STANCES = {"positive", "negative", "mixed", "mention-only"}
AUTH = {"organic", "likely-self-promo", "unclear"}

agencies = json.loads((ROOT / "agencies.json").read_text())
by_name = {a["name"]: a for a in agencies}
for a in agencies:
    a["reddit"] = {"checked": CHECKED, "threads": []}

missing, dropped, added = [], [], 0
for path in sys.argv[1:]:
    for e in json.loads(pathlib.Path(path).read_text()):
        a = by_name.get(e["name"])
        if not a:
            missing.append(e["name"])
            continue
        for t in e.get("threads") or []:
            host = urlparse(t.get("url", "")).netloc.lower()
            if not host.endswith("reddit.com"):
                dropped.append(f"{e['name']}: non-reddit URL {t.get('url')}")
                continue
            if not (t.get("gist") and t.get("subreddit")):
                dropped.append(f"{e['name']}: incomplete thread entry")
                continue
            a["reddit"]["threads"].append({
                "url": t["url"],
                "subreddit": t["subreddit"],
                "year": t.get("year") or "unknown",
                "gist": t["gist"],
                "stance": t.get("stance") if t.get("stance") in STANCES else "mention-only",
                "authenticity": t.get("authenticity") if t.get("authenticity") in AUTH else "unclear",
            })
            added += 1

(ROOT / "agencies.json").write_text(json.dumps(agencies, indent=2, ensure_ascii=False) + "\n")
with_threads = sum(1 for a in agencies if a["reddit"]["threads"])
print(f"added {added} threads across {with_threads}/{len(agencies)} agencies")
if missing:
    print("unmatched names:", missing)
for d in dropped:
    print("dropped:", d)
