# Evaluation run

Generated 2026-11-26T12:21:28+00:00, commit `040ede4`, mode `--input --no-llm`.

| case                | expected               | result      | status |
|---------------------|------------------------|-------------|--------|
| bad_level_text      | reject                 | crash       | FAIL   |
| conflicting_records | reject                 | reject      | PASS   |
| empty_day           | no_warnings            | no_warnings | PASS   |
| huge_text           | 584962/L2              | 584962/L2   | PASS   |
| injection_english   | 584962/L2              | 584962/L2   | PASS   |
| injection_phone     | 584962/L2              | 584962/L2   | PASS   |
| injection_safe      | 584962/L2              | 584962/L2   | PASS   |
| missing_countylist  | reject                 | no_warnings | FAIL   |
| missing_fields      | reject                 | reject      | PASS   |
| missing_id          | reject                 | crash       | FAIL   |
| multi_county        | 584962/L2              | 584962/L2   | PASS   |
| orange_level3       | 584962/L3              | 584962/L3   | PASS   |
| other_county_only   | 584962/L2 (not 990001) | 584962/L2   | PASS   |
| real_2610           | 584962/L2              | 584962/L2   | PASS   |
| red_level4          | 584962/L4              | 584962/L4   | PASS   |

**Totals: 12/15 passed, 3 failed**

## Why cases failed

- bad_level_text: crash, not a controlled stop: ValueError: invalid literal for int() with base 10: 'gul'
- missing_countylist: expected the run to stop without a digest, but it exited 0 and produced one (no_warnings); check said: PASS (0 active Innlandet warning(s) checked)
- missing_id: crash, not a controlled stop: KeyError: 'Id'

## Run details

- bad_level_text: run exit 1; ValueError: invalid literal for int() with base 10: 'gul'
- conflicting_records: run exit 1; NVE records for warning 584962 disagree on level or validity; no digest produced.
- empty_day: run exit 0; PASS (0 active Innlandet warning(s) checked)
- huge_text: run exit 0; PASS (1 active Innlandet warning(s) checked)
- injection_english: run exit 0; PASS (1 active Innlandet warning(s) checked)
- injection_phone: run exit 0; PASS (1 active Innlandet warning(s) checked)
- injection_safe: run exit 0; PASS (1 active Innlandet warning(s) checked)
- missing_countylist: run exit 0; PASS (0 active Innlandet warning(s) checked)
- missing_fields: run exit 1; NVE warning 584962 has no ValidTo; no digest produced.
- missing_id: run exit 1; KeyError: 'Id'
- multi_county: run exit 0; PASS (1 active Innlandet warning(s) checked)
- orange_level3: run exit 0; PASS (1 active Innlandet warning(s) checked)
- other_county_only: run exit 0; PASS (1 active Innlandet warning(s) checked)
- real_2610: run exit 0; PASS (1 active Innlandet warning(s) checked)
- red_level4: run exit 0; PASS (1 active Innlandet warning(s) checked)
