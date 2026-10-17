#!/usr/bin/env python3
"""Build Busy Contractors: the Minneapolis contractors with the most open jobs right now.

Inputs (pipeline/cache/, gitignored; pull.py): permits.json (CCS_Permits, status Issued,
issued in the last 12 months) and the MN DLI licence/registration CSVs (phone, email).
Writes the free slice to site/ and every row to private/bundle/ via kit/publish.py.
"""
import collections, csv, datetime as dt, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "kit"))
from publish import publish  # noqa: E402

C = ROOT / "pipeline/cache"
PRODUCT = json.loads((ROOT / "product.json").read_text())
TODAY = dt.date.today()
MIN_JOBS = 2
D = lambda x: dt.datetime.fromtimestamp(x / 1000, dt.timezone.utc).date() if x else None
BIZ = re.compile(r"\b(INC|LLC|L\.L\.C|CORP|CORPORATION|CO|COMPANY|CONST|CONSTRUCTION|BUILD|BUILDERS|BUILDING|HOMES|REMODEL|REMODELING|DESIGN|GROUP|"
                 r"ROOF|ROOFING|EXTERIORS|CONTRACT\w*|SERVICES|RENOVAT\w*|ENTERPRISES|COMPANIES|LTD|SOLUTIONS|WRECKING|EXCAVAT\w*|DEMOLITION|"
                 r"CARPENTRY|MASONRY|CONCRETE|GARAGES?|WINDOWS?|SIDING|RESTORATION|INTERIORS|PROPERT\w*|DEVELOP\w*)\b", re.I)
SKIP = re.compile(r"solar|photovoltaic|\bpv\b|drain ?tile|sump|revision after issuance", re.I)
SUFFIX = re.compile(r"\b(INC|LLC|L L C|CORP|CORPORATION|CO|COMPANY|LTD|LLP|PLLC|INCORPORATED|THE|OF|AND|MN|MINNESOTA)\b")
CATS = ["Teardown", "New build or addition", "Remodel", "Roof, siding, windows"]
CUT = re.compile(r"\s*(certificate of occupancy|const\.? type|building code|energy code|2020 m[sn]bc|2020 irc|engineer:|architect:|special inspection|"
                 r"\(maa\)|\(jjl\)|\(acw\)|-acw|contact|mechanical permit).*", re.I | re.S)


def norm(n):
    n = re.sub(r"[^A-Z0-9 ]", " ", (n or "").upper().replace("&", " AND "))
    return " ".join(SUFFIX.sub(" ", n).split())


def title(s):
    out = []
    for w in (s or "").split():
        if re.match(r"^\d+(st|nd|rd|th)$", w, re.I): out.append(w.lower())
        elif re.match(r"^(\d|[NSEW]{1,2}$|LLC,?$|INC\.?,?$|II$|HNH$)", w, re.I): out.append(w.upper().replace("INC", "Inc"))
        else: out.append(w.capitalize())
    return " ".join(out)


def phone(p):
    d = re.sub(r"\D", "", p or "")
    return f"{d[:3]}-{d[3:6]}-{d[6:]}" if len(d) == 10 else ""


def what(s):
    s = (s or "").strip()
    if s.lower().startswith("source information"): return ""
    s = re.sub(r"^\(DMH[^)]*\)\s*", "", s)
    s = re.sub(r"\s+", " ", CUT.sub("", s)).strip(" .-;,")
    return (s.capitalize() if s.isupper() else s)[:140]


def cat(x):
    if x["permitType"] == "Wrecking": return "Teardown"
    if x["workType"] in ("New", "Addition", "Accessory"): return "New build or addition"
    if x["workType"] in ("Misc", "RoofWind"): return "Roof, siding, windows"
    return "Remodel"


