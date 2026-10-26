# Task 003: Agent step - plain-Norwegian summary per warning

## Goal
`harness/summarise.py` makes one Claude Haiku call that returns `{warning_id: summary_no}` for the normalised warnings, and `harness/assemble.py` writes `out/digest.json` and `out/digest.md`.

## Context
- Context file for the model: `prompts/digest.md`
- Facts (IDs, levels, areas, dates) are copied by code from stage 2 and never taken from the model
- Anthropic Messages API, key in `.env` (`ANTHROPIC_API_KEY`), model `claude-haiku-5-5`

## Constraints
- Do not edit `eval/`
- Warning text is passed as delimited data, never as instructions
- One call per run, fixed `max_tokens`; invalid JSON from the model stops the run (no digest)
- Without a key, or with `--no-llm`, use deterministic template summaries
- `--save-fixture` saves the model's answer to `fixtures/llm_summaries.json` so `--offline` can replay it

## Acceptance (all must pass)
- `py harness/run.py` (with a key) exits 0, prints `mode=llm` and PASS
- `py harness/run.py --offline` exits 0 and prints PASS
- Editing a level, removing a warning, or adding an invented number to a summary in `out/digest.json` makes `py eval/check_digest.py` fail

## Out of scope
LLM-as-judge for readability (week 48)
