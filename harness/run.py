"""Run the whole harness with one command: fetch -> normalise -> summarise -> assemble -> check.

  py harness/run.py                  live run (NVE + LLM if LLM_PROVIDER=ollama or ANTHROPIC_API_KEY)
  py harness/run.py --offline        replay saved fixtures, no network
  py harness/run.py --save-fixture   live run that also refreshes fixtures/
  py harness/run.py --no-llm         skip the LLM, use template summaries
  py harness/run.py --input <file>   use a saved NVE response instead of the API/fixture
                                     (combine with --no-llm for fast deterministic runs)

Offline and --input digests are marked "Lagrede data fra <tid>, ikke dagens varsler".
If the local model (Ollama) is down or times out, the run uses template summaries
(summary_mode "fallback") and still produces a checked digest.

Exit codes:
  0  digest produced and both checks passed (eval/check_digest.py, eval/check_freshness.py)
  1  no trustworthy digest: a check failed, or the input data was rejected (stage 2)
  2  an outside service failed: NVE (unreachable, HTTP error, timeout, not JSON) or the Anthropic API
"""
import subprocess
import sys
from pathlib import Path

import common
from assemble import assemble
from fetch import data_info, fetch
from normalise import normalise
from summarise import summarise

CHECKS = ("check_digest.py", "check_freshness.py")


def main(argv):
    offline = "--offline" in argv
    save = "--save-fixture" in argv
    no_llm = "--no-llm" in argv
    input_path = None
    if "--input" in argv:
        i = argv.index("--input")
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            sys.exit("--input needs a file path, e.g. --input eval/cases/real_2610/nve.json")
        input_path = Path(argv[i + 1]).resolve()

    # Clear stale output so an old digest can never fake a PASS.
    for f in (common.RAW_FILE, common.NORMALISED_FILE, common.SUMMARIES_FILE,
              common.DIGEST_JSON, common.DIGEST_MD):
        f.unlink(missing_ok=True)

    raw = fetch(offline=offline, save_fixture=save, input_path=input_path)
    shown = input_path.relative_to(common.ROOT).as_posix() if input_path and input_path.is_relative_to(common.ROOT) else (input_path.name if input_path else "")
    source = f"input={shown}" if input_path else ("offline" if offline else "live")
    info = data_info(raw, live=not (offline or input_path))
    print(f"[1 fetch]     {len(raw)} raw record(s) ({source})")
    if info["data_note"]:
        print(f"              {info['data_note']}")

    warnings = normalise(raw)
    print(f"[2 normalise] {len(warnings)} active Innlandet warning(s)")
    if len(warnings) > common.MAX_WARNINGS:
        # Kill switch: an implausible number of warnings means something upstream is wrong.
        common.NORMALISED_FILE.unlink(missing_ok=True)
        sys.exit(f"KILL SWITCH: {len(warnings)} warnings > {common.MAX_WARNINGS}; no digest produced.")

    mode, summaries, fallback = summarise(warnings, offline=offline, no_llm=no_llm, save_fixture=save)
    print(f"[3 summarise] mode={mode}, {len(summaries)} summary(ies)")

    digest = assemble(warnings, summaries, mode, fallback, info)
    print(f"[4 assemble]  wrote {common.DIGEST_JSON.relative_to(common.ROOT)} and digest.md")
    for f in digest["fallback"]:
        print(f"              fallback to template for {f['warning_id']}: {f['reason']}")

    code = common.EXIT_OK
    for check in CHECKS:
        result = subprocess.run([sys.executable, str(common.ROOT / "eval" / check)])
        if result.returncode != 0:
            code = common.EXIT_CHECK
    print(f"[5 check]     exit {code}")
    if code != common.EXIT_OK:
        # A digest that fails a check must not be used.
        common.DIGEST_MD.unlink(missing_ok=True)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
