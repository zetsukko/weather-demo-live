# Varsel Innlandet – daily digest of flood warnings for Innlandet

KIUA-2003 course project (Kim and Ådne). An agentic harness that fetches official NVE flood warnings for Innlandet (county 34), has a language model write a short plain-Norwegian summary of each warning, and checks the result with code before anyone reads it.

```
NVE API -> 1 fetch -> 2 normalise -> 3 summarise (LLM) -> 4 assemble -> 5 check (exit 0/1/2)
```

The model writes prose only. Warning IDs, danger levels, areas and dates are copied by code from the source. See `SPEC.md` for the definition of success.

## Requirements

- Python 3.10 or newer (standard library only; no packages to install)
- Optional: [Ollama](https://ollama.com) with `llama3.2:3b` (`ollama pull llama3.2:3b`) for the summary step. Without a model, deterministic template summaries are used.

## Reproduce a run

```bash
# Offline: replays the saved NVE response and model answer in fixtures/ (no network, no key)
python harness/run.py --offline

# Live: fetches today's warnings from NVE and calls the local model if LLM_PROVIDER=ollama is set
cp .env.example .env        # then uncomment LLM_PROVIDER=ollama and OLLAMA_MODEL
python harness/run.py

# Live run that also refreshes the fixtures
python harness/run.py --save-fixture

# Check an existing output on its own
python eval/check_digest.py
```

On Windows, use `py` instead of `python`.

A successful run ends with `PASS` and exit code 0. Exit codes of `harness/run.py`:

| code | meaning |
|---|---|
| 0 | digest produced and both checks passed (`eval/check_digest.py`, `eval/check_freshness.py`) |
| 1 | no trustworthy digest: a check failed, or the input data was rejected in stage 2 |
| 2 | an outside service failed: NVE (unreachable, HTTP error, timeout, not JSON) or the Anthropic API |

Offline and `--input` runs use saved data. Their digest heading and `digest.json` (`data_source: "saved"`, `data_note`) say so, e.g. "Lagrede data fra 26.10.2026 kl. 09:22, ikke dagens varsler". `eval/check_freshness.py` fails a live digest whose NVE data was published more than 24 hours before it.

Output:

- `out/digest.json` – machine-readable digest (what the check reads)
- `out/digest.md` – readable digest (removed again if the check fails)
- `out/raw_nve_flood.json`, `out/warnings.json`, `out/summaries.json` – intermediate stages

## Evaluation run

```bash
py eval/run_eval.py
```

Replays every saved case in `eval/cases/<case>/` through the whole harness (`harness/run.py --input <case>/nve.json --no-llm`, so it is deterministic and needs no network or model), runs `eval/check_digest.py`, and compares the outcome with the case's `expected.json`. It prints a table (case, expected, result, PASS/FAIL) with totals and writes `eval/results/latest.md` and `eval/results/latest.json`. Exit code 0 means every case passed.

| case | what it tests | expected |
|---|---|---|
| `real_2610` | unchanged NVE response of 26.10.2026 | warning 584962, level 2 |
| `empty_day` | all records level 1 | no-warnings message |
| `orange_level3`, `red_level4` | warning 584962 at level 3 / 4 | level copied exactly |
| `multi_county` | 584962 also lists county 31 | still included |
| `other_county_only` | extra warning for county 46 only | must not appear |
| `conflicting_records` | same Id, different levels | run stops, no digest |
| `missing_fields` | yellow warning without `ValidTo` | run stops, no digest |
| `bad_level_text`, `missing_id`, `missing_countylist` | malformed records | run stops cleanly, no digest |
| `huge_text` | MainText of 50 000 characters | warning 584962, level 2 |
| `injection_safe`, `injection_phone`, `injection_english` | prompt injection in MainText | warning 584962, level 2 |

A reject only passes if the run stopped itself with a "no digest produced" message; a Python traceback counts as a crash. Stress tests: `py eval/run_stress.py` (injection and huge input against the real model, checked by `eval/check_injection.py`) and `py eval/run_deps.py` (NVE and Ollama failures against a local test server).

All cases except `real_2610` are derived from it; each `expected.json` has `derived_from` and a one-line `description` of the change. Rebuild the inputs with `py eval/cases/build_cases.py`. Any single saved response can also be run directly: `py harness/run.py --input <file> --no-llm`.

## Automatic daily run

`.github/workflows/digest.yml` runs the offline check and then a live run every day at 05:15 UTC, and uploads `out/` as an artifact. The GitHub runner has no local model, so this run uses the template summaries; summaries written by the model come from local runs with Ollama. The workflow still passes the `ANTHROPIC_API_KEY` secret; it is unused while the secret is not set, and setting it later switches the Actions run to the Anthropic API. Start a run by hand from the Actions tab with "Run workflow".

## Context files

- `prompts/digest.md` – instructions for the summary model (runtime context)
- `CLAUDE.md` – how the coding agent works in this repository
- `SPEC.md` – problem, users, sources, definition of success
- `tasks/` – one file per task with its acceptance check

## Safe operation (current state)

- The LLM gets only the normalised Innlandet warnings; warning text is passed as data, not instructions.
- One model call per run, output capped at 2000 tokens.
- The model runs locally through Ollama: a run costs nothing and warning data never leaves the machine.
- Kill switch: more than 60 active warnings, an NVE failure, or invalid model output stops the run without a digest.
- NVE calls have a total time limit of 30 s and one retry after 5 s on HTTP 5xx or a timeout (worst case about 65 s).
- If the local model is down or does not answer within 60 s, the run uses the template summaries (`summary_mode: "fallback"`, reason "model unavailable: ...") and still produces a checked digest; facts come from code either way.
- Official text is capped at 1500 characters per field before it reaches the model, and Ollama gets a 4096-token context window, so long warnings are not cut silently.
- The digest is never sent anywhere automatically; a person decides what to pass on.
- No API key is needed; any optional key lives only in `.env` (git-ignored) or GitHub secrets.

## Data and licence

Flood warnings from NVE / Flomvarslingstjenesten via [varsom.no](https://www.varsom.no), API docs at https://api.nve.no/doc/flomvarsling/, licensed under [NLOD 2.0](https://data.norge.no/nlod/no/2.0). Data is provided "as is". The summaries are produced by this project and are not official warnings.

## Earlier work

`index.html`, `harness/probe.py` and `eval/check_probe.py` are from task 001 (MET Norway forecast probe for Hamar), which established the fixture and `--offline` pattern.
