# Task 007: Context cap and stress test 2, dependency failure

## Goal
A. Stop the context-window failure from stress test 1 (`huge_text`: 0/5, prompt silently cut to 2050 tokens).
B. Find out how the harness behaves when NVE or Ollama fails, and record it BEFORE fixing anything (red first).

## Plan
Part A
- Stage 3 caps main_text, warning_text and advice_text at 1500 characters each before they go to the model,
  cut at a sentence end and marked "[forkortet]"; it prints a line when it cuts. Ollama gets `num_ctx: 4096`.
- `py eval/run_stress.py --runs 5 --temperature 0.7 --cases huge_text --tag after_ctx`

Part B
- NVE base URL can be overridden with `NVE_FLOOD_BASE` (default unchanged); `OLLAMA_HOST` already exists.
- `eval/run_deps.py` runs `harness/run.py` (live mode) against a local test server or a bad address for:
  NVE unreachable, NVE HTTP 503, NVE HTTP 404, NVE hangs, NVE returns HTML, Ollama not running, Ollama hangs.
  It records exit code, stop message, whether a digest was produced, files left in out/, and time taken.
- Results in `eval/results/<date>_stress2_before.md/.json`. No fixes in Part B yet.

## Constraints
- Do not edit `eval/check_digest.py`. No real NVE or LLM calls in run_deps.py (local server only).

## Acceptance
- `py harness/run.py --offline` and `py eval/run_eval.py` still pass (15/15)
- huge_text with the model: results saved as stress1_after_ctx
- `py eval/run_deps.py` prints the table and writes both stress2_before files
