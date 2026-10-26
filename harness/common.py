"""Shared paths and settings for the harness. Python 3 standard library only."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
FIXTURES = ROOT / "fixtures"
PROMPTS = ROOT / "prompts"

USER_AGENT = "weather-demo-live/0.2 github.com/zetsukko/weather-demo-live"

NVE_FLOOD_BASE = "https://api01.nve.no/hydrology/forecast/flood/v1.0.10"
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
