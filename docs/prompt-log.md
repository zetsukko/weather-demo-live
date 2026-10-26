# Prompt Log

## 2026-10-01

- **Task 001 plan — User-Agent lacked contact info.** The plan's default `User-Agent` for the MET Norway probe had no contact information, which MET's terms of service require. Rejected the plan and had the agent use the repo URL instead: `weather-demo-live/0.1 github.com/zetsukko/weather-demo-live`.
- **Unrequested push during scaffolding.** While scaffolding the project, the agent pushed to GitHub without being asked.
- **GitHub token in git remote URL.** The agent found a GitHub token embedded in the `origin` remote URL. Revoked the token and switched to credential-manager login (`git remote set-url origin https://github.com/zetsukko/weather-demo-live.git`).

## 2026-10-26

- **SPEC contradicted the technical minimum.** The agent-drafted `SPEC.md` listed "Scheduling and hosting" as out of scope, but the assignment requires at least one part to run automatically. Corrected: the daily run is in scope (GitHub Actions), only hosting and notifications are out of scope.
- **Wrong licence for MET data.** The agent-drafted `SPEC.md` gave MET Norway's licence as CC BY 4.0 only. Checking https://api.met.no/doc/License showed NLOD 2.0 and CC BY 4.0. Corrected in `SPEC.md`.
- **Facts kept away from the model.** Instead of letting the LLM write the whole digest, we required that IDs, levels, areas and dates are copied by code and the model only writes `summary_no`. The check then rejects any summary containing a number that is not in the source.
- **Wrong NVE endpoint in generated code.** The harness code from a separate Claude session used `.../flood/v1.0.10/Warning/County/34/1`, which returns 404. The coding agent tested the endpoint before running, found the correct path is `.../flood/v1.0.10/api/Warning/County/34/1` (200, 138 records), and proposed the fix. Lesson: verify every API path against the live service, not only the docs.
- **Duplicate warning IDs.** The generated normalise.py assumed one NVE record per warning, but NVE sends one record per municipality sharing the same Id. The coding agent found this in the live response and merged records by Id, stopping the run if the merged records disagree on level or validity. Without the fix the check would have failed (same warning listed 5 times).
- **Weak Norwegian from llama3.2:3b.** The first live Ollama digest passed all fact checks but contained wrong or garbled Norwegian ('Flomfare er utsatt', 'sikre verdier bort fra'). The binary checks cannot catch language quality; this motivates the LLM-as-judge readability rubric and a model comparison in the evaluation.
