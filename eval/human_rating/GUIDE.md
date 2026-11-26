# Human rating of model summaries

The binary checks (`eval/check_digest.py`, the meaning check in `harness/assemble.py`) prove the facts, but not whether the Norwegian is good, whether a reader could misunderstand it, or whether it is useful. This rating measures that by hand.

## What you rate

`rating_kim.csv` and `rating_adne.csv` are the same 20 summaries written by `llama3.2:3b` (Ollama, temperature 0.7). They are the model's own text, before any fallback to the template. Every summary is for the same real NVE flood warning (26.10.2026, five Innlandet municipalities), sometimes with the level raised to orange or red. The `level` column is the official level the summary must match: `gult` (2), `oransje` (3) or `rødt` (4).

The ids S01-S20 are in random order. The sheet does not show which test case a summary came from or what the automatic meaning check decided, so that this does not affect your rating.

## Rules

Give each criterion **1 = yes** or **0 = no**. Never leave a cell empty, and do not use any other value. Use `comment` for anything you want to explain. It is optional, but useful for every 0.

| column | criterion | 1 when | 0 for example |
|---|---|---|---|
| `R1_norwegian` | Correct Norwegian | no wrong, invented or misspelled words | "Gull nivå", "foreventet" |
| `R2_meaning` | Correct meaning | nothing a reader could misunderstand; the colour matches the level; nothing that contradicts the warning | "Flomfare er utsatt"; colour word missing; "oransje" in a `gult` row |
| `R3_useful` | Useful | it says where the warning applies and what people should do | no area, or no advice |
| `R4_forward` | Would forward unchanged | you would send it to a municipal coordinator as it is | anything you would want to edit first |

Rate each criterion on its own. A summary can have perfect Norwegian (R1 = 1) and still get the wrong meaning (R2 = 0).

## How to rate

1. Rate alone. **Do not discuss the summaries or your ratings until both sheets are done.** The score measures how much we agree, so talking first would make it worthless.
2. Open your own sheet in Excel and fill in the four rating columns (and `comment` if you like). Do not change `id`, `level` or `summary`, and do not sort or delete rows.
3. Save as CSV in the same place, keeping the name. "CSV UTF-8 (semikolondelt)" is best. Plain "CSV (semikolondelt)" also works.
4. When both sheets are done, run `py eval/human_rating/score.py`. It writes `eval/results/<date>_human_rating.md` and `.json`: the % yes per criterion, how well we agree (% and Cohen's kappa), and the meaning check's kept/replaced decision against R4.

`summaries.json` has the answer key (case, run, meaning-check decision). Do not open it until you have finished rating.
