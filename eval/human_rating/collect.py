"""Collect model summaries for the human rating (task 011).

  py eval/human_rating/collect.py [--runs N] [--temperature T] [--cases a,b,...]

Same approach as eval/run_stress.py: runs
  harness/run.py --input eval/cases/<case>/nve.json   (LLM_PROVIDER=ollama, OLLAMA_TEMPERATURE=T)
N times per case (default 5, temperature 0.7, cases real_2610, orange_level3, red_level4,
multi_county) and keeps one record per warning: the raw text the model wrote
(out/summaries.json, before any fallback), case, run, warning id, danger level, and whether the
meaning check in harness/assemble.py kept it or replaced it (with the reason from digest.json).

The records get rating ids S01.. in a shuffled order, so the sheets do not group by case.
Writes eval/human_rating/summaries.json and two identical blank sheets, rating_kim.csv and
rating_adne.csv (semicolon-separated, UTF-8 with BOM for Norwegian Excel). The sheets show only
id, level, summary and empty rating columns: no case name and no meaning-check decision.
Refuses to overwrite a sheet that already has ratings in it.
Needs a running Ollama with the model from OLLAMA_MODEL (default llama3.2:3b).
"""
import csv
import json
import os
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
CASES = ROOT / "eval" / "cases"
OUT = ROOT / "out"
RUN = ROOT / "harness" / "run.py"
SUMMARIES = HERE / "summaries.json"
SHEETS = [HERE / "rating_kim.csv", HERE / "rating_adne.csv"]
COLUMNS = ["id", "level", "summary", "R1_norwegian", "R2_meaning", "R3_useful", "R4_forward", "comment"]
RATINGS = COLUMNS[3:]
LEVEL_NAMES = {2: "gult", 3: "oransje", 4: "rødt"}   # same as harness/normalise.py
DEFAULT_CASES = "real_2610,orange_level3,red_level4,multi_county"


def arg(argv, name, default):
    if name in argv and argv.index(name) + 1 < len(argv):
        return argv[argv.index(name) + 1]
    return default


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def sheet_has_ratings(path):
    if not path.exists():
        return False
    with path.open(encoding="utf-8-sig", newline="") as f:
        return any(any((row.get(c) or "").strip() for c in RATINGS) for row in csv.DictReader(f, delimiter=";"))


def one_run(case, n, env):
    rel = (CASES / case / "nve.json").relative_to(ROOT).as_posix()
    p = subprocess.run([sys.executable, str(RUN), "--input", rel], cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=env)
    stage3 = read_json(OUT / "summaries.json") or {}
    digest = read_json(OUT / "digest.json") or {}
    replaced = {f["warning_id"]: f["reason"] for f in digest.get("fallback") or []}
    records = []
    for w in digest.get("warnings") or []:
        wid = w["warning_id"]
        raw = (stage3.get("summaries") or {}).get(wid) if stage3.get("mode") == "llm" else None
        records.append({
            "case": case, "run": n, "warning_id": wid, "danger_level": w["danger_level"],
            "level": LEVEL_NAMES.get(w["danger_level"], str(w["danger_level"])),
            "summary": raw,
            "meaning_check": "replaced" if wid in replaced else "kept",
            "meaning_check_reason": replaced.get(wid),
            "summary_in_digest": w.get("summary_no"),
            "run_exit": p.returncode,
        })
    if not records:
        lines = [l for l in (p.stdout + p.stderr).splitlines() if l.strip()]
        print(f"    no digest (exit {p.returncode}): {lines[-1] if lines else ''}")
    return records


def main(argv):
    runs = int(arg(argv, "--runs", 5))
    temperature = float(arg(argv, "--temperature", 0.7))
    cases = [c.strip() for c in arg(argv, "--cases", DEFAULT_CASES).split(",") if c.strip()]
    for s in SHEETS:
        if sheet_has_ratings(s):
            sys.exit(f"{s.name} already has ratings; refusing to overwrite it.")
    env = dict(os.environ, LLM_PROVIDER="ollama", OLLAMA_TEMPERATURE=str(temperature))
    model = env.get("OLLAMA_MODEL", "llama3.2:3b")

    records = []
    for case in cases:
        for n in range(1, runs + 1):
            got = one_run(case, n, env)
            for r in got:
                print(f"{case} run {n}: {r['meaning_check']}"
                      f"{' (' + r['meaning_check_reason'] + ')' if r['meaning_check_reason'] else ''}: {r['summary']!r}")
            records += got

    usable = [r for r in records if r["summary"]]
    if len(usable) < len(records):
        print(f"{len(records) - len(usable)} record(s) have no model text (model unavailable) and are left out.")
    seed = random.SystemRandom().randrange(2**32)
    order = list(range(len(usable)))
    random.Random(seed).shuffle(order)
    for i, idx in enumerate(order, 1):
        usable[idx]["id"] = f"S{i:02d}"
    usable.sort(key=lambda r: r["id"])

    SUMMARIES.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider": "ollama", "model": model, "temperature": temperature, "runs_per_case": runs,
        "cases": cases, "shuffle_seed": seed, "total": len(usable),
        "summaries": [{"id": r.pop("id"), **r} for r in usable],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for s in SHEETS:
        # utf-8-sig writes the BOM, so Excel opens the file as UTF-8 and shows æøå correctly.
        with s.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";", lineterminator="\r\n")
            w.writerow(COLUMNS)
            for r in json.loads(SUMMARIES.read_text(encoding="utf-8"))["summaries"]:
                w.writerow([r["id"], r["level"], r["summary"], "", "", "", "", ""])
    kept = sum(r["meaning_check"] == "kept" for r in usable)
    print(f"\n{len(usable)} summaries: {kept} kept, {len(usable) - kept} replaced by the meaning check.")
    print(f"Wrote {SUMMARIES.relative_to(ROOT).as_posix()}, " + ", ".join(s.name for s in SHEETS))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
