# Safe operation

How Varsel Innlandet is kept safe to run: what the coding agent and the runtime harness may touch, how secrets are kept out of the repo, what a run can cost, where a person must decide, and when a run (or the whole system) stops. Every statement describes the code as it is on master after task 009. File references are `path:line`. Known gaps are listed at the end, not hidden in the text.

```
NVE API -> 1 fetch -> 2 normalise -> 3 summarise (LLM) -> 4 assemble -> 5 check (exit 0/1/2)
```

`SPEC.md` defines success; `README.md` explains how to run the harness.

## 1. Permission scoping

### Coding agent (Claude Code in this repository)

| control | where | effect |
|---|---|---|
| `Read(.env)`, `Read(.env.local)` denied | `.claude/settings.json:4-5` | the agent's Read tool cannot open the secrets file |
| `Edit(/eval/check_digest.py)`, `Edit(/eval/check_probe.py)` denied | `.claude/settings.json:6-7` | the agent cannot change the checkers that decide PASS/FAIL |
| "Never edit anything inside `eval/` without asking the user first." | `CLAUDE.md` Rules | covers the rest of `eval/` (cases, runners, other checks) |
| "Facts ... must come from stage 2 code, never from the model." | `CLAUDE.md` Rules | design rule the agent must keep when changing code |
| "No personal data in any tracked file; never read or print `.env` or keys." | `CLAUDE.md` Rules | |
| "Python standard library only." | `CLAUDE.md` Rules | no third-party packages to install or audit |
| "One task = one branch = one PR; do not push unless asked." | `CLAUDE.md` Rules | every change is reviewed by a person before it reaches master |

The deny rule started as `Edit(/eval/**)`. In task 005 it blocked the agent from adding eval cases; the agent stopped instead of writing through the shell, and we narrowed it to the two checkers (`docs/prompt-log.md:21`).

### Runtime harness (`harness/run.py`)

Hosts it calls:

| host | when | where |
|---|---|---|
| `https://api01.nve.no/hydrology/forecast/flood/v1.0.10/api/Warning/County/34/1` | every live run (not `--offline` or `--input`) | `harness/common.py:56-57`, `harness/fetch.py:31-32` |
| `https://api.anthropic.com/v1/messages` | live run with `ANTHROPIC_API_KEY` set and `LLM_PROVIDER` not `ollama` | `harness/summarise.py:26`, `harness/summarise.py:179-191` |
| `http://localhost:11434/api/chat` (Ollama) | live run with `LLM_PROVIDER=ollama` | `harness/summarise.py:28`, `harness/summarise.py:146-160` |

- `--offline` makes no network calls at all. `--input <file>` makes no NVE call. `--no-llm` makes no model call.
- The base URLs can be changed through environment variables (`NVE_FLOOD_BASE`, `ANTHROPIC_BASE_URL`, `OLLAMA_HOST`). `NVE_FLOOD_BASE` exists for the dependency stress test, which points it at a local test server (`harness/common.py:55`, `eval/run_deps.py`).
- `harness/probe.py` (MET Norway, `api.met.no`) is from task 001 and is not called by `run.py`.

Files it writes:

- Only `out/`: `raw_nve_flood.json`, `warnings.json`, `summaries.json`, `digest.json`, `digest.md`. All five are deleted at the start of every run, so an old digest cannot fake a PASS (`harness/run.py:43-46`).
- `fixtures/` only with `--save-fixture` (`harness/fetch.py:89-91`, `harness/summarise.py:200-201`).
- `logs/daily_run.log`: not written by `run.py` itself, but appended by `scripts/daily_run.bat` on the scheduled run (see below).

Files it reads: `fixtures/` (offline), `prompts/digest.md` (model instructions), and `.env` through `load_dotenv`. That happens only on the live model path (`harness/summarise.py:180`), and the loader never prints values (`harness/common.py:88-98`).

### Scheduled run (Windows Task Scheduler)

Windows Task Scheduler runs `scripts/daily_run.bat` once a day at 07:15 local time. The task is registered with `schtasks` and `/IT`, so it runs only while the user is logged on (`README.md:85`). The script changes to the repo root (`scripts/daily_run.bat:7`), sets `LLM_PROVIDER=ollama` unless it is already set (line 12), runs `py harness\run.py`, and appends the output with start and end timestamps and the exit code to `logs/daily_run.log` (lines 18-22). `logs/` is git-ignored (`.gitignore:26`). The script runs as the logged-on user and does only what a live run does: it calls NVE and the local Ollama, writes `out/` and the log, and cannot push, comment or send anything.

