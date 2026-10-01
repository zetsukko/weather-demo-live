# Problem Candidates

Three candidate problems for an agentic workflow in Innlandet.

## 1. Natural hazard warnings digest

- **Users:** Municipal emergency coordinators and volunteer groups in Innlandet.
- **Public source:**
  - NVE flood warning API: https://api.nve.no/doc/flomvarsling/
  - NVE landslide warning API: https://api.nve.no/doc/jordskredvarsling/
  - MET Norway MetAlerts: https://api.met.no/weatherapi/metalerts/2.0/documentation
  - Public warning site: https://www.varsom.no/
- **Terms to respect:**
  - MET: identifying `User-Agent`, respect caching headers and rate limits, attribution per https://api.met.no/doc/TermsOfService
  - NVE: API data is licensed under NLOD 2.0 (https://data.norge.no/nlod/no/2.0), per https://api.nve.no/doc/. Credit NVE ("Contains data under NLOD provided by NVE") and link to the service used; mark our changes as ours; data is provided "as is" with no guarantee of accuracy.
- **Agent step:** Produce a plain-Norwegian weekly digest of active flood, landslide and weather warnings for Innlandet.
- **Definition of success:** Every warning ID and danger level in the source appears exactly once in `out/digest.json`, and no area outside Innlandet appears.

## 2. Council agenda summaries

- **Users:** Residents and local journalists in Hamar.
- **Public source:**
  - Hamar kommune: https://www.hamar.kommune.no/
  - Published meeting agendas (saksliste PDFs): TODO: verify link
- **Terms to respect:** Reuse terms for published municipal documents — TODO: verify link. Fetch politely (identifying `User-Agent`, low request rate) and avoid repeating personal data that appears in case documents.
- **Agent step:** Write a plain-language summary for each case on the agenda.
- **Definition of success:** Every case number in the PDF appears exactly once, every date and NOK amount in the output exists in the source, and each item is at most 60 words.

## 3. Campus bus disruption brief

- **Users:** Students at Inland Norway University, Hamar and Lillehammer campuses.
- **Public source:**
  - Entur developer portal: https://developer.entur.org/
  - Real-time / journey planner API docs: TODO: verify link
- **Terms to respect:**
  - Every request must send the `ET-Client-Name` header: https://developer.entur.org/pages-intro-authentication
  - Data licence and rate limits — TODO: verify link
- **Agent step:** Write a short brief of cancellations and delays affecting the campus stops.
- **Definition of success:** Every cancelled departure for the campus stops in the source appears in the brief, and no stop outside the campus list appears.
