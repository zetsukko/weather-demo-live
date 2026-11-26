"""Binary check: is the digest honest about how old its NVE data is?

  py eval/check_freshness.py

Reads out/digest.json (written by harness/assemble.py) and fails (exit 1) if
  - the digest does not say where its data came from (data_source "live" or "saved")
  - a live digest has no NVE publish time, or its NVE data is more than 24 hours older
    than the digest (a stale response presented as today's warnings)
  - a saved-data digest (--offline, --input) does not carry the note "ikke dagens varsler"
Prints PASS and exits 0 otherwise. Run by harness/run.py after eval/check_digest.py.
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIGEST = ROOT / "out" / "digest.json"
MAX_AGE = timedelta(hours=24)


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


digest = json.loads(DIGEST.read_text(encoding="utf-8"))
source = digest.get("data_source")

if source == "saved":
    if "ikke dagens varsler" not in (digest.get("data_note") or ""):
        fail("saved-data digest does not say 'ikke dagens varsler'")
    print(f"PASS (saved data, marked: {digest['data_note']})")
elif source == "live":
    try:
        generated = datetime.fromisoformat(digest["generated_at"])
        published = datetime.fromisoformat(digest["data_published"])
    except (KeyError, TypeError, ValueError):
        fail("live digest has no valid NVE publish time (data_published)")
    age = generated - published
    if age > MAX_AGE:
        fail(f"live digest uses NVE data published {age.total_seconds() / 3600:.0f} hours before the digest (limit 24)")
    print(f"PASS (live data, published {age.total_seconds() / 3600:.1f} hours before the digest)")
else:
    fail("digest does not say where its data came from (data_source)")
