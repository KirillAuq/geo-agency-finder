#!/usr/bin/env python3
"""One-off: merge research JSON (caseStudies/strengths/weaknesses/scores) into agencies.json by name.

Integrity checks:
  - a case study whose URL is off the agency's own domain is dropped with a warning
  - every score is clamped to 1..5; missing criteria become 1 / "No public evidence"
"""
import json
import pathlib
import sys
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).parent
SCORE_KEYS = [
    "aiContent", "thoughtLeadership", "linkbuilding", "mentionBuilding",
    "customOutreach", "technicalGeo", "promptAnalytics", "conversionTracking",
    "contentDesign", "development",
]


def host(url):
    """Registrable domain, approximated as the last two labels (elogia.net for blog.elogia.net)."""
    h = urlparse(url).netloc.lower()
    if h.startswith("www."):
        h = h[4:]
    parts = h.split(".")
    return ".".join(parts[-2:]) if len(parts) > 2 else h


agencies = json.loads((ROOT / "agencies.json").read_text())
by_name = {a["name"]: a for a in agencies}

merged, missing, dropped = 0, [], []
for path in sys.argv[1:]:
    for e in json.loads(pathlib.Path(path).read_text()):
        a = by_name.get(e["name"])
        if not a:
            missing.append(e["name"])
            continue
        own = host(a["website"])
        cs = []
        for c in (e.get("caseStudies") or [])[:3]:
            if not (c.get("title") and c.get("url") and c.get("summary")):
                dropped.append(f"{e['name']}: incomplete case study")
                continue
            ch = host(c["url"])
            if ch != own and not ch.endswith("." + own) and not own.endswith("." + ch):
                dropped.append(f"{e['name']}: off-domain case study {c['url']}")
                continue
            cs.append({"title": c["title"], "url": c["url"], "summary": c["summary"]})
        a["caseStudies"] = cs
        a["strengths"] = [s for s in (e.get("strengths") or []) if s][:4]
        a["weaknesses"] = [s for s in (e.get("weaknesses") or []) if s][:4]
        scores = {}
        for k in SCORE_KEYS:
            sc = (e.get("scores") or {}).get(k) or {}
            try:
                n = max(1, min(5, int(sc.get("score") or 1)))
            except (TypeError, ValueError):
                n = 1
            scores[k] = {"score": n, "evidence": (sc.get("evidence") or "No public evidence").strip()}
        a["scores"] = scores
        merged += 1

(ROOT / "agencies.json").write_text(json.dumps(agencies, indent=2, ensure_ascii=False) + "\n")
graded = sum(1 for a in agencies if a.get("scores"))
with_cs = sum(1 for a in agencies if a.get("caseStudies"))
print(f"merged {merged}; graded {graded}/{len(agencies)}; with case studies {with_cs}")
if missing:
    print("unmatched names:", missing)
for d in dropped:
    print("dropped:", d)
