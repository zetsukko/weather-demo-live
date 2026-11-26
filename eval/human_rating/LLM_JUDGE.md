# Rater 2: LLM judge

Rater 2 in the human rating is a language model, not a person. Ådne did not rate. `rating_llm.csv` is the judge's sheet and `rating_kim.csv` is Kim's. `score.py` labels rater 2 "LLM judge" in the report.

## Who

Claude (Anthropic), model id `claude-opus-5-5`. It ran in a separate chat with Kim. It is not the coding agent working in this repository, and the coding agent did not take part in that chat. Everything in this section and in "Input" is Kim's account of how the judge was run. The coding agent can only check the files: `rating_llm.csv` has the same 20 ids, levels and summary texts as the blank sheet, and all 80 rating cells are 0 or 1.

## Input

- Only `GUIDE.md` and the blank sheet: `rating_adne.csv` as committed in `4d5a3f6` (20 rows, all rating cells empty).
- It did not see `rating_kim.csv` or `summaries.json`, so it did not know the case, the run, or the meaning check's decision for any summary.
- One pass, no reruns: the sheet is the judge's first and only answer, not the best of several.

## Known failure modes

- **Same model as the builder.** The coding agent that built the harness and the meaning check in `harness/assemble.py` is also Claude `claude-opus-5-5`, so the judge is not just the same model family but the same model. Where the harness and the judge share a blind spot, agreement between them proves nothing.
- **It knew the meaning-check rules.** Earlier in the same chat it had seen the meaning-check rules (colour word for the level, "utsatt", "avlyst", "ingen fare"). It may therefore weight the colour word heavily in R2 and R4 and agree with the automatic check more than an unprimed reader would. The comparison of the meaning check against R4 in the report has to be read with this in mind.
- **Not a native speaker.** Its sense of correct and natural Norwegian (R1) is not validated. It may accept phrasing a Norwegian reader finds odd, or reject phrasing that is fine.
- **Strictness is not calibrated.** Nothing sets how strict the judge is compared with a person. Measuring that is the point of this rating: the agreement with the human rater (% and Cohen's kappa per criterion in the report) is the measure of how far the judge can stand in for a person, not a given.
- **One run.** With one pass there is no measure of how stable the judge's ratings are. Another run of the same prompt could give different ratings.

## How to read the result

The judge is a second, independent rating that is easy to repeat, not a replacement for a second person. A high kappa on a criterion means the judge rates that criterion like Kim does. A low kappa means its ratings on that criterion cannot be used without a person.