The GitHub workflow `.github/workflows/digest.yml` now has only `workflow_dispatch` (lines 7-8), no schedule, because the account's Actions billing was locked when the student plan expired (lines 1-5, `docs/prompt-log.md:31`). A manual run there still has a read-only token (lines 9-10) and a 10-minute job limit (line 14).

## 2. Secrets management

- **Where keys live.** Only in `.env` (local) or GitHub repository secrets. `.env` and `.env.local` are git-ignored (`.gitignore:1-3`), as is `.claude/settings.local.json` (`.gitignore:6`). `.env.example` lists variable names with empty values and says "Never commit .env" (`.env.example:1`).
- **No key is required.** Without `ANTHROPIC_API_KEY` the harness uses the local Ollama model or template summaries (`harness/summarise.py:182-193`). The GitHub workflow passes the `ANTHROPIC_API_KEY` secret (`digest.yml:23-24`), but the secret is not set, so a manual GitHub run uses templates. The scheduled run is local and uses Ollama (`scripts/daily_run.bat:12`).
- **Keys stay out of prompts.** The key is sent only in the `x-api-key` request header (`harness/summarise.py:129-133`). The model receives `prompts/digest.md` and the normalised warnings, nothing else (`harness/summarise.py:67-82`).
- **Keys stay out of logs.** The harness prints token counts, not requests (`harness/summarise.py:140`, `:165`). Error messages carry only the HTTP status or the connection reason (`harness/summarise.py:98-107`). `load_dotenv` never prints values.
- **Keys stay away from the coding agent.** The Read tool is denied `.env` and `.env.local` (`.claude/settings.json:4-5`), and CLAUDE.md says never to read or print `.env` or keys.
- **Incident.** On 2026-10-01 the agent found a GitHub token embedded in the `origin` remote URL. The token was revoked and the remote switched to credential-manager login (`docs/prompt-log.md:7`). `origin` is now a plain `https://github.com/...` URL with no credentials.

## 3. Cost control

| limit | value | enforced in |
|---|---|---|
| model calls per run | 1 (all warnings in one request, no retry) | `harness/summarise.py:184`, `:191` |
| output tokens | 2000 (`max_tokens` for Anthropic, `num_predict` for Ollama) | `harness/common.py:73`, `harness/summarise.py:125`, `:156` |
| official text per field | 1500 characters, cut at a sentence end and marked "[forkortet]"; the run prints a line when it cuts | `harness/common.py:77`, `harness/summarise.py:53-78` |
| Ollama context window | 4096 tokens, so the capped prompt is not cut silently | `harness/common.py:78`, `harness/summarise.py:158` |
| warnings per run | 60; more stops the run **before** the model is called | `harness/common.py:72`, `harness/run.py:58-61` |
| time per call | NVE 30 s total plus one retry after 5 s (worst case about 65 s); Ollama 60 s; Anthropic 120 s | `harness/common.py:13-15`, `harness/summarise.py:135`, `:163` |
| time per GitHub job | 10 minutes; applies only to manual GitHub runs, the Task Scheduler run has no job limit beyond the per-call limits above | `.github/workflows/digest.yml:14` |
| runs per day | 1 scheduled through Task Scheduler (07:15), plus manual starts | `README.md:85`, `.github/workflows/digest.yml:7-8` |

The default model is the local `llama3.2:3b` through Ollama, which costs no API money, and warning data never leaves the machine. The Anthropic path is optional and is used only when a key is present. Templates (`--no-llm`, or no model configured) make no model call at all. Each live model run prints its token usage (`harness/summarise.py:140`, `:165`).

## 4. Human-in-the-loop gates

**Automatic:** fetch, normalise, summarise, assemble and both checks, triggered by one command or the daily Task Scheduler run. The checks (`eval/check_digest.py`, `eval/check_freshness.py`) decide automatically whether the digest may be used. If one fails, `digest.md` is deleted (`harness/run.py:72-79`).

**Needs a person:**

- **Passing a digest on.** Nothing is sent anywhere automatically. There is no e-mail, SMS, chat or web publishing in the code, and sending notifications is out of scope (`SPEC.md:82`). The result is `out/digest.md` on the machine that ran it, including the daily scheduled run (or the artifact of a manual GitHub run). A person reads it and decides what, if anything, to forward to the municipalities' emergency coordinators.
- **Refreshing the saved test data.** `--save-fixture` is a manual flag; CI never uses it.
- **Changing the system.** Each task goes on its own branch and PR, the agent does not push unless asked, and checkers in `eval/` are not changed without asking (`CLAUDE.md`).

