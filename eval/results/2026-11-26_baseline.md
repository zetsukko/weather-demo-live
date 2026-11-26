# Evaluation run

Generated 2026-11-26T12:00:13+00:00, commit `1f05a8e`, mode `--input --no-llm`.

| case                | expected               | result      | status |
|---------------------|------------------------|-------------|--------|
| conflicting_records | reject                 | reject      | PASS   |
| empty_day           | no_warnings            | no_warnings | PASS   |
| missing_fields      | reject                 | 584962/L2   | FAIL   |
| multi_county        | 584962/L2              | 584962/L2   | PASS   |
| orange_level3       | 584962/L3              | 584962/L3   | PASS   |
| other_county_only   | 584962/L2 (not 990001) | 584962/L2   | PASS   |
| real_2610           | 584962/L2              | 584962/L2   | PASS   |
| red_level4          | 584962/L4              | 584962/L4   | PASS   |

**Totals: 7/8 passed, 1 failed**

## Why cases failed

- missing_fields: expected the run to stop without a digest, but it exited 0 and produced one (584962/L2); check said: PASS (1 active Innlandet warning(s) checked)

## Run details

- conflicting_records: run exit 1; NVE records for warning 584962 disagree on level or validity; no digest produced.
- empty_day: run exit 0; PASS (0 active Innlandet warning(s) checked)
- missing_fields: run exit 0; PASS (1 active Innlandet warning(s) checked)
- multi_county: run exit 0; PASS (1 active Innlandet warning(s) checked)
- orange_level3: run exit 0; PASS (1 active Innlandet warning(s) checked)
- other_county_only: run exit 0; PASS (1 active Innlandet warning(s) checked)
- real_2610: run exit 0; PASS (1 active Innlandet warning(s) checked)
- red_level4: run exit 0; PASS (1 active Innlandet warning(s) checked)
