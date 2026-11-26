# Task 011: Human rating of model summaries

## Goal
Measure the language quality the binary checks do not measure: two people rate 20 model summaries
on four yes/no criteria, and we compare their verdict with the automatic meaning check.

## Plan
- `eval/human_rating/collect.py`: same approach as `eval/run_stress.py` (`run.py --input`, Ollama
  llama3.2:3b, temperature 0.7), 5 runs each on real_2610, orange_level3, red_level4, multi_county.
  Saves the raw model text (before fallback), case, run, level and the meaning-check decision and
  reason to `summaries.json`, with ids S01-S20 in shuffled order.
- `rating_kim.csv` (Kim), `rating_llm.csv` (rater 2, an LLM judge; see `LLM_JUDGE.md`): identical blank sheets (semicolon, UTF-8 with BOM) with only
  id, level, summary and the rating columns. No case name, no meaning-check decision.
- `GUIDE.md`: rules R1-R4 (1 = yes, 0 = no); rate alone, no discussion until both sheets are done.
- `score.py`: % yes per criterion per rater and on average, agreement (% and Cohen's kappa), and
  meaning check (kept/replaced) against R4 where both raters agree. Writes
  `eval/results/<date>_human_rating.md` and `.json`.

## Constraints
- No existing checker is changed. Standard library only.

## Acceptance
- `summaries.json` has 20 records; both sheets are identical and blank
- `py eval/human_rating/score.py` exits 1 with "Cannot score yet" while a sheet is blank,
  and writes both result files once both sheets are filled
- `py eval/run_eval.py` still 15/15
