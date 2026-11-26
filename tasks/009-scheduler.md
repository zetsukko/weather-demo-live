# Task 009: Daily run with Windows Task Scheduler

## Goal
Keep the daily automatic run working after GitHub Actions was blocked for the account by a billing
lock (student plan expired, mid-November). Every scheduled Actions run failed before it started.

## Plan
- `scripts/daily_run.bat`: cd to the repo root, set `LLM_PROVIDER=ollama` unless already set,
  run `py harness/run.py`, append the output with start/end timestamps and the exit code to
  `logs/daily_run.log`. `logs/` is git-ignored.
- Register it with `schtasks` daily at 07:15 as the logged-on user (`/IT`), so Ollama is running.
- `.github/workflows/digest.yml`: remove the schedule trigger, keep `workflow_dispatch`, comment why.
- README "Automatic daily run" and SPEC.md describe the new setup and the reason.

## Constraints
- Do not edit `eval/`. No personal data or absolute user paths in tracked files.
- The script must not read or print `.env`; the harness loads it as before.

## Acceptance
- `py harness/run.py --offline` exits 0 and prints PASS
- `scripts\daily_run.bat` exits with the run's exit code and appends a timestamped block to `logs/daily_run.log`
- `schtasks /Run /TN "Varsel Innlandet daily run"` adds a new block to the log
