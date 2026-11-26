# Evaluation run

Generated 2026-11-26T12:04:46+00:00, commit `80215c1`, mode `--input --no-llm`.

| case                | expected               | result      | status |
|---------------------|------------------------|-------------|--------|
| conflicting_records | reject                 | reject      | PASS   |
| empty_day           | no_warnings            | no_warnings | PASS   |
| missing_fields      | reject                 | reject      | PASS   |
| multi_county        | 584962/L2              | 584962/L2   | PASS   |
| orange_level3       | 584962/L3              | 584962/L3   | PASS   |
| other_county_only   | 584962/L2 (not 990001) | 584962/L2   | PASS   |
| real_2610           | 584962/L2              | 584962/L2   | PASS   |
| red_level4          | 584962/L4              | 584962/L4   | PASS   |

**Totals: 8/8 passed, 0 failed**

## Run details

- conflicting_records: run exit 1; NVE records for warning 584962 disagree on level or validity; no digest produced.
- empty_day: run exit 0; PASS (0 active Innlandet warning(s) checked)
- missing_fields: run exit 1; NVE warning 584962 has no ValidTo; no digest produced.
- multi_county: run exit 0; PASS (1 active Innlandet warning(s) checked)
- orange_level3: run exit 0; PASS (1 active Innlandet warning(s) checked)
- other_county_only: run exit 0; PASS (1 active Innlandet warning(s) checked)
- real_2610: run exit 0; PASS (1 active Innlandet warning(s) checked)
- red_level4: run exit 0; PASS (1 active Innlandet warning(s) checked)
