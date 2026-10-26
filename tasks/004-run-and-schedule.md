# Task 004: One command and a daily schedule

## Goal
`harness/run.py` runs stages 1-5 with one command, and a GitHub Actions workflow runs it daily without a person at the keyboard.

## Context
- `.github/workflows/digest.yml`: cron `15 5 * * *` plus manual `workflow_dispatch`
- Secret `ANTHROPIC_API_KEY` in GitHub repo settings (Settings > Secrets and variables > Actions)

## Constraints
- Do not edit `eval/`
- `run.py` deletes stale output first, so an old digest can never fake a PASS
- Kill switch: more than 60 active warnings stops the run without a digest
- A digest that fails the check is not published (`digest.md` is removed); the digest is never sent anywhere automatically

## Acceptance (all must pass)
- `py harness/run.py --offline` exits 0 and prints PASS
- The workflow runs green from the Actions tab ("Run workflow") and uploads `out/` as an artifact

## Out of scope
Notifications, e-mail, hosting a web page
