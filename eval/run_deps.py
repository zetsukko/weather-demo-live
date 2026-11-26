"""Stress test 2: dependency failure. What does a live run do when NVE or Ollama fails?

  py eval/run_deps.py [--tag NAME] [--limit SECONDS]

Each scenario runs harness/run.py in live mode (no --offline, no --input) with the outside
services pointed at a local test server or a bad address via NVE_FLOOD_BASE / OLLAMA_HOST.
Nothing here calls the real NVE API or a real model.

  nve_unreachable   NVE_FLOOD_BASE=http://nve.invalid            (name does not resolve)
  nve_503           local server answers HTTP 503
  nve_404           local server answers HTTP 404 (old API version removed)
  nve_hang          local server accepts the connection and never answers
  nve_html          local server answers 200 with an HTML page
  ollama_down       NVE ok (local copy of the fixture), OLLAMA_HOST is a closed port
  ollama_hang       NVE ok, local "Ollama" accepts the request and never answers

Records exit code, the stop message (or "CRASH: <exception>"), whether a digest was produced,
which files are left in out/, and the time taken. A run that is still going after --limit
seconds (default 600) is killed and recorded as a hang.
Writes eval/results/<date>_stress2_<tag>.md and .json (tag defaults to "before").
"""
import json
import os
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
RESULTS = ROOT / "eval" / "results"
RUN = ROOT / "harness" / "run.py"
FIXTURE = ROOT / "fixtures" / "nve_flood_innlandet.json"
RELEASE = threading.Event()   # set at the end so hanging handlers can exit


class Handler(BaseHTTPRequestHandler):
    """The first path segment picks the behaviour: /ok, /503, /404, /hang, /html."""

    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        mode = self.path.strip("/").split("/")[0]
        if mode == "hang":
            RELEASE.wait()
            return
        if mode == "503":
            self._send(503, b"Service Unavailable", "text/plain")
        elif mode == "404":
            self._send(404, b"Not Found", "text/plain")
        elif mode == "html":
            self._send(200, b"<!doctype html><html><head><title>Vedlikehold</title></head>"
                            b"<body><h1>Tjenesten er midlertidig utilgjengelig</h1></body></html>",
                       "text/html; charset=utf-8")
        else:
            self._send(200, FIXTURE.read_bytes(), "application/json; charset=utf-8")

    def do_POST(self):
        # Fake Ollama: only the hanging variant is needed.
        RELEASE.wait()


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def scenarios(base):
    closed = f"http://127.0.0.1:{free_port()}"   # nothing listens here
    nve_ok = f"{base}/ok"
    return [
        ("nve_unreachable", "NVE unreachable (bad host)", {"NVE_FLOOD_BASE": "http://nve.invalid"}),
        ("nve_503", "NVE returns HTTP 503", {"NVE_FLOOD_BASE": f"{base}/503"}),
        ("nve_404", "NVE returns HTTP 404", {"NVE_FLOOD_BASE": f"{base}/404"}),
        ("nve_hang", "NVE never answers", {"NVE_FLOOD_BASE": f"{base}/hang"}),
        ("nve_html", "NVE returns HTML (200)", {"NVE_FLOOD_BASE": f"{base}/html"}),
        ("ollama_down", "Ollama not running", {"NVE_FLOOD_BASE": nve_ok, "OLLAMA_HOST": closed}),
        ("ollama_hang", "Ollama never answers", {"NVE_FLOOD_BASE": nve_ok, "OLLAMA_HOST": f"{base}/hang"}),
    ], closed


def message(output):
    lines = [l.strip() for l in output.splitlines() if l.strip()]
    if any(l.startswith("Traceback") for l in lines):
        return "CRASH: " + lines[-1]
    for l in lines:
        if "no digest produced" in l or l.startswith("FAIL") or "KILL SWITCH" in l:
            return l
    return lines[-1] if lines else ""


def run_one(key, label, overrides, closed, limit):
    # Always the Ollama path, so no scenario can reach the Anthropic API; NVE stages that fail
    # first never get here. A pre-made out/digest.* shows whether old output survives.
    env = dict(os.environ, LLM_PROVIDER="ollama", OLLAMA_HOST=closed)
    env.update(overrides)
    OUT.mkdir(exist_ok=True)
    for name in ("digest.json", "digest.md"):
        (OUT / name).write_text("STALE output from an earlier run\n", encoding="utf-8")
    t0 = time.monotonic()
    try:
        p = subprocess.run([sys.executable, str(RUN)], cwd=ROOT, env=env, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=limit)
        code, output, hung = p.returncode, (p.stdout + p.stderr), False
    except subprocess.TimeoutExpired as e:
        out = e.stdout or ""
        out = out.decode("utf-8", "replace") if isinstance(out, bytes) else out
        code, output, hung = None, out, True
    seconds = round(time.monotonic() - t0, 1)
    left = sorted(f.name for f in OUT.iterdir() if f.is_file() and f.name != "probe.json")
    stale = [n for n in ("digest.json", "digest.md")
             if (OUT / n).exists() and (OUT / n).read_text(encoding="utf-8", errors="replace").startswith("STALE")]
    return {
        "case": key, "scenario": label, "exit": code, "seconds": seconds,
        "hung": hung, "message": f"killed after {limit}s" if hung else message(output),
        "digest_produced": (OUT / "digest.md").exists() and not stale,
        "stale_output_left": stale, "out_files_left": left,
    }


def table(rows):
    head = ("case", "scenario", "exit", "seconds", "digest", "message")
    data = [(r["case"], r["scenario"], r["exit"], r["seconds"],
             "yes" if r["digest_produced"] else ("STALE" if r["stale_output_left"] else "no"),
             r["message"]) for r in rows]
    widths = [max(len(str(x)) for x in col) for col in zip(head, *data)]
    line = lambda cells: "| " + " | ".join(str(c).replace("|", "\\|").ljust(w) for c, w in zip(cells, widths)) + " |"
    sep = "|" + "|".join("-" * (w + 2) for w in widths) + "|"
    return "\n".join([line(head), sep] + [line(d) for d in data])


def arg(argv, name, default):
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default


def main(argv):
    tag = arg(argv, "--tag", "before")
    limit = int(arg(argv, "--limit", 600))
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"

    rows = []
    cases, closed = scenarios(base)
    for key, label, overrides in cases:
        rec = run_one(key, label, overrides, closed, limit)
        rows.append(rec)
        print(f"{key}: exit {rec['exit']} after {rec['seconds']}s; digest={rec['digest_produced']}; {rec['message']}")
    RELEASE.set()
    server.shutdown()
    for name in ("digest.json", "digest.md"):   # do not leave the planted stale files behind
        f = OUT / name
        if f.exists() and f.read_text(encoding="utf-8", errors="replace").startswith("STALE"):
            f.unlink()

    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip() or None
    name = f"{stamp[:10]}_stress2_{tag}"
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{name}.json").write_text(json.dumps({
        "generated_at": stamp, "git_commit": commit, "mode": "live run.py, local test server",
        "limit_seconds": limit, "cases": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tbl = table(rows)
    md = [f"# Stress test 2: dependency failure ({tag})", "",
          f"Generated {stamp}, commit `{commit}`, live `harness/run.py` against a local test server; "
          f"runs killed after {limit}s.", "", tbl, "",
          "## Files left in out/", ""] + [f"- {r['case']}: {', '.join(r['out_files_left']) or '(none)'}" for r in rows] + [""]
    (RESULTS / f"{name}.md").write_text("\n".join(md), encoding="utf-8")
    print("\n" + tbl + f"\n\nWrote eval/results/{name}.md and .json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
