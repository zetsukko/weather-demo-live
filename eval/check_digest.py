"""Binary check for out/digest.json against the raw NVE response used in the same run.

Exit 0 and print PASS if every property in SPEC.md "Definition of success" holds,
otherwise exit 1 with the first failing property.

Inputs:  out/raw_nve_flood.json  (raw source, written by harness/fetch.py)
         out/digest.json         (written by harness/assemble.py)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "out" / "raw_nve_flood.json"
DIGEST = ROOT / "out" / "digest.json"

INNLANDET = "34"
MIN_LEVEL = 2
MAX_WORDS = 60
NUMBER = re.compile(r"\d+")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"(?<!\d)(?:\+47\s?)?(?:\d[\s]?){8}(?!\d)")


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def county_ids(rec):
    return {str(c.get("Id")) for c in (rec.get("CountyList") or [])}


raw = json.loads(RAW.read_text(encoding="utf-8"))
digest = json.loads(DIGEST.read_text(encoding="utf-8"))

if not isinstance(raw, list):
    fail("raw source is not a list of warnings")

source = {}
for rec in raw:
    if int(rec.get("ActivityLevel") or 0) >= MIN_LEVEL and INNLANDET in county_ids(rec):
        source[str(rec["Id"])] = rec

warnings = digest.get("warnings")
if not isinstance(warnings, list):
    fail("digest has no warnings list")

# 1 completeness + exactly once
ids = [str(w.get("warning_id")) for w in warnings]
for wid in source:
    n = ids.count(wid)
    if n != 1:
        fail(f"property 1: source warning {wid} appears {n} times in digest")

# 2 no invention
for wid in ids:
    if wid not in source:
        fail(f"property 2: digest warning {wid} is not an active Innlandet warning in the source")

for w in warnings:
    wid = str(w["warning_id"])
    rec = source[wid]
    # 3 fidelity
    if int(w.get("danger_level")) != int(rec.get("ActivityLevel")):
        fail(f"property 3: danger_level differs for {wid}")
    if w.get("valid_from") != rec.get("ValidFrom") or w.get("valid_to") != rec.get("ValidTo"):
        fail(f"property 3: validity period differs for {wid}")
    # 4 locality
    if INNLANDET not in county_ids(rec):
        fail(f"property 4: {wid} does not list Innlandet")
    # 5 grounded summary
    summary = w.get("summary_no") or ""
    if not summary.strip():
        fail(f"property 5: empty summary for {wid}")
    if len(summary.split()) > MAX_WORDS:
        fail(f"property 5: summary for {wid} has more than {MAX_WORDS} words")
    source_numbers = set(NUMBER.findall(json.dumps(rec, ensure_ascii=False)))
    for num in NUMBER.findall(summary):
        if num not in source_numbers and num.lstrip("0") not in source_numbers:
            fail(f"property 5: number '{num}' in summary for {wid} is not in the source")

text = json.dumps(digest, ensure_ascii=False)

# 6 attribution and privacy
attribution = " ".join(digest.get("attribution") or [])
if "NVE" not in attribution or "varsom.no" not in attribution:
    fail("property 6: NVE/varsom.no attribution missing")
if EMAIL.search(text):
    fail("property 6: digest contains an e-mail address")
for w in warnings:
    if PHONE.search(w.get("summary_no") or ""):
        fail("property 6: summary contains a phone number")

# 7 empty case
if not source:
    if warnings or not digest.get("no_warnings_message"):
        fail("property 7: no active warnings in source, but digest does not say so")

print(f"PASS ({len(source)} active Innlandet warning(s) checked)")
