# Project Specification: Natural hazard warnings digest for Innlandet

> **DRAFT – pending discussion with lecturer**

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
| NVE flood warnings | https://api.nve.no/doc/flomvarsling/ | NLOD 2.0 (see below) | County-level endpoint, to be confirmed in a probe task |
| NVE landslide warnings | https://api.nve.no/doc/jordskredvarsling/ | NLOD 2.0 (see below) | County-level endpoint, to be confirmed in a probe task |
| MET Norway MetAlerts 2.0 | https://api.met.no/weatherapi/metalerts/2.0/documentation | CC BY 4.0 (see below) | `county=34&geographicDomain=land` |

**NVE terms:** NVE's API data is licensed under NLOD 2.0 (https://data.norge.no/nlod/no/2.0), per https://api.nve.no/doc/.
- Credit NVE ("Contains data under NLOD provided by NVE") and link to the service used.
- Mark our changes as ours.
- The data is provided "as is", with no guarantee of accuracy.

**MET terms** (https://api.met.no/doc/TermsOfService):
- The data is licensed under CC BY 4.0. Give credit, link to the licence and indicate any changes.
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

All checks are binary and run by a script against the saved source fixtures:

1. Every warning ID in the source (filtered to Innlandet and active in the period) appears exactly once in `out/digest.json`.
2. Each warning's `danger_level` equals the level in the source for that ID.
3. No `warning_id` in the digest is missing from the source.
4. No area outside Innlandet appears. Every `area` is in the Innlandet area list, or its county is 34.
5. Every date or time in the output exists in the source for that warning.
6. `sources[]` contains the NVE and MET attribution strings.
7. The digest contains no email addresses or phone numbers. This is a regex check.
8. Each `summary_no` is at most 60 words.

## Out of scope

- Personal data of any kind, including contact lists of coordinators or volunteers.
- Sending messages automatically (email, SMS, push). A human reads the digest and decides what to send.
- Making our own risk assessments or reinterpreting official danger levels.
- Areas outside Innlandet.
- Scheduling and hosting.

## Open questions for the lecturer

- Is a weekly digest frequent enough, given that warnings can change daily?
- How should updated or cancelled MetAlerts (`msgType` Update or Cancel) count towards "exactly once"?
- May we use NVE's own area names, or must areas be mapped to municipalities?
