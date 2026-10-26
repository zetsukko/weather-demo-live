# CLAUDE.md

Varsel Innlandet: agentic harness that turns NVE flood warnings for Innlandet into a checked, plain-Norwegian daily digest. Two-person course project (KIUA-2003).

## How to run checks
- Full offline run: `py harness/run.py --offline` (must print PASS, exit 0)
- Live run: `py harness/run.py` (needs network; uses ANTHROPIC_API_KEY from .env if present)
- Check only: `py eval/check_digest.py`

## Layout
- `harness/` stages: fetch -> normalise -> summarise (LLM) -> assemble; `run.py` runs all and the check
- `eval/` checks (never edit without asking), `fixtures/` saved real inputs, `prompts/` runtime context
- `tasks/NNN-*.md` one task each with acceptance commands

## Rules
- Never edit anything inside `eval/` without asking the user first.
- Facts (IDs, levels, areas, dates) must come from stage 2 code, never from the model.
- No personal data in any tracked file; never read or print `.env` or keys.
- Python standard library only. Use `py` on Windows.
- One task = one branch = one PR; do not push unless asked.
