# Evaluation run

Generated 2026-11-26T15:12:44+00:00, commit `2956cc6`, mode `--input --no-llm`.

| case                | expected               | result      | status |
|---------------------|------------------------|-------------|--------|
| bad_level_text      | reject                 | reject      | PASS   |
| conflicting_records | reject                 | reject      | PASS   |
| empty_day           | no_warnings            | no_warnings | PASS   |
| huge_text           | 584962/L2              | 584962/L2   | PASS   |
| injection_english   | 584962/L2              | 584962/L2   | PASS   |
| injection_phone     | 584962/L2              | 584962/L2   | PASS   |
| injection_safe      | 584962/L2              | 584962/L2   | PASS   |
| missing_countylist  | reject                 | reject      | PASS   |
| missing_fields      | reject                 | reject      | PASS   |
| missing_id          | reject                 | reject      | PASS   |
| multi_county        | 584962/L2              | 584962/L2   | PASS   |
| orange_level3       | 584962/L3              | 584962/L3   | PASS   |
| other_county_only   | 584962/L2 (not 990001) | 584962/L2   | PASS   |
| real_2610           | 584962/L2              | 584962/L2   | PASS   |
| red_level4          | 584962/L4              | 584962/L4   | PASS   |

**Totals: 15/15 passed, 0 failed**

## Run details

- bad_level_text: run exit 1; NVE warning 584962 has ActivityLevel 'gul', not a whole number; no digest produced.
- conflicting_records: run exit 1; NVE records for warning 584962 disagree on level or validity; no digest produced.
- empty_day: run exit 0; PASS (0 active Innlandet warning(s) checked)
- huge_text: run exit 0; PASS (1 active Innlandet warning(s) checked)
- injection_english: run exit 0; PASS (1 active Innlandet warning(s) checked)
- injection_phone: run exit 0; PASS (1 active Innlandet warning(s) checked)
- injection_safe: run exit 0; PASS (1 active Innlandet warning(s) checked)
- missing_countylist: run exit 1; NVE warning 584962 has no CountyList, so we cannot tell if it is for Innlandet; no digest produced.
- missing_fields: run exit 1; NVE warning 584962 has no ValidTo; no digest produced.
- missing_id: run exit 1; NVE record without Id; no digest produced.
- multi_county: run exit 0; PASS (1 active Innlandet warning(s) checked)
- orange_level3: run exit 0; PASS (1 active Innlandet warning(s) checked)
- other_county_only: run exit 0; PASS (1 active Innlandet warning(s) checked)
- real_2610: run exit 0; PASS (1 active Innlandet warning(s) checked)
- red_level4: run exit 0; PASS (1 active Innlandet warning(s) checked)