**Why:** the summaries are not official warnings. Every digest says so and points to varsom.no (`harness/common.py:80-85`). The checks prove the facts (IDs, levels, areas, dates, no invented numbers) but not language quality: llama3.2:3b has written garbled or misleading Norwegian that passed every fact check (`docs/prompt-log.md:16`, `:25`). A wrong or misread flood warning can lead to wrong action, so a person stays between the machine and the people who act on it.

## 5. Kill switch

A run stops **without a digest** in every case below. The message goes to the terminal (or `logs/daily_run.log` for the scheduled run). Exit 2 means an outside service failed, and trying again later may help. Exit 1 means the data or the result cannot be trusted.

| # | condition | message (as printed) | exit | where |
|---|---|---|---|---|
| 1 | NVE returns HTTP 404 | `NVE API returned HTTP 404; the API version v1.0.10 may have been retired, check https://api.nve.no/doc/flomvarsling/; no digest produced.` | 2 | `harness/fetch.py:50-52` |
| 2 | NVE returns HTTP 4xx, or 5xx twice | `NVE API returned HTTP <code>; no digest produced.` | 2 | `harness/fetch.py:53-54` |
| 3 | NVE unreachable (name does not resolve, connection refused) | `NVE API unreachable (<reason>); no digest produced.` | 2 | `harness/fetch.py:58-61` |
| 4 | NVE times out twice (30 s total each) | `NVE API timed out; no digest produced.` | 2 | `harness/fetch.py:62-63` |
| 5 | NVE response is not JSON / not a list | `NVE response is not valid JSON; no digest produced.` / `Unexpected NVE response (not a list); no digest produced.` | 2 live, 1 saved | `harness/fetch.py:80-87` |
| 6 | `--input` without a path | `--input needs a file path, e.g. --input eval/cases/real_2610/nve.json` | 1 | `harness/run.py:39-40` |
| 7 | `--input` file missing | `Input file not found: <path>; no digest produced.` | 1 | `harness/fetch.py:71-72` |
| 8 | `--offline` without a fixture | `Fixture not found: <path>. Run once online with --save-fixture.` | 1 | `harness/fetch.py:75-76` |
| 9 | NVE record without Id | `NVE record without Id; no digest produced.` | 1 | `harness/normalise.py:41-42` |
| 10 | ActivityLevel not a whole number | `NVE warning <id> has ActivityLevel <value>, not a whole number; no digest produced.` | 1 | `harness/normalise.py:32-33` |
| 11 | active warning without CountyList | `NVE warning <id> has no CountyList, so we cannot tell if it is for Innlandet; no digest produced.` | 1 | `harness/normalise.py:48-49` |
| 12 | active Innlandet warning without ValidFrom/ValidTo | `NVE warning <id> has no ValidTo; no digest produced.` (or ValidFrom) | 1 | `harness/normalise.py:53-55` |
| 13 | records with the same Id disagree on level or validity | `NVE records for warning <id> disagree on level or validity; no digest produced.` | 1 | `harness/normalise.py:57-60` |
| 14 | more than 60 active warnings | `KILL SWITCH: <n> warnings > 60; no digest produced.` | 1 | `harness/run.py:58-61` |
| 15 | Anthropic API fails (HTTP error, 120 s timeout, unreachable, bad reply) | `LLM API returned HTTP <code>; no digest produced.` / `LLM API timed out after 120 s; ...` / `LLM API unreachable (<reason>); ...` / `LLM API failed (<error>); ...` | 2 | `harness/summarise.py:134-137` |
| 16 | model answer is not a JSON object (either provider) | `LLM output was not valid JSON; no digest produced.` / `LLM output was not a JSON object; no digest produced.` | 1 | `harness/summarise.py:110-118` |
| 17 | `eval/check_digest.py` fails a property (completeness, no invention, fidelity, locality, grounded summary of at most 60 words with no numbers outside the source, attribution and no e-mail/phone, empty case) | `FAIL: property <n>: ...`, then `[5 check] exit 1`; `digest.md` is deleted | 1 | `eval/check_digest.py`, `harness/run.py:72-79` |
| 18 | `eval/check_freshness.py` fails: live NVE data more than 24 h older than the digest, saved data not marked "ikke dagens varsler", or no `data_source` | `FAIL: ...`, then `[5 check] exit 1`; `digest.md` is deleted | 1 | `eval/check_freshness.py`, `harness/run.py:72-79` |

