"""Stress test 1: prompt injection against the real model.

  py eval/run_stress.py [--runs N] [--tag NAME]

Runs every eval/cases/injection_*/ case N times (default 3) with the LLM on:
  harness/run.py --input eval/cases/<case>/nve.json        (LLM_PROVIDER=ollama)
then eval/check_digest.py and eval/check_injection.py on the digest it wrote, and records
case, run, both check results and the exact summary the model wrote.

Writes eval/results/<date>_stress1_<tag>.md and .json (tag defaults to "before").
Needs a running Ollama with the model from OLLAMA_MODEL (default llama3.2:3b).
Exit 0 if every run passes both checks, 1 otherwise.
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "eval" / "cases"
RESULTS = ROOT / "eval" / "results"
OUT = ROOT / "out"
RUN = ROOT / "harness" / "run.py"
CHECKS = {"check_digest": ROOT / "eval" / "check_digest.py",
          "check_injection": ROOT / "eval" / "check_injection.py"}


def arg(argv, name, default):
    if name in argv and argv.index(name) + 1 < len(argv):
        return argv[argv.index(name) + 1]
    return default


def run(args, env=None):
    p = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=env)
    return p.returncode, (p.stdout + p.stderr).strip()


def last_line(text):
    lines = [l for l in text.splitlines() if l.strip()]
    return lines[-1] if lines else ""


def stop_message(text):
    for line in text.splitlines():
        if "no digest produced" in line or line.startswith("FAIL") or "KILL SWITCH" in line:
            return line.strip()
    return last_line(text)


def one_run(case_dir, n, env):
    rel = (case_dir / "nve.json").relative_to(ROOT).as_posix()
    t0 = time.monotonic()
    code, output = run([RUN, "--input", rel], env)
    rec = {"case": case_dir.name, "run": n, "run_exit": code,
           "seconds": round(time.monotonic() - t0, 1)}
    digest_file = OUT / "digest.json"
    if not digest_file.exists():
        # The run stopped before stage 4: nothing for the checks to look at.
        rec.update(check_digest="n/a (no digest)", check_injection="n/a (no digest)",
                   summary=None, mode=None, detail=stop_message(output))
    else:
        digest = json.loads(digest_file.read_text(encoding="utf-8"))
        rec["mode"] = digest.get("summary_mode")
        rec["summary"] = " | ".join(w.get("summary_no") or "" for w in digest.get("warnings") or [])
        for name, path in CHECKS.items():
            rec[name] = last_line(run([path])[1])
        rec["detail"] = stop_message(output) if code else "run exit 0"
    rec["status"] = "PASS" if all(str(rec[c]).startswith("PASS") for c in CHECKS) else "FAIL"
    return rec


def cell(text):
    return "" if text is None else str(text).replace("|", "\\|").replace("\n", " ")


def git_commit():
    p = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return p.stdout.strip() or None


def main(argv):
    runs = int(arg(argv, "--runs", 3))
    tag = arg(argv, "--tag", "before")
    env = dict(os.environ, LLM_PROVIDER="ollama")
    model = env.get("OLLAMA_MODEL", "llama3.2:3b")
    case_dirs = sorted(d for d in CASES.glob("injection_*") if (d / "nve.json").exists())

    rows = []
    for d in case_dirs:
        for n in range(1, runs + 1):
            rec = one_run(d, n, env)
            rows.append(rec)
            print(f"{rec['case']} run {n}: {rec['status']} ({rec['seconds']}s) "
                  f"digest={rec['check_digest']} | injection={rec['check_injection']}")
            print(f"    summary: {rec['summary']!r}" if rec["summary"] is not None else f"    {rec['detail']}")

    passed = sum(r["status"] == "PASS" for r in rows)
    totals = f"Totals: {passed}/{len(rows)} runs passed both checks, {len(rows) - passed} failed"
    print("\n" + totals)

    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    commit = git_commit()
    name = f"{stamp[:10]}_stress1_{tag}"
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{name}.json").write_text(json.dumps({
        "generated_at": stamp, "git_commit": commit, "mode": "--input (LLM on)",
        "provider": "ollama", "model": model, "runs_per_case": runs,
        "passed": passed, "total": len(rows), "runs": rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = [f"# Stress test 1: prompt injection ({tag})", "",
          f"Generated {stamp}, commit `{commit}`, model `ollama/{model}`, {runs} run(s) per case, "
          "mode `--input` with the LLM on.", "",
          "| case | run | check_digest | check_injection | summary |",
          "|------|-----|--------------|-----------------|---------|"]
    md += [f"| {r['case']} | {r['run']} | {cell(r['check_digest'])} | {cell(r['check_injection'])} | "
           f"{cell(r['summary'] if r['summary'] is not None else '(no digest) ' + r['detail'])} |" for r in rows]
    md += ["", f"**{totals}**", ""]
    (RESULTS / f"{name}.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote eval/results/{name}.md and .json")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
