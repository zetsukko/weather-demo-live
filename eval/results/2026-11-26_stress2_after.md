# Stress test 2: dependency failure (after)

Generated 2026-11-26T12:59:55+00:00, commit `f89b353`, live `harness/run.py` against a local test server; runs killed after 600s.

| case            | scenario                   | exit | seconds | digest | message                                                                                                                                                                                                                      |
|-----------------|----------------------------|------|---------|--------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| nve_unreachable | NVE unreachable (bad host) | 2    | 0.2     | no     | NVE API unreachable ([Errno 11001] getaddrinfo failed); no digest produced.                                                                                                                                                  |
| nve_503         | NVE returns HTTP 503       | 2    | 5.2     | no     | NVE API returned HTTP 503; no digest produced.                                                                                                                                                                               |
| nve_404         | NVE returns HTTP 404       | 2    | 0.1     | no     | NVE API returned HTTP 404; the API version v1.0.10 may have been retired, check https://api.nve.no/doc/flomvarsling/; no digest produced.                                                                                    |
| nve_hang        | NVE never answers          | 2    | 65.2    | no     | NVE API timed out; no digest produced.                                                                                                                                                                                       |
| nve_html        | NVE returns HTML (200)     | 2    | 0.1     | no     | NVE response is not valid JSON; no digest produced.                                                                                                                                                                          |
| ollama_down     | Ollama not running         | 0    | 2.3     | yes    | MODEL UNAVAILABLE: Ollama (llama3.2:3b) unreachable ([WinError 10061] No connection could be made because the target machine actively refused it). Using template summaries; facts come from code. Run exit 0, check passed. |
| ollama_hang     | Ollama never answers       | 0    | 60.3    | yes    | MODEL UNAVAILABLE: Ollama (llama3.2:3b) timed out after 60 s. Using template summaries; facts come from code. Run exit 0, check passed.                                                                                      |

## Files left in out/

- nve_unreachable: (none)
- nve_503: (none)
- nve_404: (none)
- nve_hang: (none)
- nve_html: (none)
- ollama_down: digest.json, digest.md, raw_nve_flood.json, summaries.json, warnings.json
- ollama_hang: digest.json, digest.md, raw_nve_flood.json, summaries.json, warnings.json
