"""Stage 1 - Fetch: NVE flood warnings for Innlandet (county 34).

Online:  GET {base}/api/Warning/County/34/1  (today, tomorrow and the day after)
Offline: replay fixtures/nve_flood_innlandet.json
Input:   --input <file> replays any saved NVE response (used by eval/run_eval.py)
Always writes the raw response that was used to out/raw_nve_flood.json, so the check
compares the digest with exactly the data this run saw.

Online calls have a total time limit (common.NVE_TIMEOUT) and one retry after
common.RETRY_DELAY seconds on HTTP 5xx or a timeout. Every NVE failure stops the run with
exit code 2 (common.EXIT_SERVICE) and a "...; no digest produced." message.
"""
import json
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

import common

API_DOC = "https://api.nve.no/doc/flomvarsling/"
# NVE times without an offset are Norwegian time. A fixed UTC+1 is at most an hour off in
# summer, which does not matter for the 24-hour freshness limit.
NORWAY = timezone(timedelta(hours=1))
TIME = re.compile(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.\d+)?(Z|[+-]\d\d:\d\d)?$")


def url():
    return f"{common.NVE_FLOOD_BASE}/api/Warning/County/{common.INNLANDET}/{common.LANG_NO}"


def _get(req):
    with urllib.request.urlopen(req, timeout=common.NVE_TIMEOUT) as resp:
        return resp.read()


def _download():
    req = urllib.request.Request(url(), headers={
        "User-Agent": common.USER_AGENT,
        "Accept": "application/json",
    })
    for attempt in (1, 2):
        last = attempt == 2
        try:
            return common.call_with_deadline(lambda: _get(req), common.NVE_TIMEOUT)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                common.stop(f"NVE API returned HTTP 404; the API version v1.0.10 may have been retired, "
                            f"check {API_DOC}; no digest produced.", common.EXIT_SERVICE)
            if e.code < 500 or last:
                common.stop(f"NVE API returned HTTP {e.code}; no digest produced.", common.EXIT_SERVICE)
            print(f"NVE API returned HTTP {e.code}; retrying once in {common.RETRY_DELAY} s")
        except (TimeoutError, urllib.error.URLError, OSError) as e:
            timed_out = isinstance(e, TimeoutError) or isinstance(getattr(e, "reason", None), TimeoutError)
            if not timed_out:
                # Name does not resolve, connection refused, ...: retrying will not help.
                reason = getattr(e, "reason", e)
                common.stop(f"NVE API unreachable ({reason}); no digest produced.", common.EXIT_SERVICE)
            if last:
                common.stop("NVE API timed out; no digest produced.", common.EXIT_SERVICE)
            print(f"NVE API timed out; retrying once in {common.RETRY_DELAY} s")
        time.sleep(common.RETRY_DELAY)


def fetch(offline=False, save_fixture=False, input_path=None):
    common.OUT.mkdir(exist_ok=True)
    if input_path:
        if not input_path.is_file():
            sys.exit(f"Input file not found: {input_path}; no digest produced.")
        raw = input_path.read_bytes()
    elif offline:
        if not common.FIXTURE_RAW.exists():
            sys.exit(f"Fixture not found: {common.FIXTURE_RAW}. Run once online with --save-fixture.")
        raw = common.FIXTURE_RAW.read_bytes()
    else:
        raw = _download()
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        code = common.EXIT_CHECK if (offline or input_path) else common.EXIT_SERVICE
        common.stop("NVE response is not valid JSON; no digest produced.", code)
    if not isinstance(data, list):
        code = common.EXIT_CHECK if (offline or input_path) else common.EXIT_SERVICE
        common.stop("Unexpected NVE response (not a list); no digest produced.", code)
    common.RAW_FILE.write_bytes(raw)
    if save_fixture and not offline and not input_path:
        common.FIXTURES.mkdir(exist_ok=True)
        shutil.copyfile(common.RAW_FILE, common.FIXTURE_RAW)
    return data


def _parse_time(text):
    m = TIME.match(str(text or ""))
    if not m:
        return None
    dt = datetime.fromisoformat(m.group(1))
    tz = m.group(2)
    if tz == "Z":
        return dt.replace(tzinfo=timezone.utc)
    if tz:
        sign = 1 if tz[0] == "+" else -1
        return dt.replace(tzinfo=timezone(sign * timedelta(hours=int(tz[1:3]), minutes=int(tz[4:6]))))
    return dt.replace(tzinfo=NORWAY)


def data_info(raw, live):
    """Where the data came from and when NVE published it (newest PublishTime, else CreatedTime)."""
    times = [t for t in (_parse_time(r.get("PublishTime") or r.get("CreatedTime")) for r in raw
                         if isinstance(r, dict)) if t]
    newest = max(times) if times else None
    when = newest.strftime("%d.%m.%Y kl. %H:%M") if newest else None
    note = None
    if not live:
        note = (f"Lagrede data fra {when}, ikke dagens varsler" if when
                else "Lagrede data (ukjent tidspunkt), ikke dagens varsler")
    return {"data_source": "live" if live else "saved",
            "data_published": newest.isoformat() if newest else None,
            "data_note": note}


if __name__ == "__main__":
    records = fetch(offline="--offline" in sys.argv, save_fixture="--save-fixture" in sys.argv)
    print(f"Fetched {len(records)} NVE flood record(s) for county {common.INNLANDET}")
