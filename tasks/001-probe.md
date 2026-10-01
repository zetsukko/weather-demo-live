# Task 001: Probe one public source

## Goal
`harness/probe.py` fetches tomorrow's forecast for Hamar from MET Norway and writes `out/probe.json` with `source_url` and `items` (title, date, air_temperature).

## Context
- Forecast endpoint: https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=60.79&lon=11.07
- Terms of service: https://api.met.no/doc/TermsOfService

## Constraints
- Do not edit `eval/`
- No personal data
- Send an identifying `User-Agent` header
- Save the raw response to `fixtures/met_hamar.json`
- Support `--offline` (reads the fixture instead of hitting the network)
- Python 3 standard library only
- This is Windows: use `py` to run Python

## Acceptance (all must pass)
- `py harness/probe.py && py eval/check_probe.py` prints `PASS`
- `py harness/probe.py --offline && py eval/check_probe.py` prints `PASS`
- The check failed before this task started

## Out of scope
Summarisation, scheduling, LLM calls, caching (task 002).
