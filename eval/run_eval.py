"""Evaluation run: replay every saved case through the harness and compare with expected.json.

  py eval/run_eval.py

For each eval/cases/<case>/ it runs
  harness/run.py --input eval/cases/<case>/nve.json --no-llm
then eval/check_digest.py, and compares the outcome with expected.json:
  "warnings"     run exits 0, check passes, digest has exactly these (warning_id, danger_level),
                 and none of "absent_ids"
  "no_warnings"  run exits 0, check passes, empty warning list with a no-warnings message
  "reject"       run exits non-zero, no out/digest.md is left, and the run stopped itself with a
                 clean "...; no digest produced." message. A Python traceback is a crash, not a
                 controlled stop, and counts as FAIL.

Prints a table plus totals and writes eval/results/latest.md and latest.json.
Exit 0 if every case passes, 1 otherwise. Cases run one after another (they share out/).
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "eval" / "cases"
RESULTS = ROOT / "eval" / "results"
OUT = ROOT / "out"
RUN = ROOT / "harness" / "run.py"
CHECK = ROOT / "eval" / "check_digest.py"


def run(args):
    p = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr).strip()


def last_line(text):
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[-1] if lines else ""


def stop_message(text):
    """The line that explains why the run stopped (sys.exit message or check FAIL)."""
    for line in text.splitlines():
        if "no digest produced" in line or line.startswith("FAIL") or "KILL SWITCH" in line:
            return line.strip()
    return last_line(text)


def crashed(text):
    return "Traceback (most recent call last)" in text


def fmt_expected(exp):
    if exp["expect"] == "warnings":
        s = ", ".join(f"{w['warning_id']}/L{w['danger_level']}" for w in exp["warnings"])
        if exp.get("absent_ids"):
            s += " (not " + ", ".join(exp["absent_ids"]) + ")"
        return s
    return exp["expect"]


def evaluate(case_dir):
    exp = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
    rel_input = (case_dir / "nve.json").relative_to(ROOT).as_posix()
    code, output = run([RUN, "--input", rel_input, "--no-llm"])
    digest_md = (OUT / "digest.md").exists()
    rec = {"case": case_dir.name, "expected": fmt_expected(exp), "expect": exp["expect"],
           "run_exit": code, "digest_md": digest_md, "check": None}

    if code != 0 or not digest_md:
        rec["result"] = "crash" if crashed(output) else "reject"
        rec["controlled_stop"] = code != 0 and not crashed(output) and "no digest produced" in output
        rec["detail"] = stop_message(output)
    else:
        ccode, cout = run([CHECK])
        rec["check"] = last_line(cout)
        digest = json.loads((OUT / "digest.json").read_text(encoding="utf-8"))
        got = sorted((str(w["warning_id"]), int(w["danger_level"])) for w in digest.get("warnings") or [])
        rec["got"] = [{"warning_id": i, "danger_level": l} for i, l in got]
        if ccode != 0:
            rec["result"] = "check failed"
        elif not got and digest.get("no_warnings_message"):
            rec["result"] = "no_warnings"
        else:
            rec["result"] = ", ".join(f"{i}/L{l}" for i, l in got) or "empty (no message)"
        rec["detail"] = rec["check"]

    # Compare with expected.json
    why = None
    if exp["expect"] == "reject":
        if rec["result"] == "crash":
            why = f"crash, not a controlled stop: {rec['detail']}"
        elif rec["result"] != "reject":
            why = f"expected the run to stop without a digest, but it exited 0 and produced one ({rec['result']}); check said: {rec['check']}"
        elif not rec["controlled_stop"]:
            why = f"run stopped without a clean 'no digest produced' message: {rec['detail']}"
    elif rec["result"] == "crash":
        why = f"crash, not a controlled stop: {rec['detail']}"
    elif rec["result"] == "reject":
        why = f"run stopped without a digest: {rec['detail']}"
    elif rec["check"] is None or not rec["check"].startswith("PASS"):
        why = f"check did not pass: {rec['check']}"
    elif exp["expect"] == "no_warnings":
        if rec["result"] != "no_warnings":
            why = f"expected no warnings, got {rec['result']}"
    else:
        want = sorted((str(w["warning_id"]), int(w["danger_level"])) for w in exp["warnings"])
        got_pairs = [(w["warning_id"], w["danger_level"]) for w in rec["got"]]
        present = [i for i in exp.get("absent_ids", []) if i in {g[0] for g in got_pairs}]
        if got_pairs != want:
            why = f"expected {want}, got {got_pairs}"
        elif present:
            why = f"warning(s) {present} must not appear but did"
    rec["status"] = "FAIL" if why else "PASS"
    rec["why"] = why
    return rec


def table(rows):
    head = ("case", "expected", "result", "status")
    data = [(r["case"], r["expected"], r["result"], r["status"]) for r in rows]
    widths = [max(len(str(x)) for x in col) for col in zip(head, *data)]
    line = lambda cells: "| " + " | ".join(str(c).ljust(w) for c, w in zip(cells, widths)) + " |"
    sep = "|" + "|".join("-" * (w + 2) for w in widths) + "|"
    return "\n".join([line(head), sep] + [line(d) for d in data])


def git_commit():
    try:
        p = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
        return p.stdout.strip() or None
    except OSError:
        return None


def main():
    case_dirs = sorted(d for d in CASES.iterdir() if (d / "expected.json").exists())
    rows = [evaluate(d) for d in case_dirs]
    passed = sum(r["status"] == "PASS" for r in rows)
    totals = f"Totals: {passed}/{len(rows)} passed, {len(rows) - passed} failed"
    failures = [f"- {r['case']}: {r['why']}" for r in rows if r["why"]]

    tbl = table(rows)
    print(tbl)
    print()
    print(totals)
    if failures:
        print("\nWhy cases failed:")
        print("\n".join(failures))

    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    commit = git_commit()
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "latest.json").write_text(json.dumps({
        "generated_at": stamp, "git_commit": commit, "mode": "--input --no-llm", "reject_rule": "strict (controlled stop only)",
        "passed": passed, "total": len(rows), "cases": rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = [f"# Evaluation run", "", f"Generated {stamp}, commit `{commit}`, mode `--input --no-llm`.", "",
          tbl, "", f"**{totals}**", ""]
    if failures:
        md += ["## Why cases failed", ""] + failures + [""]
    md += ["## Run details", ""] + [f"- {r['case']}: run exit {r['run_exit']}; {r['detail']}" for r in rows] + [""]
    (RESULTS / "latest.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nWrote eval/results/latest.md and latest.json")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
