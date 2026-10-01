"""Probe MET Norway for tomorrow's Hamar forecast and write out/probe.json."""

import argparse
import json
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SOURCE_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=60.79&lon=11.07"
USER_AGENT = "weather-demo-live/0.1 github.com/zetsukko/weather-demo-live"

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "fixtures" / "met_hamar.json"
OUTPUT = ROOT / "out" / "probe.json"


def fetch():
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_bytes(raw)
    return json.loads(raw)


def load_fixture():
    if not FIXTURE.exists():
        sys.exit(f"Fixture not found: {FIXTURE}. Run once without --offline first.")
    return json.loads(FIXTURE.read_bytes())


def build_items(data, tomorrow):
    prefix = tomorrow.isoformat()
    items = []
    for entry in data["properties"]["timeseries"]:
        time = entry["time"]
        if not time.startswith(prefix):
            continue
        items.append({
            "title": f"Hamar {time[11:16]} UTC",
            "date": time,
            "air_temperature": entry["data"]["instant"]["details"]["air_temperature"],
        })
    return items


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="read the saved fixture instead of the network")
    args = parser.parse_args()

    if args.offline:
        data = load_fixture()
        # Anchor "tomorrow" to when the fixture was produced, so old fixtures still yield items.
        updated = data["properties"]["meta"]["updated_at"]
        today = datetime.fromisoformat(updated.replace("Z", "+00:00")).date()
    else:
        data = fetch()
        today = date.today()

    items = build_items(data, today + timedelta(days=1))
    if not items:
        sys.exit(f"No forecast entries found for {today + timedelta(days=1)}.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "source_url": SOURCE_URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "offline": args.offline,
        "items": items,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(items)} items to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
