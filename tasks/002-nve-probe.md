# Task 002: Fetch and normalise NVE flood warnings for Innlandet

## Goal
`harness/fetch.py` and `harness/normalise.py` fetch NVE flood warnings for county 34 (Innlandet) and produce a normalised list of active warnings (level >= 2).

## Context
- API docs: https://api.nve.no/doc/flomvarsling/
- Endpoint: `https://api01.nve.no/hydrology/forecast/flood/v1.0.10/api/Warning/County/34/1` (no dates = today, tomorrow and the day after; `1` = Norwegian)
- Fields used: `Id`, `ActivityLevel`, `ValidFrom`, `ValidTo`, `CountyList`, `MunicipalityList`, `MainText`, `WarningText`, `AdviceText`

## Constraints
- Do not edit `eval/`
- No personal data; public sources only
- Identifying `User-Agent`; GET only; NLOD attribution
- Save the raw response to `out/raw_nve_flood.json`; `--save-fixture` also copies it to `fixtures/nve_flood_innlandet.json`; `--offline` replays the fixture
- Stop with a clear error on HTTP errors instead of producing a partial result
- Python 3 standard library only

## Acceptance (all must pass)
- `py harness/run.py --save-fixture` exits 0 and writes `fixtures/nve_flood_innlandet.json`
- `py harness/run.py --offline` exits 0 and prints PASS
- `eval/check_digest.py` failed before this task (no `out/raw_nve_flood.json`)

## Out of scope
LLM summaries (task 003), scheduling (task 004), landslide and MetAlerts sources (week 45)
