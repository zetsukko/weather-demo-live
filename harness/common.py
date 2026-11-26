"""Shared paths and settings for the harness. Python 3 standard library only."""
import os
import sys
import threading
from pathlib import Path

# Exit codes of harness/run.py
EXIT_OK = 0        # digest produced and every check passed
EXIT_CHECK = 1     # no trustworthy digest: a check failed or the input data was rejected
EXIT_SERVICE = 2   # an outside service failed (NVE, or the Anthropic API)

# Time limits per call, for the whole call and not only per network read.
NVE_TIMEOUT = 30
OLLAMA_TIMEOUT = 60
RETRY_DELAY = 5    # NVE: one retry after this many seconds on HTTP 5xx or a timeout


def stop(message, code=EXIT_CHECK):
    """End the run without a digest: message on stderr, chosen exit code."""
    print(message, file=sys.stderr)
    sys.exit(code)


def call_with_deadline(fn, seconds):
    """Run fn() and return its result, or raise TimeoutError if it takes longer than seconds.

    Socket timeouts only limit each read, so a server that trickles one byte at a time
    could keep a call alive forever; this caps the whole call. The worker thread is a
    daemon, so a stuck call cannot keep the process alive after the run ends.
    """
    result = {}

    def work():
        try:
            result["value"] = fn()
        except BaseException as e:   # handed to the caller below
            result["error"] = e

    t = threading.Thread(target=work, daemon=True)
    t.start()
    t.join(seconds)
    if t.is_alive():
        raise TimeoutError(f"no complete answer within {seconds} s")
    if "error" in result:
        raise result["error"]
    return result["value"]

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
FIXTURES = ROOT / "fixtures"
PROMPTS = ROOT / "prompts"

USER_AGENT = "weather-demo-live/0.2 github.com/zetsukko/weather-demo-live"

# NVE_FLOOD_BASE can be overridden for dependency tests (eval/run_deps.py); default is the real API.
NVE_FLOOD_BASE = (os.environ.get("NVE_FLOOD_BASE") or
                  "https://api01.nve.no/hydrology/forecast/flood/v1.0.10").rstrip("/")
INNLANDET = "34"          # county number (fylkesnummer)
LANG_NO = "1"             # NVE language key: 1 = Norwegian
MIN_LEVEL = 2             # NVE activity level 2 (yellow) and above counts as active

RAW_FILE = OUT / "raw_nve_flood.json"
NORMALISED_FILE = OUT / "warnings.json"
SUMMARIES_FILE = OUT / "summaries.json"
DIGEST_JSON = OUT / "digest.json"
DIGEST_MD = OUT / "digest.md"

FIXTURE_RAW = FIXTURES / "nve_flood_innlandet.json"
FIXTURE_LLM = FIXTURES / "llm_summaries.json"

# Safe-operation limits (kill switch): the run stops without producing a digest if exceeded.
MAX_WARNINGS = 60
MAX_TOKENS = 2000

# Context window: each official text field is capped before it goes to the model,
# and Ollama gets a window large enough for the capped prompt.
MAX_TEXT_CHARS = 1500
OLLAMA_NUM_CTX = 4096

ATTRIBUTION = [
    "Flomvarsler fra NVE / Flomvarslingstjenesten (varsom.no), NLOD 2.0. "
    "Contains data under NLOD provided by NVE. Data levert 'som den er'.",
    "Sammendragene er laget automatisk i dette prosjektet (språkmodell eller mal) og er ikke offisielle varsler. "
    "Les alltid hele varselet på https://www.varsom.no.",
]


def load_dotenv():
    """Minimal .env loader (KEY=VALUE lines). Never prints values."""
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
