# Task 005: Evaluation harness

## Goal
A fixed test set of saved NVE responses (typical, boundary and must-reject cases) that runs on demand with one command and reports PASS/FAIL per case, for regression.

## Context
- `harness/run.py --input <file>` runs the pipeline on any saved NVE response
- `eval/cases/<case>/nve.json` + `expected.json`; derived cases are built from `fixtures/nve_flood_innlandet.json` (26.10) by `eval/cases/build_cases.py`
- `eval/run_eval.py` writes `eval/results/latest.md` and `latest.json`

## Constraints
- Do not edit `eval/check_digest.py` or `eval/check_probe.py`
- Cases run with `--no-llm` (deterministic, no network)
- Results files contain no personal data or absolute paths

## Acceptance
- `py harness/run.py --offline` exits 0 and prints PASS
- `py eval/run_eval.py` prints the table and totals and writes both results files
- All 8 cases PASS (currently 7/8: `missing_fields` is accepted by the harness; fix is a follow-up)

## Out of scope
Fixing the harness for `missing_fields`, LLM-mode evaluation, LLM-as-judge readability scoring
