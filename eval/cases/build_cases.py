"""Rebuild eval/cases/<case>/nve.json from the real NVE fixture of 26.10.2026.

  py eval/cases/build_cases.py

Every derived case is a small, documented change to the real response, so the test set
stays close to what NVE actually sends. expected.json in each folder is written by hand
and is not touched by this script.
"""
import copy
import json
import shutil
from pathlib import Path

CASES = Path(__file__).resolve().parent
ROOT = CASES.parent.parent
FIXTURE = ROOT / "fixtures" / "nve_flood_innlandet.json"
WARNING_ID = "584962"   # the one active (yellow) Innlandet warning in the 26.10 fixture


def load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def warning_records(data):
    recs = [r for r in data if str(r.get("Id")) == WARNING_ID]
    assert len(recs) == 5, f"expected 5 records for {WARNING_ID}, found {len(recs)}"
    return recs


def write(name, data):
    folder = CASES / name
    folder.mkdir(exist_ok=True)
    (folder / "nve.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def set_level(level):
    data = load()
    for r in warning_records(data):
        r["ActivityLevel"] = level
    return data


def multi_county():
    data = load()
    for r in warning_records(data):
        r["CountyList"].append({"Id": "31", "Name": "Viken", "MunicipalityList": [], "HighestActivityLevel": None})
    return data


def other_county_only():
    data = load()
    rec = copy.deepcopy(warning_records(data)[0])
    rec["Id"] = "990001"
    rec["CountyList"] = [{"Id": "46", "Name": "Vestland", "MunicipalityList": [], "HighestActivityLevel": None}]
    rec["MunicipalityList"] = [{"Id": "4601", "Name": "Bergen", "CountyList": None}]
    data.append(rec)
    return data


def conflicting_records():
    data = load()
    warning_records(data)[2]["ActivityLevel"] = "3"
    return data


def missing_fields():
    data = load()
    for r in warning_records(data):
        r.pop("ValidTo", None)
    return data


def main():
    (CASES / "real_2610").mkdir(exist_ok=True)
    shutil.copyfile(FIXTURE, CASES / "real_2610" / "nve.json")   # byte copy, unchanged
    write("empty_day", set_level("1"))
    write("orange_level3", set_level("3"))
    write("red_level4", set_level("4"))
    write("multi_county", multi_county())
    write("other_county_only", other_county_only())
    write("conflicting_records", conflicting_records())
    write("missing_fields", missing_fields())
    print("Rebuilt nve.json for 8 cases in eval/cases/")


if __name__ == "__main__":
    main()
