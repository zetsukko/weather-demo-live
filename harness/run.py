"""Run the whole harness with one command: fetch -> normalise -> summarise -> assemble -> check.

  py harness/run.py                  live run (NVE + LLM if ANTHROPIC_API_KEY is set)
  py harness/run.py --offline        replay saved fixtures, no network
  py harness/run.py --save-fixture   live run that also refreshes fixtures/
  py harness/run.py --no-llm         skip the LLM, use template summaries

Exit code: 0 = digest produced and check passed; non-zero = no trustworthy digest.
"""
import subprocess
import sys

import common
from assemble import assemble
from fetch import fetch
from normalise import normalise
from summarise import summarise


def main(argv):
    offline = "--offline" in argv
    save = "--save-fixture" in argv
    no_llm = "--no-llm" in argv

    # Clear stale output so an old digest can never fake a PASS.
    for f in (common.RAW_FILE, common.NORMALISED_FILE, common.SUMMARIES_FILE,
              common.DIGEST_JSON, common.DIGEST_MD):
        f.unlink(missing_ok=True)

    raw = fetch(offline=offline, save_fixture=save)
    print(f"[1 fetch]     {len(raw)} raw record(s) ({'offline' if offline else 'live'})")

    warnings = normalise(raw)
    print(f"[2 normalise] {len(warnings)} active Innlandet warning(s)")
    if len(warnings) > common.MAX_WARNINGS:
        # Kill switch: an implausible number of warnings means something upstream is wrong.
        common.NORMALISED_FILE.unlink(missing_ok=True)
        sys.exit(f"KILL SWITCH: {len(warnings)} warnings > {common.MAX_WARNINGS}; no digest produced.")

    mode, summaries = summarise(warnings, offline=offline, no_llm=no_llm, save_fixture=save)
    print(f"[3 summarise] mode={mode}, {len(summaries)} summary(ies)")

    assemble(warnings, summaries, mode)
    print(f"[4 assemble]  wrote {common.DIGEST_JSON.relative_to(common.ROOT)} and digest.md")

    result = subprocess.run([sys.executable, str(common.ROOT / "eval" / "check_digest.py")])
    print(f"[5 check]     exit {result.returncode}")
    if result.returncode != 0:
        # A digest that fails the check must not be used.
        common.DIGEST_MD.unlink(missing_ok=True)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