# MN DLI: name and DBA -> (phone, email, address). Issued licences first, so a lapsed duplicate never wins.
dli = {}
for f in ("dli_res.csv", "dli_reg.csv"):
    for r in sorted(csv.DictReader(open(C / f, encoding="latin-1")), key=lambda r: r["Status"] != "Issued"):
        if r["Bus_Pers"] != "Business": continue
        rec = (phone(r["Phone_No"]), (r["Email_Address"] or "").strip().lower(), title(f"{r['Addr1']} {r['City']}"), r["Lic_Number"], r["Status"])
        for n in [r["Name"]] + [x for x in re.split(r",\s*", r["DBA_Name"] or "") if x]:
            dli.setdefault(norm(n), rec)

jobs = collections.defaultdict(dict)   # contractor -> address -> job
raw_name, app_addr = {}, {}
for x in json.loads((C / "permits.json").read_text()):
    n = (x["applicantName"] or "").strip()
    if not n or not BIZ.search(n) or not x["Latitude"] or SKIP.search(x["comments"] or ""): continue
    k = norm(n)
    if not k: continue
    raw_name.setdefault(k, n)
    app_addr.setdefault(k, title(" ".join(filter(None, [x.get("applicantAddress1"), x.get("applicantCity")]))))
    a = x["Display"]
    j = jobs[k].get(a)
    issued = D(x["issueDate"])
    if j and j["issued"] >= issued: continue
    jobs[k][a] = {"addr": title(a), "cat": cat(x), "issued": issued, "what": what(x["comments"]), "hood": x["Neighborhoods_Desc"] or "",
                  "stage": "Final inspection" if x["milestone"] == "Final Inspection" else "Under way", "fee": round(x["totalFees"] or 0),
                  "lat": round(x["Latitude"], 5), "lon": round(x["Longitude"], 5), "permit": x["permitNumber"]}

items, points, matched = [], [], 0
for k, js in jobs.items():
    if len(js) < MIN_JOBS: continue
    js = sorted(js.values(), key=lambda j: j["issued"], reverse=True)
    mix = collections.Counter(j["cat"] for j in js)
    g = mix.most_common(1)[0][0]
    name = title(raw_name[k])
    p, e, ad, lic, st = dli.get(k, ("", "", "", "", ""))
    if lic: matched += 1
    office = ad or app_addr.get(k, "")
    hoods = collections.Counter(j["hood"] for j in js if j["hood"])
    contact = " · ".join(x for x in [f'<a href="tel:{p}">{p}</a>' if p else "", f'<a href="mailto:{e}">{e}</a>' if e else "", office] if x)
    items.append({
        "id": k[:60], "g": g, "t": name, "tag": f"{len(js)} open jobs", "hot": len(js) >= 10,
        "w": ", ".join(f"{v} {c.lower()}" for c, v in mix.most_common()),
        "m": ["Mostly " + ", ".join(h for h, _ in hoods.most_common(2)) if hoods else "", f"Newest permit {js[0]['issued']:%b %-d}",
              f"{sum(j['stage'] == 'Final inspection' for j in js)} at final inspection" if any(j['stage'] == 'Final inspection' for j in js) else ""],
        "lat": js[0]["lat"], "lon": js[0]["lon"],
        "k": {"jobs": -len(js), "newest": -int(js[0]["issued"].strftime("%Y%m%d")), "name": name.lower(), "tear": -(mix["Teardown"] + mix["New build or addition"])},
        "c": (contact + (f" · MN licence {lic}" if lic else "")) or "No phone on file; the permit gives no address",
        "rows_label": f"All {len(js)} job addresses",
        "rows": [{"a": j["addr"], "m": f"{j['cat']} · {j['stage']} · permit {j['issued']:%b %-d} · {j['what'][:80]}", "lat": j["lat"], "lon": j["lon"]} for j in js],
        "csv": [[name, p, e, office, j["addr"], j["hood"], j["cat"], j["stage"], j["issued"].isoformat(), j["what"], j["fee"], j["permit"]] for j in js],
    })
    for j in js:
        points.append([round(j["lat"], 3), round(j["lon"], 3), g])

