"""Stage 2 - Normalise: map raw NVE records to one schema and keep active Innlandet warnings.

This list is the single source of truth for every fact in the digest
(IDs, levels, areas, dates). The language model never produces these fields.
"""
import json
import sys

import common

LEVEL_NAMES = {2: "gult", 3: "oransje", 4: "rødt"}


def county_ids(rec):
    return {str(c.get("Id")) for c in (rec.get("CountyList") or [])}


def innlandet_municipalities(rec):
    names = []
    for m in rec.get("MunicipalityList") or []:
        counties = {str(c.get("Id")) for c in (m.get("CountyList") or [])}
        if not counties or common.INNLANDET in counties:
            if m.get("Name"):
                names.append(m["Name"])
    return names


def parse_level(value, wid):
    """NVE ActivityLevel as an int. A missing level counts as 0 (no warning), as before."""
    if value in (None, ""):
        return 0
    if isinstance(value, bool) or not (isinstance(value, int) or (isinstance(value, str) and value.strip().isdigit())):
        sys.exit(f"NVE warning {wid} has ActivityLevel {value!r}, not a whole number; no digest produced.")
    return int(value)


def normalise(raw):
    by_id = {}
    for rec in raw:
        # Malformed records stop the run with a clear message instead of a crash.
        if rec.get("Id") in (None, ""):
            sys.exit("NVE record without Id; no digest produced.")
        wid = str(rec["Id"])
        level = parse_level(rec.get("ActivityLevel"), wid)
        if level < common.MIN_LEVEL:
            continue
        # An active warning with no county list could be for Innlandet: never give a silent all-clear.
        if not rec.get("CountyList"):
            sys.exit(f"NVE warning {wid} has no CountyList, so we cannot tell if it is for Innlandet; no digest produced.")
        if common.INNLANDET not in county_ids(rec):
            continue
        # A warning without a validity period cannot be checked or acted on: stop.
        missing = [f for f in ("ValidFrom", "ValidTo") if not rec.get(f)]
        if missing:
            sys.exit(f"NVE warning {wid} has no {' or '.join(missing)}; no digest produced.")
        # NVE sends one record per municipality with the same Id: merge them.
        if wid in by_id:
            w = by_id[wid]
            if (w["danger_level"], w["valid_from"], w["valid_to"]) != (level, rec.get("ValidFrom"), rec.get("ValidTo")):
                sys.exit(f"NVE records for warning {wid} disagree on level or validity; no digest produced.")
            for name in innlandet_municipalities(rec):
                if name not in w["_municipalities"]:
                    w["_municipalities"].append(name)
            continue
        by_id[wid] = {
            "source": "nve-flood",
            "warning_id": wid,
            "type": "flood",
            "danger_level": level,
            "danger_colour": LEVEL_NAMES.get(level, str(level)),
            "valid_from": rec.get("ValidFrom"),
            "valid_to": rec.get("ValidTo"),
            # Official text, passed to the model as data only:
            "main_text": rec.get("MainText") or "",
            "warning_text": rec.get("WarningText") or "",
            "advice_text": rec.get("AdviceText") or "",
            "_municipalities": innlandet_municipalities(rec),
        }
    warnings = list(by_id.values())
    for w in warnings:
        w["area"] = ", ".join(w.pop("_municipalities")) or "Innlandet"
    warnings.sort(key=lambda w: (w["valid_from"] or "", w["warning_id"]))
    common.NORMALISED_FILE.write_text(json.dumps(warnings, ensure_ascii=False, indent=2), encoding="utf-8")
    return warnings
