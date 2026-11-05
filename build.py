#!/usr/bin/env python3
"""Build the GEO Agency Finder static site from agencies.json.

Generates:
  data.js                      - dataset consumed by the directory page
  agencies/<slug>/index.html   - one profile page per agency
  sitemap.xml                  - directory + profiles
Run:  python3 build.py
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
BASE_URL = "https://auq.io/agency-finder/"
LAST_CHECKED = "November 2026"

SERVICE_BLURBS = {
    "AI visibility tracking": "Measuring how often the brand appears in answers from ChatGPT, Perplexity, Gemini and Google AI Overviews, and tracking share of voice over time.",
    "Content for LLM citation": "Publishing and restructuring content so AI assistants can quote it: direct answers, clear structure, extractable facts.",
    "Technical GEO": "Making the site readable to AI systems: structured data, llms.txt, rendering and indexation fixes for AI crawlers.",
    "Digital PR & mentions": "Earning brand mentions and links on the third-party pages AI assistants already cite.",
    "Listicle placements": "Getting the brand into the ranking best-of lists that assistants reach for on comparison questions.",
    "Classic SEO": "Traditional search engine optimization: rankings and traffic, with the content, technical and authority work underneath them.",
    "CRO": "Conversion rate optimization: turning the visits that still land on the site into pipeline.",
}

SOCIAL_LABELS = [("linkedin", "LinkedIn"), ("youtube", "YouTube"), ("x", "X (Twitter)")]

# Capability scorecard: (group label, [(key, display name)]).
SCORE_GROUPS = [
    ("Content", [
        ("aiContent", "AI content"),
        ("thoughtLeadership", "Thought leadership with expert authors"),
    ]),
    ("Off site", [
        ("linkbuilding", "Link building"),
        ("mentionBuilding", "Mention building"),
        ("customOutreach", "Custom outreach"),
    ]),
    ("Technical", [
        ("technicalGeo", "Technical SEO / GEO"),
    ]),
    ("Analytics", [
        ("promptAnalytics", "Prompt analytics"),
        ("conversionTracking", "Conversion tracking"),
    ]),
    ("Dev & design", [
        ("contentDesign", "Content design"),
        ("development", "Development for LLM-ready site sections"),
    ]),
]

CSS = """
  :root {
    --c-text: #000000; --c-text-dark: #ffffff; --c-bg: #ffffff; --c-dark: #010120;
    --c-magenta: #ef2cc1; --c-orange: #fc4c02; --c-lavender: #bdbbff;
    --c-border-light: rgba(0, 0, 0, 0.08);
    --c-fill-light: rgba(0, 0, 0, 0.04);
    --c-muted-light: rgba(0, 0, 0, 0.55);
    --shadow: 0 4px 10px rgba(1, 1, 32, 0.10); --shadow-lg: 0 12px 32px rgba(1, 1, 32, 0.10);
    --r-sharp: 4px; --r-comfort: 8px;
    --f-display: "Inter", "Helvetica Neue", Arial, sans-serif;
    --f-mono: "JetBrains Mono", Georgia, monospace;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: var(--f-display); font-size: 16px; line-height: 1.3; letter-spacing: -0.16px; color: var(--c-text); background: var(--c-bg); -webkit-font-smoothing: antialiased; }
  h1 { font-size: 46px; font-weight: 500; line-height: 1.05; letter-spacing: -1.2px; }
  h2 { font-size: 30px; font-weight: 500; line-height: 1.1; letter-spacing: -0.6px; }
  h3 { font-size: 20px; font-weight: 500; line-height: 1.2; letter-spacing: -0.2px; }
  p { font-size: 16px; line-height: 1.45; letter-spacing: -0.16px; }
  a { color: inherit; }
  .caption { font-size: 13px; line-height: 1.4; color: var(--c-muted-light); }
  .mono-label { font-family: var(--f-mono); font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: 0.12em; color: var(--c-muted-light); display: inline-block; }
  .container { max-width: 1080px; margin: 0 auto; padding: 0 32px; }
  nav.topnav { position: sticky; top: 0; z-index: 50; backdrop-filter: saturate(180%) blur(14px); -webkit-backdrop-filter: saturate(180%) blur(14px); background: rgba(255,255,255,0.75); border-bottom: 1px solid var(--c-border-light); }
  nav.topnav .container { display: flex; justify-content: space-between; align-items: center; padding-top: 16px; padding-bottom: 16px; gap: 16px; }
  .brand { font-weight: 500; font-size: 18px; display: flex; align-items: center; gap: 10px; text-decoration: none; color: var(--c-text); }
  .brand .dot { width: 10px; height: 10px; border-radius: 2px; background: linear-gradient(135deg, var(--c-magenta), var(--c-lavender)); }
  .navmid a { color: var(--c-text); text-decoration: none; font-size: 14px; }
  .navmid a:hover { opacity: 0.6; }
  .btn-cta { display: inline-flex; align-items: center; gap: 8px; background: var(--c-dark); color: var(--c-text-dark); padding: 10px 18px; border-radius: var(--r-sharp); font-size: 14px; font-weight: 500; text-decoration: none; transition: transform 0.15s ease; }
  .btn-cta:hover { transform: translateY(-1px); }
  .btn-outline { display: inline-flex; align-items: center; gap: 8px; border: 1px solid var(--c-border-light); background: rgba(255,255,255,0.7); color: var(--c-text); padding: 10px 18px; border-radius: var(--r-sharp); font-size: 14px; font-weight: 500; text-decoration: none; }
  .btn-outline:hover { border-color: var(--c-magenta); color: var(--c-magenta); }
  .hero { position: relative; overflow: hidden; padding: 56px 0 48px; }
  .hero::before { content: ""; position: absolute; pointer-events: none; filter: blur(60px); z-index: 0; width: 640px; height: 640px; top: -260px; right: -200px; background: radial-gradient(circle at 30% 30%, rgba(239, 44, 193, 0.26) 0%, transparent 60%), radial-gradient(circle at 70% 70%, rgba(189, 187, 255, 0.45) 0%, transparent 65%); border-radius: 50%; }
  .hero .container { position: relative; z-index: 1; }
  .crumb { font-size: 14px; color: var(--c-muted-light); margin-bottom: 24px; display: inline-block; text-decoration: none; }
  .crumb:hover { color: var(--c-magenta); }
  .hero h1 { margin: 10px 0 14px; }
  .hero .lede { font-size: 19px; line-height: 1.4; color: rgba(0,0,0,0.75); max-width: 60ch; margin-bottom: 24px; }
  .hero-badges { display: flex; gap: 8px; margin-bottom: 4px; flex-wrap: wrap; }
  .badge { font-family: var(--f-mono); font-size: 10px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.1em; padding: 4px 8px; border-radius: var(--r-sharp); background: linear-gradient(135deg, rgba(239,44,193,0.12), rgba(189,187,255,0.25)); color: var(--c-dark); }
  .badge-note { background: var(--c-fill-light); color: var(--c-muted-light); }
  .hero-ctas { display: flex; gap: 10px; flex-wrap: wrap; }
  .layout { display: grid; grid-template-columns: 1fr 320px; gap: 40px; padding: 48px 0 72px; align-items: start; }
  .main-col section + section { margin-top: 48px; border-top: 1px solid var(--c-border-light); padding-top: 40px; }
  .main-col h2 { margin: 6px 0 18px; }
  .offer { display: flex; flex-direction: column; gap: 6px; padding: 16px 0; border-top: 1px solid var(--c-border-light); }
  .offer:first-of-type { border-top: none; }
  .offer h3 { font-size: 17px; }
  .offer p { color: rgba(0,0,0,0.7); font-size: 15px; }
  .price-line { font-size: 26px; font-weight: 600; letter-spacing: -0.4px; margin-bottom: 10px; }
  .review-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 14px 16px; border: 1px solid var(--c-border-light); border-radius: var(--r-comfort); margin-bottom: 10px; }
  .review-row .stars { color: var(--c-orange); font-size: 14px; letter-spacing: 1px; }
  .review-row a { font-size: 14px; font-weight: 500; text-decoration: none; color: var(--c-dark); white-space: nowrap; }
  .review-row a:hover { color: var(--c-magenta); }
  .aside { position: sticky; top: 84px; display: flex; flex-direction: column; gap: 16px; }
  .fact-card { border: 1px solid var(--c-border-light); border-radius: var(--r-comfort); padding: 22px; box-shadow: var(--shadow); background: var(--c-bg); }
  .fact-card h3 { margin-bottom: 14px; font-size: 16px; }
  .fact { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; border-top: 1px solid var(--c-border-light); font-size: 14px; }
  .fact:first-of-type { border-top: none; }
  .fact .k { color: var(--c-muted-light); white-space: nowrap; }
  .fact .v { text-align: right; overflow-wrap: anywhere; }
  .fact .v a { text-decoration: none; color: var(--c-dark); font-weight: 500; }
  .fact .v a:hover { color: var(--c-magenta); }
  .tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
  .tag { font-size: 12px; padding: 4px 9px; border-radius: 999px; background: var(--c-fill-light); border: 1px solid var(--c-border-light); }
  .case { padding: 16px 0; border-top: 1px solid var(--c-border-light); }
  .case:first-of-type { border-top: none; }
  .case h3 { font-size: 17px; }
  .case h3 a { text-decoration: none; color: var(--c-dark); }
  .case h3 a:hover { color: var(--c-magenta); }
  .case p { color: rgba(0,0,0,0.7); font-size: 15px; margin-top: 4px; }
  .sw-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; margin-top: 16px; }
  .sw-col h3 { font-size: 15px; margin-bottom: 6px; }
  .sw-col ul { list-style: none; }
  .sw-col li { font-size: 15px; line-height: 1.45; padding: 9px 0 9px 18px; position: relative; border-top: 1px solid var(--c-border-light); }
  .sw-col li:first-child { border-top: none; }
  .sw-col li::before { content: ""; position: absolute; left: 0; top: 15px; width: 7px; height: 7px; border-radius: 2px; }
  .sw-plus li::before { background: linear-gradient(135deg, var(--c-magenta), var(--c-lavender)); }
  .sw-minus li::before { background: var(--c-fill-light); border: 1px solid rgba(0,0,0,0.25); }
  .score-group { margin-top: 24px; }
  .score-row { padding: 12px 0; border-top: 1px solid var(--c-border-light); }
  .score-row:last-child { padding-bottom: 2px; }
  .score-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
  .score-name { font-weight: 500; font-size: 15px; }
  .score-num { font-family: var(--f-mono); font-size: 12px; color: var(--c-muted-light); white-space: nowrap; }
  .score-bar { display: flex; gap: 4px; margin: 8px 0 6px; }
  .score-bar .seg { width: 34px; height: 6px; border-radius: 3px; background: var(--c-fill-light); border: 1px solid var(--c-border-light); }
  .score-bar .seg.on { background: linear-gradient(135deg, var(--c-magenta), var(--c-lavender)); border-color: transparent; }
  .score-ev { font-size: 13px; color: var(--c-muted-light); line-height: 1.4; }
  .cta-band { background: var(--c-dark); color: var(--c-text-dark); border-radius: var(--r-comfort); padding: 36px; margin: 0 0 64px; display: flex; flex-wrap: wrap; gap: 20px; align-items: center; justify-content: space-between; }
  .cta-band h2 { font-size: 24px; letter-spacing: -0.4px; max-width: 26ch; }
  .cta-band p { color: rgba(255,255,255,0.75); max-width: 56ch; margin-top: 6px; font-size: 15px; }
  .btn-light { display: inline-flex; background: var(--c-text-dark); color: var(--c-dark); padding: 11px 20px; border-radius: var(--r-sharp); font-weight: 500; font-size: 14px; text-decoration: none; }
  .btn-light:hover { background: var(--c-lavender); }
  footer { border-top: 1px solid var(--c-border-light); padding: 32px 0; }
  footer .container { display: flex; flex-wrap: wrap; gap: 12px; justify-content: space-between; }
  footer a { color: var(--c-muted-light); }
  @media (max-width: 880px) {
    .container { padding: 0 16px; }
    h1 { font-size: 34px; }
    .layout { grid-template-columns: 1fr; gap: 24px; padding: 32px 0 56px; }
    .aside { position: static; }
    .navmid { display: none; }
    .sw-grid { grid-template-columns: 1fr; gap: 12px; }
    .score-bar .seg { width: 24px; }
  }
