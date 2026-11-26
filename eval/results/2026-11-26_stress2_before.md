# Stress test 2: dependency failure (before)

Generated 2026-11-26T12:38:02+00:00, commit `c52e785`, live `harness/run.py` against a local test server; runs killed after 600s.

| case            | scenario                   | exit | seconds | digest | message                                                                                                                                             |
|-----------------|----------------------------|------|---------|--------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| nve_unreachable | NVE unreachable (bad host) | 1    | 0.2     | no     | NVE API unreachable ([Errno 11001] getaddrinfo failed); no digest produced. Try --offline.                                                          |
| nve_503         | NVE returns HTTP 503       | 1    | 0.1     | no     | NVE API returned HTTP 503; no digest produced.                                                                                                      |
| nve_404         | NVE returns HTTP 404       | 1    | 0.1     | no     | NVE API returned HTTP 404; no digest produced.                                                                                                      |
| nve_hang        | NVE never answers          | 1    | 30.3    | no     | CRASH: TimeoutError: timed out                                                                                                                      |
| nve_html        | NVE returns HTML (200)     | 1    | 0.2     | no     | NVE response is not valid JSON; no digest produced.                                                                                                 |
| ollama_down     | Ollama not running         | 1    | 2.2     | no     | Ollama (llama3.2:3b) unreachable ([WinError 10061] No connection could be made because the target machine actively refused it); no digest produced. |
| ollama_hang     | Ollama never answers       | 1    | 300.2   | no     | Ollama (llama3.2:3b) failed (timed out); no digest produced.                                                                                        |

## Files left in out/

- nve_unreachable: (none)
- nve_503: (none)
- nve_404: (none)
- nve_hang: (none)
- nve_html: (none)
- ollama_down: raw_nve_flood.json, warnings.json
- ollama_hang: raw_nve_flood.json, warnings.json
