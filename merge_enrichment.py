#!/usr/bin/env python3
"""One-off: merge enrichment JSON (contact/socials/reviews) into agencies.json by name."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
# Personal founder accounts published in site footers; not listed as agency socials.
DROP_URLS = {
    "https://x.com/vc_jacob",
    "https://www.youtube.com/@niklas.buschner",
    "https://www.youtube.com/@ldunne",
}
FIELDS = ["contactUrl", "email", "phone", "linkedin", "youtube", "x", "reviews"]

agencies = json.loads((ROOT / "agencies.json").read_text())
by_name = {a["name"]: a for a in agencies}

merged, missing = 0, []
for path in sys.argv[1:]:
    for e in json.loads(pathlib.Path(path).read_text()):
        a = by_name.get(e["name"])
        if not a:
            missing.append(e["name"])
            continue
        for f in FIELDS:
            v = e.get(f)
            if isinstance(v, str) and v in DROP_URLS:
                v = ""
            if v:
                a[f] = v
        merged += 1

(ROOT / "agencies.json").write_text(json.dumps(agencies, indent=2, ensure_ascii=False) + "\n")
enriched = sum(1 for a in agencies if a.get("contactUrl") or a.get("linkedin"))
print(f"merged {merged} records; {len(agencies)} agencies; {enriched} with contact/linkedin; unmatched: {missing or 'none'}")
