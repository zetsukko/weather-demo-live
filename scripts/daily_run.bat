@echo off
rem Daily live run for Windows Task Scheduler (replaces the GitHub Actions schedule, task 009).
rem Runs harness/run.py from the repo root and appends its output, with start and end
rem timestamps and the exit code (0 ok, 1 no trustworthy digest, 2 outside service failed),
rem to logs\daily_run.log. The script's exit code is the run's exit code.
setlocal
cd /d "%~dp0.." || exit /b 1
if not exist logs mkdir logs

rem Use the local model unless the caller chose a provider. Values in the environment win
rem over .env. If Ollama is not running, the harness falls back to template summaries.
if not defined LLM_PROVIDER set "LLM_PROVIDER=ollama"
rem Redirected output would otherwise use the ANSI code page and be buffered, which puts
rem the check lines (printed by a child process) before the stage lines in the log.
set "PYTHONIOENCODING=utf-8"
set "PYTHONUNBUFFERED=1"

>>logs\daily_run.log echo ===== %date% %time% start =====
py harness\run.py >>logs\daily_run.log 2>&1
set "CODE=%errorlevel%"
>>logs\daily_run.log echo ===== %date% %time% end, exit %CODE% =====
>>logs\daily_run.log echo.
exit /b %CODE%
