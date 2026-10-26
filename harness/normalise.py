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


def normalise(raw):
    by_id = {}
    for rec in raw:
        level = int(rec.get("ActivityLevel") or 0)
        if level < common.MIN_LEVEL or common.INNLANDET not in county_ids(rec):
            continue
        wid = str(rec["Id"])
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
