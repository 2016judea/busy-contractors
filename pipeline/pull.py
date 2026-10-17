#!/usr/bin/env python3
"""Pull Minneapolis building permits that are still open (CCS_Permits, live) and the MN DLI
contractor licence + registration exports (phone, email), into pipeline/cache/ (gitignored)."""
import datetime as dt, json, subprocess, urllib.parse, urllib.request
from pathlib import Path

C = Path(__file__).resolve().parent / "cache"
C.mkdir(exist_ok=True)
U = "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/CCS_Permits/FeatureServer/0/query"
since = (dt.date.today() - dt.timedelta(days=365)).isoformat()
where = f"status='Issued' AND permitType IN ('Commercial','Res','Wrecking') AND issueDate >= date '{since}'"
rows, off = [], 0
while True:
    p = urllib.parse.urlencode(dict(where=where, outFields="*", f="json", resultOffset=off, resultRecordCount=2000, orderByFields="issueDate DESC", returnGeometry="false"))
    d = json.load(urllib.request.urlopen(U + "?" + p))
    fs = [f["attributes"] for f in d["features"]]
    rows += fs
    if not d.get("exceededTransferLimit") or not fs:
        break
    off += len(fs)
(C / "permits.json").write_text(json.dumps(rows))
print("open permits", len(rows), "issued since", since)
for name in ("Residential_Contractors", "Contractor_Registrations"):
    out = C / ("dli_res.csv" if name.startswith("Res") else "dli_reg.csv")
    # curl, not urllib: Python's TLS fails on this host's chain ("self-signed in chain") where curl works
    subprocess.run(["curl", "-sfL", "-A", "Mozilla/5.0", "-o", str(out), f"https://secure.doli.state.mn.us/ccld/data/MNDLILicRegCertExport_{name}.csv"], check=True)
    print(out.name, out.stat().st_size)
