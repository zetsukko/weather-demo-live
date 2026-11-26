"""Stage 1 - Fetch: NVE flood warnings for Innlandet (county 34).

Online:  GET {base}/api/Warning/County/34/1  (today, tomorrow and the day after)
Offline: replay fixtures/nve_flood_innlandet.json
Input:   --input <file> replays any saved NVE response (used by eval/run_eval.py)
Always writes the raw response that was used to out/raw_nve_flood.json, so the check
compares the digest with exactly the data this run saw.
"""
import json
import shutil
import sys
import urllib.error
import urllib.request

import common


def url():
    return f"{common.NVE_FLOOD_BASE}/api/Warning/County/{common.INNLANDET}/{common.LANG_NO}"


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
        req = urllib.request.Request(url(), headers={
            "User-Agent": common.USER_AGENT,
            "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as e:
            # Dependency failure: stop instead of producing a partial digest.
            sys.exit(f"NVE API returned HTTP {e.code}; no digest produced.")
        except urllib.error.URLError as e:
            sys.exit(f"NVE API unreachable ({e.reason}); no digest produced. Try --offline.")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit("NVE response is not valid JSON; no digest produced.")
    if not isinstance(data, list):
        sys.exit("Unexpected NVE response (not a list); no digest produced.")
    common.RAW_FILE.write_bytes(raw)
    if save_fixture and not offline and not input_path:
        common.FIXTURES.mkdir(exist_ok=True)
        shutil.copyfile(common.RAW_FILE, common.FIXTURE_RAW)
    return data


if __name__ == "__main__":
    records = fetch(offline="--offline" in sys.argv, save_fixture="--save-fixture" in sys.argv)
    print(f"Fetched {len(records)} NVE flood record(s) for county {common.INNLANDET}")