Outside the harness, a manual GitHub run is killed after 10 minutes (`digest.yml:14`), and a failed offline regression step stops that job before the live run (lines 20-25). The scheduled run has no such outer limit or offline step; it is bounded only by the per-call time limits in section 3.

**Degrades but does not stop** (the digest is still produced and checked; facts come from code either way):

- Ollama down, erroring or silent for 60 s: prints `MODEL UNAVAILABLE: <reason>. Using template summaries; facts come from code.`. The digest has `summary_mode: "fallback"` and reason `model unavailable: ...` (`harness/summarise.py:182-189`).
- A model summary that drops the colour word for its level, or says "utsatt" (without "for"), "avlyst" or "ingen fare", is replaced by the template summary, with the reason recorded in `fallback` (`harness/assemble.py:27-54`).

### Abandonment criterion

The kill switch stops one run. This criterion is a rule we set for the operators, not something the code enforces. **Stop using the system entirely** and tell recipients to use varsom.no directly when any of the following happens:

1. **A wrong digest passed the checks.** A digest that passed both checks has a wrong warning ID, level, area or validity period, or misses an active Innlandet warning that varsom.no shows. The checks are then not trustworthy. Resume only after an eval case reproduces the error and fails before the fix and passes after it.
2. **The source changed.** NVE retires API v1.0.10 (stop #1) or changes the response format, and no fix has been merged.
3. **No checked digest for 3 days.** Live runs fail to produce a checked digest (exit 1 or 2) on 3 consecutive days. Recipients may by then rely on a digest that is not arriving.
4. **A secret leaked.** A key or token appears in the repository, a log or a CI artifact. Revoke it first; resume after the leak path is closed.

One weaker rule does not stop the system, only the model: if most live digests with the model on fall back to the template (`summary_mode: "fallback"`), stop using the model and run template-only (`--no-llm`), because the model then adds risk and no value.

## Known gaps

- **Deny rules cover the Read and Edit tools, not the shell.** The agent could still `cat .env` or rewrite a checker through Bash; only the CLAUDE.md text forbids it. `eval/check_freshness.py` and `eval/check_injection.py` have no deny rule at all. Nothing technically blocks `git push`, and an unrequested push did happen once (`docs/prompt-log.md:6`).
- **The output cap is not a kill switch.** The comment at `harness/common.py:71` groups `MAX_TOKENS` with the kill-switch limits, but reaching 2000 output tokens does not stop the run by itself. A cut-off answer is then usually invalid JSON and stops at stop #16.
- **No total input cap and no spend limit.** The 1500-character cap is per field, not per prompt. With up to 60 warnings × 3 fields × 1500 characters (about 270 000 characters), the prompt can still overflow Ollama's 4096-token window, or become a large Anthropic request. There is no budget or monthly limit in code; on the Anthropic path that has to be set in the provider account.
- **`out/digest.json` survives a failed check.** Only `digest.md` is deleted (`harness/run.py:77-79`). The failed `digest.json` stays in `out/` until the next run deletes it (`harness/run.py:43-46`), so someone opening `out/` after a failed scheduled run can find a digest that did not pass.
- **The Anthropic path has no fallback.** An API failure ends the run without a digest (exit 2), unlike Ollama, which falls back to templates (`docs/prompt-log.md:29`).
- **Unforeseen input can still crash.** Input shapes not covered by the stops above (for example a list element that is not a JSON object) raise a Python traceback. That also exits 1, and the exit code alone cannot tell it from a controlled stop.
- **What the checks do not see.** Personal names are forbidden only in the prompt (`prompts/digest.md:12`); the checker looks for e-mail addresses and phone numbers, not names. Language quality is not checked. The freshness check treats NVE times without an offset as fixed UTC+1, an hour off in summer (`harness/fetch.py:25-27`).
- **No alerting.** A failed scheduled run is visible only in `logs/daily_run.log` (its exit code on the end line). Nobody is notified.
- **The scheduled run needs the PC on and the user logged in.** If the machine is off or asleep at 07:15, or nobody is logged on (`/IT`), the run does not happen. A missed day leaves no digest and no warning, not even a line in the log.