"""


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s


def esc(s):
    return html.escape(str(s), quote=True)


def stars(rating):
    full = int(round(float(rating)))
    full = max(0, min(5, full))
    return "★" * full + "☆" * (5 - full)


def fact(k, v_html):
    return f'<div class="fact"><span class="k">{esc(k)}</span><span class="v">{v_html}</span></div>'


def build_profile(a):
    slug = slugify(a["name"])
    name = a["name"]
    loc = ", ".join(x for x in [a.get("city"), a.get("country")] if x) or a["region"]
    price = f"From ${a['priceMonthlyUSD']:,}/mo" if a.get("priceMonthlyUSD") else "Pricing on request"
    canonical = f"{BASE_URL}agencies/{slug}/"
    is_auq = name == "AUQ"

    badges = ""
    if a.get("specialist"):
        badges += '<span class="badge">GEO specialist</span>'
    else:
        badges += '<span class="badge badge-note">Wider agency</span>'
    if a.get("disclosure"):
        badges += f'<span class="badge badge-note">{esc(a["disclosure"])}</span>'

    # Offerings
    offers = ""
    for s in a["services"]:
        blurb = SERVICE_BLURBS.get(s, "")
        offers += f'<div class="offer"><h3>{esc(s)}</h3><p>{esc(blurb)}</p></div>'

    # Pricing
    pricing = f'<p class="price-line">{esc(price)}</p>'
    if a.get("priceNote"):
        pricing += f"<p>{esc(a['priceNote'])}</p>"
    elif not a.get("priceMonthlyUSD"):
        pricing += f"<p>{esc(name)} does not publish pricing. Expect a scoped proposal after an intro call.</p>"
    pricing += '<p class="caption" style="margin-top:10px;">Prices in other currencies are converted at approximate rates. Confirm current pricing and scope with the agency before signing.</p>'

    # Reviews
    reviews = a.get("reviews") or []
    if reviews:
        rhtml = ""
        for r in reviews:
            count = f" · {r['count']} reviews" if r.get("count") else ""
            rating = f"{r['rating']:.1f}" if isinstance(r.get("rating"), (int, float)) else ""
            rhtml += (
                '<div class="review-row">'
                f'<div><strong>{esc(r["platform"])}</strong> '
                f'<span class="stars">{stars(r["rating"])}</span> '
                f'<span class="caption">{rating}{esc(count)}</span></div>'
                f'<a href="{esc(r["url"])}" target="_blank" rel="noopener nofollow">Read reviews &rarr;</a>'
                "</div>"
            )
        rhtml += f'<p class="caption">Ratings read from each platform in {LAST_CHECKED}; they change, so check the live profile.</p>'
    else:
        rhtml = (
            f"<p>No independent review profile was verified for {esc(name)} as of {LAST_CHECKED}.</p>"
            '<p style="margin-top:8px;">Absence of reviews is common for young GEO specialists. Weigh named clients and published case studies instead, and ask for references on a call.</p>'
        )

    # Case studies
    cs = a.get("caseStudies") or []
    if cs:
        cs_html = "".join(
            '<div class="case">'
            f'<h3><a href="{esc(c["url"])}" target="_blank" rel="noopener nofollow">{esc(c["title"])}</a></h3>'
            f'<p>{esc(c["summary"])}</p></div>'
            for c in cs[:3]
        )
        cs_html += f'<p class="caption" style="margin-top:10px;">Read from {esc(name)}&#39;s own site in {LAST_CHECKED}. The numbers are the agency&#39;s published claims, quoted as found.</p>'
    else:
        cs_html = (
            f"<p>I found no case studies on {esc(name)}&#39;s site as of {LAST_CHECKED}.</p>"
            '<p style="margin-top:8px;">Ask for two or three recent GEO results on the intro call, with the prompt set they tracked and the before and after numbers.</p>'
        )
    case_section = (
        '<section><span class="mono-label">Case studies</span>'
        f"<h2>Case studies {esc(name)} publishes</h2>{cs_html}</section>"
    )

    # Strengths and weaknesses
    sw_section = ""
    if a.get("strengths") or a.get("weaknesses"):
        plus = "".join(f"<li>{esc(s)}</li>" for s in a.get("strengths") or [])
        minus = "".join(f"<li>{esc(s)}</li>" for s in a.get("weaknesses") or [])
        auq_sw = " AUQ is my agency, so read this one as a self-assessment." if is_auq else ""
        sw_section = (
            '<section><span class="mono-label">Strengths &amp; weaknesses</span>'
            f"<h2>Where {esc(name)} is strong, and what to check</h2>"
            f'<p class="caption">Observations from reading {esc(name)}&#39;s site and public profiles in {LAST_CHECKED}.{auq_sw}</p>'
            '<div class="sw-grid">'
            f'<div class="sw-col sw-plus"><h3>Strengths</h3><ul>{plus}</ul></div>'
            f'<div class="sw-col sw-minus"><h3>Weaknesses</h3><ul>{minus}</ul></div>'
            "</div></section>"
        )

    # Capability scorecard
    score_section = ""
    avg_grade = None
    scores = a.get("scores") or {}
    if scores:
        groups_html = ""
        vals = []
        for gname, crits in SCORE_GROUPS:
            rows = ""
            for key, label in crits:
                sc = scores.get(key) or {}
                try:
                    n = int(sc.get("score") or 1)
                except (TypeError, ValueError):
                    n = 1
                n = max(1, min(5, n))
                vals.append(n)
                ev = sc.get("evidence") or "No public evidence"
                segs = "".join(
                    f'<span class="seg{" on" if i < n else ""}"></span>' for i in range(5)
                )
                rows += (
                    '<div class="score-row">'
                    f'<div class="score-head"><span class="score-name">{esc(label)}</span><span class="score-num">{n}/5</span></div>'
                    f'<div class="score-bar">{segs}</div>'
                    f'<p class="score-ev">{esc(ev)}</p>'
                    "</div>"
                )
            groups_html += f'<div class="score-group"><span class="mono-label">{esc(gname)}</span>{rows}</div>'
        avg_grade = sum(vals) / len(vals)
        auq_sc = " AUQ is my agency, so these grades are self-assigned against the same rubric. Discount accordingly." if is_auq else ""
        score_section = (
            '<section><span class="mono-label">Capability scorecard</span>'
            f"<h2>What {esc(name)} shows evidence of doing</h2>"
            f'<p class="caption">Each grade reflects public evidence on {esc(name)}&#39;s own site as of {LAST_CHECKED}. A 5 is a productized offering with documented results. A 1 means I found no public evidence, which happens for services an agency delivers without writing about them. Use the low grades as questions for the intro call.{auq_sc}</p>'
            f"{groups_html}</section>"
        )

    # Clients
    clients_html = ""
    if a.get("clients"):
        clients_html = (
            '<section><span class="mono-label">Clients</span><h2>Clients named on their site</h2><div class="tags">'
            + "".join(f'<span class="tag">{esc(c)}</span>' for c in a["clients"])
            + "</div></section>"
        )

    # Aside: quick facts + contact
    facts = fact("Location", esc(loc)) + fact("Region", esc(a["region"]))
    facts += fact("Type", "GEO specialist" if a.get("specialist") else "Wider agency")
    if a.get("founded"):
        facts += fact("Founded", esc(a["founded"]))
    facts += fact("Starting price", esc(price))
    if avg_grade is not None:
        facts += fact("Evidence grade", f"{avg_grade:.1f}/5")

    website_host = re.sub(r"^https?://(www\.)?|/$", "", a["website"])
    contact = fact("Website", f'<a href="{esc(a["website"])}" target="_blank" rel="noopener nofollow">{esc(website_host)}</a>')
    if a.get("contactUrl"):
        contact += fact("Contact page", f'<a href="{esc(a["contactUrl"])}" target="_blank" rel="noopener nofollow">Open &rarr;</a>')
    if a.get("email"):
        contact += fact("Email", f'<a href="mailto:{esc(a["email"])}">{esc(a["email"])}</a>')
    if a.get("phone"):
        tel = re.sub(r"[^0-9+]", "", a["phone"])
        contact += fact("Phone", f'<a href="tel:{esc(tel)}">{esc(a["phone"])}</a>')

    socials = ""
    for key, label in SOCIAL_LABELS:
        if a.get(key):
            socials += fact(label, f'<a href="{esc(a[key])}" target="_blank" rel="noopener nofollow">Open &rarr;</a>')
    socials_card = (
        f'<div class="fact-card"><h3>Socials</h3>{socials}</div>' if socials else ""
    )

    # CTA band
    if is_auq:
        band = (
            '<div class="cta-band"><div><h2>Want to know where you stand in AI search?</h2>'
            "<p>We run GEO audits that measure how AI assistants currently represent your brand: trigger rate, citation rate, and share of voice against named competitors.</p></div>"
            '<a class="btn-light" href="https://auq.io/contact/" target="_blank" rel="noopener">Get a GEO audit</a></div>'
        )
    else:
        band = (
            '<div class="cta-band"><div><h2>Briefing agencies? Know where you stand first.</h2>'
            f"<p>AUQ, the agency behind this directory, runs GEO audits that measure how AI assistants currently represent your brand. Useful before you brief {esc(name)} or anyone else on the list.</p></div>"
            '<a class="btn-light" href="https://auq.io/contact/" target="_blank" rel="noopener">Get a GEO audit</a></div>'
        )

    # JSON-LD
    ld = {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "name": name,
        "url": a["website"],
        "description": a["description"],
    }
    addr = {}
    if a.get("city"):
        addr["addressLocality"] = a["city"]
    if a.get("country"):
        addr["addressCountry"] = a["country"]
    if addr:
        ld["address"] = dict({"@type": "PostalAddress"}, **addr)
    same_as = [a[k] for k, _ in SOCIAL_LABELS if a.get(k)]
    if same_as:
        ld["sameAs"] = same_as
    ld_json = json.dumps(ld, indent=2, ensure_ascii=False)

    title = f"{name}: GEO agency profile"
    meta_desc = (a["description"][:150] + "…") if len(a["description"]) > 155 else a["description"]

    return slug, f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(meta_desc)}">
<link rel="canonical" href="{esc(canonical)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>

<nav class="topnav">
  <div class="container">
    <a class="brand" href="https://auq.io" target="_blank" rel="noopener"><span class="dot"></span>AUQ</a>
    <span class="navmid"><a href="../../">All GEO agencies</a></span>
    <a class="btn-cta" href="https://auq.io/contact/" target="_blank" rel="noopener">Talk to AUQ</a>
  </div>
</nav>

<header class="hero">
  <div class="container">
    <a class="crumb" href="../../">&larr; GEO Agency Finder</a>
    <div class="hero-badges">{badges}</div>
    <h1>{esc(name)}</h1>
    <p class="mono-label">{esc(loc)}</p>
    <p class="lede">{esc(a["description"])}</p>
    <div class="hero-ctas">
      <a class="btn-cta" href="{esc(a["website"])}" target="_blank" rel="noopener nofollow">Visit site</a>
      {f'<a class="btn-outline" href="{esc(a["contactUrl"])}" target="_blank" rel="noopener nofollow">Contact {esc(name)}</a>' if a.get("contactUrl") else ""}
    </div>
  </div>
</header>

<div class="container">
  <div class="layout">
    <div class="main-col">
      <section>
        <span class="mono-label">Core offerings</span>
        <h2>What {esc(name)} sells</h2>
        <p class="caption">The selection below comes from {esc(name)}&#39;s own site; the category descriptions are this directory&#39;s.</p>
        {offers}
      </section>
      {case_section}
      {sw_section}
      {score_section}
      <section>
        <span class="mono-label">Pricing</span>
        <h2>What {esc(name)} costs</h2>
        {pricing}
      </section>
      <section>
        <span class="mono-label">Reviews</span>
        <h2>Independent reviews</h2>
        {rhtml}
      </section>
      {clients_html}
    </div>
    <aside class="aside">
      <div class="fact-card"><h3>Quick facts</h3>{facts}</div>
      <div class="fact-card"><h3>Contact</h3>{contact}</div>
      {socials_card}
    </aside>
  </div>
  {band}
</div>

<footer>
  <div class="container">
    <span class="caption"><a href="../../">GEO Agency Finder</a>, maintained by <a href="https://auq.io" target="_blank" rel="noopener">AUQ</a>.</span>
    <span class="caption">Details verified {LAST_CHECKED}. Confirm everything with the agency.</span>
  </div>
</footer>

<script type="application/ld+json">
{ld_json}
</script>
</body>
</html>
"""


def main():
    agencies = json.loads((ROOT / "agencies.json").read_text())

    # data.js for the directory page (adds slug for profile links).
    # Profile-only fields stay out of it to keep the directory payload small.
    PROFILE_ONLY = {"caseStudies", "strengths", "weaknesses", "scores"}
    for a in agencies:
        a["slug"] = slugify(a["name"])
    slim = [{k: v for k, v in a.items() if k not in PROFILE_ONLY} for a in agencies]
    data_js = (
        "/* Generated by build.py from agencies.json. Do not edit by hand. */\n"
        "var AGENCIES = " + json.dumps(slim, indent=2, ensure_ascii=False) + ";\n"
    )
    (ROOT / "data.js").write_text(data_js)

    urls = [BASE_URL]
    for a in agencies:
        slug, page = build_profile(a)
        out = ROOT / "agencies" / slug
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(page)
        urls.append(f"{BASE_URL}agencies/{slug}/")

    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
    sitemap += "</urlset>\n"
    (ROOT / "sitemap.xml").write_text(sitemap)

    print(f"Built {len(agencies)} profiles, data.js, sitemap.xml")


if __name__ == "__main__":
    main()
