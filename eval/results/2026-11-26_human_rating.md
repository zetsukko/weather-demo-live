# Human rating of model summaries

Generated 2026-11-26T15:01:30+00:00. 20 summaries by `llama3.2:3b` (temperature 0.7), cases real_2610, orange_level3, red_level4, multi_county, rated by Kim and LLM judge (see `eval/human_rating/LLM_JUDGE.md`) independently (1 = yes, 0 = no; rules in `eval/human_rating/GUIDE.md`).

## Share of yes, and agreement

| criterion | Kim | LLM judge | average | agreement | Cohen's kappa |
|---|---|---|---|---|---|
| R1 correct Norwegian | 55 % | 25 % | 40 % | 50 % | 0.05 |
| R2 correct meaning | 95 % | 35 % | 65 % | 30 % | -0.10 |
| R3 useful | 100 % | 70 % | 85 % | 70 % | 0.00 |
| R4 would forward unchanged | 65 % | 5 % | 35 % | 40 % | 0.06 |

## Meaning check against R4

Only the 8 summaries where both raters gave the same R4; 12 left out (S03, S04, S05, S06, S08, S09, S11, S12, S13, S16, S17, S18).

| meaning check | both would forward (R4 = 1) | both would not (R4 = 0) |
|---|---|---|
| kept | 1 | 3 |
| replaced | 0 | 4 |

Kept and not forward: the meaning check let through a summary people would not send. Replaced and forward: it threw away a summary people would have sent.
