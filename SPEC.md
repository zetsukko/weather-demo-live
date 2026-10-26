# Project Specification: Natural hazard warnings digest for Innlandet

> Approved by the lecturer (October 2026). Walking skeleton (Compulsory 2): NVE flood warnings only; NVE landslide warnings and MET MetAlerts are added in week 45.

Based on candidate 1 in `docs/problem-candidates.md`.

## Problem

Today someone has to check varsom.no (NVE flood and landslide warnings) and MET's farevarsler (weather warnings) by hand, then copy the active warnings for Innlandet into an email or briefing note. This spec replaces that recurring weekly task.

It matters because the warnings come from two agencies in different formats and change during the week. Missing an update or cancellation, or copying the wrong danger level, leads to poor preparedness decisions. The agent step collates the warnings and phrases the digest in plain Norwegian. Deterministic checks make sure no warning is dropped, duplicated or invented.

## Users

- Municipal emergency coordinators (beredskapskoordinatorer) in Innlandet's municipalities.
- Volunteer groups in Innlandet, such as the Red Cross, Norwegian People's Aid and local search-and-rescue teams.

Users are described by role only; no names or contact details are stored.

## Sources

| Source | Docs | Licence / terms | Innlandet filter |
|---|---|---|---|
| NVE flood warnings | https://api.nve.no/doc/flomvarsling/ | NLOD 2.0 (see below) | `/api/Warning/County/34/1` (task 002) |
| NVE landslide warnings | https://api.nve.no/doc/jordskredvarsling/ | NLOD 2.0 (see below) | County-level endpoint, to be confirmed in a probe task |
| MET Norway MetAlerts 2.0 | https://api.met.no/weatherapi/metalerts/2.0/documentation | NLOD 2.0 and CC BY 4.0 (see below) | `county=34&geographicDomain=land` |

**NVE terms:** NVE's API data is licensed under NLOD 2.0 (https://data.norge.no/nlod/no/2.0), per https://api.nve.no/doc/.
- Credit NVE ("Contains data under NLOD provided by NVE") and link to the service used.
- Mark our changes as ours.
- The data is provided "as is", with no guarantee of accuracy.

**MET terms** (https://api.met.no/doc/TermsOfService):
- The data is licensed under NLOD 2.0 and CC BY 4.0 (https://api.met.no/doc/License). Credit MET Norway, link to the source and indicate any changes.
- Send an identifying `User-Agent` with a project contact (no personal email).
- Cache responses: respect `Expires` and use `If-Modified-Since`.
- Expect HTTP 429 if throttled.

**MetAlerts format:** MetAlerts are CAP messages, delivered as an RSS feed by default. Each alert is identified by its CAP id. Awareness levels are yellow, orange and red, and `msgType` is Alert, Update or Cancel.

Raw responses are saved to `fixtures/` so the pipeline and checks can run with `--offline`, following the pattern from task 001.

## Output

`out/digest.json`:

- `generated_at`: when the digest was produced.
- `sources[]`: one entry per source, with its URL and attribution string.
- `warnings[]`: one entry per warning, with these fields:
  - `source`: `nve-flood`, `nve-landslide` or `met-metalerts`
  - `warning_id`: the ID used by the source
  - `type`: `flood`, `landslide` or `weather`
  - `danger_level`: the level as given by the source
  - `area`: the area name as given by the source
  - `valid_from`, `valid_to`
  - `summary_no`: a plain-Norwegian summary written by the agent

## Definition of success

A run succeeds if and only if `py eval/check_digest.py` exits 0. It compares `out/digest.json` with the raw source response the same run used (`out/raw_nve_flood.json`):

1. **Completeness:** every active Innlandet warning in the source (level >= 2, county 34) appears in the digest exactly once, by source ID.
2. **No invention:** every `warning_id` in the digest exists in the source.
3. **Fidelity:** `danger_level`, `valid_from` and `valid_to` equal the source values.
4. **Locality:** every warning in the digest lists county 34.
5. **Grounded summaries:** every number (including dates and times) in a `summary_no` occurs in the source record, each summary is non-empty and at most 60 words.
6. **Attribution and privacy:** NVE/varsom.no attribution is present; no e-mail addresses or phone numbers.
7. **Empty case:** if the source has no active warning, the digest says so and lists none.

Readability and usefulness are not binary; they will be judged later with a documented LLM-as-judge rubric.

## Out of scope

- Personal data of any kind, including contact lists of coordinators or volunteers.
- Sending messages automatically (email, SMS, push). A human reads the digest and decides what to send.
- Making our own risk assessments or reinterpreting official danger levels.
- Areas outside Innlandet.
- Hosting a website or sending notifications. The daily run is scheduled with GitHub Actions; its output is an artifact a person reads.

## Open questions for the lecturer

- Is a weekly digest frequent enough, given that warnings can change daily?
- How should updated or cancelled MetAlerts (`msgType` Update or Cancel) count towards "exactly once"?
- May we use NVE's own area names, or must areas be mapped to municipalities?