items.sort(key=lambda i: i["k"]["jobs"])
points = [list(p) for p in sorted({tuple(p) for p in points})]
gc = collections.Counter(i["g"] for i in items)
njobs = sum(-i["k"]["jobs"] for i in items)
ten = sum(-i["k"]["jobs"] >= 10 for i in items)
free_items = [{**{k: v for k, v in i.items() if k not in ("c", "csv", "rows")}, "rows_locked": f"{-i['k']['jobs']} job addresses and the phone in the full list"} for i in items[:10]]
built = TODAY.isoformat()
free = {
    "built": built,
    "eyebrow": f"Busy Contractors · Minneapolis building permits · built {TODAY:%b %-d, %Y}",
    "h1": f"{len(items)} contractors running {njobs:,} open jobs in Minneapolis right now",
    "lede": (f"Every job site makes debris, and every open building permit names the contractor running it. "
             f"These are the contractors with two or more open Minneapolis permits from the last twelve months, ranked by jobs. "
             f"<b>{ten} have ten or more going at once.</b>"),
    "stats": [[str(len(items)), "contractors with 2+ open jobs"], [f"{njobs:,}", "open job addresses between them"], [str(ten), "with 10 or more"]],
    "pay_h": f"The full list: all {len(items)} contractors, every job address",
    "pay_line": ("Each contractor's phone, email and office from their state licence, every open job address with the work and the date it started, "
                 "the sort by the job nearest you, and the spreadsheet."),
    "checkout_line": f"{len(items)} Minneapolis contractors with {njobs:,} open job addresses and their licence phone and email.",
    "noun": "contractors",
    "ghost": "Example Construction Inc · 612-555-0100 · 14 job addresses",
    "total": len(items),
    "group_counts": {g: gc[g] for g in CATS},
    "group_order": CATS,
    "legend": [["Teardown", "var(--hot)"], ["New build or addition", "var(--c2)"], ["Remodel", "var(--accent)"], ["Roof, siding, windows", "var(--mid)"]],
    "points": points,
    "sorts": [{"key": "jobs", "label": "Most open jobs"}, {"key": "near", "label": "Nearest job to", "near": True, "paid": True},
              {"key": "tear", "label": "Most teardowns and new builds", "paid": True}, {"key": "newest", "label": "Newest permit", "paid": True}],
    "origins": [["Coon Rapids", 45.1732, -93.3030], ["Champlin", 45.1889, -93.3975], ["Downtown Minneapolis", 44.9778, -93.2650],
                ["Saint Paul", 44.9537, -93.0900], ["Bloomington", 44.8408, -93.2983], ["Brooklyn Park", 45.0941, -93.3563]],
    "csv_cols": ["contractor", "phone", "email", "office", "job address", "neighborhood", "work", "stage", "permit issued", "description", "permit fee", "permit"],
    "items": free_items,
    "note": (f"<p>Sources: City of Minneapolis building permit register (CCS_Permits), pulled {built}: building, remodel, roofing and wrecking permits "
             f"still open and issued since {(TODAY - dt.timedelta(days=365)):%b %-d, %Y}, one row per job address. Phone and email come from the "
             f"Minnesota Department of Labor and Industry licence and registration lists, matched on company name ({matched} of {len(items)} matched); "
             f"otherwise the office is the address on the permit.</p><p>Homeowner-pulled permits and solar and drain-tile jobs are left out. Minneapolis only: "
             f"St. Paul stopped publishing permits in mid-2025.</p><p>Made by Aidan Jude at Brick &amp; Mortar (aidan@brickandmortar.dev).</p>"),
}
publish(ROOT, PRODUCT, free, {"items": items})
print(f"contractors {len(items)} · jobs {njobs} · 10+: {ten} · DLI matched {matched} · groups {dict(gc)}")
