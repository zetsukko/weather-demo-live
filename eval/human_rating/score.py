"""Score the human rating (task 011).

  py eval/human_rating/score.py [--dir DIR] [--out DIR]

Reads rating_kim.csv (Kim), rating_llm.csv (rater 2, an LLM judge; see LLM_JUDGE.md) and summaries.json (from --dir, default this folder)
and writes <out>/<today>_human_rating.md and .json (default eval/results/) with:
  - % yes per criterion (R1-R4) per rater and on average
  - agreement between the raters per criterion: % and Cohen's kappa
  - the meaning check's decision (kept/replaced) against R4, for the summaries where both
    raters gave the same R4
Accepts the sheets as written by collect.py or as saved by Excel (UTF-8 with or without BOM,
or Windows-1252; semicolon or comma). Exit 0 when the report is written, 1 when a sheet is
missing, incomplete or has a value other than 0/1 (nothing is written then).
"""
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
RATERS = {"kim": "rating_kim.csv", "llm": "rating_llm.csv"}
LABELS = {"kim": "Kim", "llm": "LLM judge"}   # how each rater is named in the report
CRITERIA = {"R1_norwegian": "R1 correct Norwegian", "R2_meaning": "R2 correct meaning",
            "R3_useful": "R3 useful", "R4_forward": "R4 would forward unchanged"}


def arg(argv, name, default):
    if name in argv and argv.index(name) + 1 < len(argv):
        return argv[argv.index(name) + 1]
    return default


def read_sheet(path):
    data = path.read_bytes()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("cp1252")
    first = text.splitlines()[0] if text else ""
    delimiter = ";" if first.count(";") >= first.count(",") else ","
    rows = list(csv.DictReader(text.splitlines(), delimiter=delimiter))
    return {(r.get("id") or "").strip(): r for r in rows if (r.get("id") or "").strip()}


def load(sheet_dir, ids):
    """{rater: {id: {criterion: 0/1}}}, plus a list of problems."""
    ratings, problems = {}, []
    for rater, name in RATERS.items():
        path = sheet_dir / name
        if not path.exists():
            problems.append(f"{name}: missing")
            continue
        rows = read_sheet(path)
        missing_cols = [c for c in CRITERIA if rows and c not in next(iter(rows.values()))]
        if missing_cols:
            problems.append(f"{name}: missing column(s) {', '.join(missing_cols)}")
            continue
        ratings[rater] = {}
        for sid in ids:
            row = rows.get(sid)
            if row is None:
                problems.append(f"{name}: row {sid} missing")
                continue
            ratings[rater][sid] = {}
            for c in CRITERIA:
                value = (row.get(c) or "").strip()
                if value not in ("0", "1"):
                    problems.append(f"{name}: {sid} {c} is {value!r}, must be 0 or 1")
                else:
                    ratings[rater][sid][c] = int(value)
        extra = sorted(set(rows) - set(ids))
        if extra:
            problems.append(f"{name}: unknown id(s) {', '.join(extra)}")
    return ratings, problems


def kappa(a, b):
    """Cohen's kappa for two lists of 0/1, or None when chance agreement is 1 (undefined)."""
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else (po - pe) / (1 - pe)


def pct(x):
    return f"{100 * x:.0f} %"


def main(argv):
    sheet_dir = Path(arg(argv, "--dir", HERE)).resolve()
    out_dir = Path(arg(argv, "--out", ROOT / "eval" / "results")).resolve()
    key = json.loads((sheet_dir / "summaries.json").read_text(encoding="utf-8"))
    summaries = {s["id"]: s for s in key["summaries"]}
    ids = sorted(summaries)
    ratings, problems = load(sheet_dir, ids)
    if problems:
        print("Cannot score yet:")
        for p in problems[:40]:
            print(f"  {p}")
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more")
        return 1

    n = len(ids)
    a, b = (ratings[r] for r in RATERS)
    per_criterion = {}
    for c in CRITERIA:
        va, vb = [a[i][c] for i in ids], [b[i][c] for i in ids]
        yes = {r: sum(ratings[r][i][c] for i in ids) / n for r in RATERS}
        per_criterion[c] = {
            "yes": yes, "yes_average": sum(yes.values()) / len(yes),
            "agreement": sum(x == y for x, y in zip(va, vb)) / n,
            "kappa": kappa(va, vb),
        }

    # Meaning check (kept/replaced) against R4 where both raters agree.
    table = {d: {"forward": 0, "not_forward": 0} for d in ("kept", "replaced")}
    disagree = []
    for i in ids:
        if a[i]["R4_forward"] != b[i]["R4_forward"]:
            disagree.append(i)
            continue
        col = "forward" if a[i]["R4_forward"] else "not_forward"
        table[summaries[i]["meaning_check"]][col] += 1

    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    today = datetime.now().date().isoformat()
    result = {
        "generated_at": stamp, "n": n, "raters": list(RATERS), "rater_labels": LABELS,
        "model": key.get("model"), "temperature": key.get("temperature"), "cases": key.get("cases"),
        "criteria": per_criterion,
        "meaning_check_vs_r4": table, "r4_disagreements": disagree,
        "ratings": {r: ratings[r] for r in RATERS},
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{today}_human_rating.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    r1, r2 = (LABELS[r] for r in RATERS)
    k1, k2 = RATERS
    md = ["# Human rating of model summaries", "",
          f"Generated {stamp}. {n} summaries by `{key.get('model')}` (temperature {key.get('temperature')}), "
          f"cases {', '.join(key.get('cases') or [])}, rated by {r1} and {r2} (see `eval/human_rating/LLM_JUDGE.md`) independently "
          "(1 = yes, 0 = no; rules in `eval/human_rating/GUIDE.md`).", "",
          "## Share of yes, and agreement", "",
          f"| criterion | {r1} | {r2} | average | agreement | Cohen's kappa |",
          "|---|---|---|---|---|---|"]
    for c, label in CRITERIA.items():
        s = per_criterion[c]
        k = "n/a (same value everywhere)" if s["kappa"] is None else f"{s['kappa']:.2f}"
        md.append(f"| {label} | {pct(s['yes'][k1])} | {pct(s['yes'][k2])} | {pct(s['yes_average'])} | "
                  f"{pct(s['agreement'])} | {k} |")
    agreed = n - len(disagree)
    md += ["", "## Meaning check against R4", "",
           f"Only the {agreed} summaries where both raters gave the same R4; "
           f"{len(disagree)} left out ({', '.join(disagree) or 'none'}).", "",
           "| meaning check | both would forward (R4 = 1) | both would not (R4 = 0) |",
           "|---|---|---|"]
    for d in ("kept", "replaced"):
        md.append(f"| {d} | {table[d]['forward']} | {table[d]['not_forward']} |")
    md += ["", "Kept and not forward: the meaning check let through a summary people would not send. "
           "Replaced and forward: it threw away a summary people would have sent.", ""]
    (out_dir / f"{today}_human_rating.md").write_text("\n".join(md), encoding="utf-8")
    rel = out_dir.relative_to(ROOT).as_posix() if out_dir.is_relative_to(ROOT) else str(out_dir)
    print("\n".join(md))
    print(f"Wrote {rel}/{today}_human_rating.md and .json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
