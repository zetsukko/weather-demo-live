# Varsel Innlandet – daily digest of flood warnings for Innlandet

KIUA-2003 course project (Kim and Ådne). An agentic harness that fetches official NVE flood warnings for Innlandet (county 34), has a language model write a short plain-Norwegian summary of each warning, and checks the result with code before anyone reads it.

```
NVE API -> 1 fetch -> 2 normalise -> 3 summarise (LLM) -> 4 assemble -> 5 check (exit 0/1)
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

A successful run ends with `PASS` and exit code 0. Output:

- `out/digest.json` – machine-readable digest (what the check reads)
- `out/digest.md` – readable digest (removed again if the check fails)
- `out/raw_nve_flood.json`, `out/warnings.json`, `out/summaries.json` – intermediate stages

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
- Kill switch: more than 60 active warnings, an API error, or invalid model output stops the run without a digest.
- The digest is never sent anywhere automatically; a person decides what to pass on.
- No API key is needed; any optional key lives only in `.env` (git-ignored) or GitHub secrets.

## Data and licence

Flood warnings from NVE / Flomvarslingstjenesten via [varsom.no](https://www.varsom.no), API docs at https://api.nve.no/doc/flomvarsling/, licensed under [NLOD 2.0](https://data.norge.no/nlod/no/2.0). Data is provided "as is". The summaries are produced by this project and are not official warnings.

## Earlier work

`index.html`, `harness/probe.py` and `eval/check_probe.py` are from task 001 (MET Norway forecast probe for Hamar), which established the fixture and `--offline` pattern.
