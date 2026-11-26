"""Stage 4 - Assemble: join code-copied facts with the model's summaries.

Writes out/digest.json (checked by eval/check_digest.py) and out/digest.md (for people).

Meaning check: a model summary that drops the colour word for its level, says the danger is
"utsatt" (postponed), "avlyst" (cancelled) or "ingen fare", is replaced by the template
summary built from the official fields. The digest then has summary_mode "fallback" and
lists the reason per warning. The model's original text stays in out/summaries.json.
"""
import json
import re
from datetime import datetime, timezone

import common
from normalise import LEVEL_NAMES
from summarise import template_summary

UTSATT = re.compile(r"\butsatt\b(?!\s+for\b)", re.IGNORECASE)   # "utsatt for" (exposed to) is fine
FORBIDDEN = ["avlyst", "ingen fare"]


def meaning_problem(summary, level):
    """Reason the summary may change the meaning of the warning, or None."""
    low = summary.lower()
    colour = LEVEL_NAMES.get(level)
    if colour and colour not in low:
        return f"missing colour word '{colour}' for level {level}"
    if UTSATT.search(summary):
        return "contains 'utsatt' (postponed) without 'utsatt for'"
    for word in FORBIDDEN:
        if word in low:
            return f"contains '{word}'"
    return None

NO_WARNINGS = "Ingen aktive flomvarsler (gult nivå eller høyere) for Innlandet i perioden."


def assemble(warnings, summaries, mode):
    fallback = []
    if mode in ("llm", "replay"):
        summaries = dict(summaries)
        for w in warnings:
            reason = meaning_problem(summaries.get(w["warning_id"], ""), w["danger_level"])
            if reason and w["warning_id"] in summaries:
                summaries[w["warning_id"]] = template_summary(w)
                fallback.append({"warning_id": w["warning_id"], "reason": reason})
        if fallback:
            mode = "fallback"
    entries = [{
        "source": w["source"],
        "warning_id": w["warning_id"],
        "type": w["type"],
        "danger_level": w["danger_level"],
        "area": w["area"],
        "valid_from": w["valid_from"],
        "valid_to": w["valid_to"],
        "summary_no": summaries.get(w["warning_id"], ""),
    } for w in warnings]
    digest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "region": "Innlandet (fylke 34)",
        "summary_mode": mode,
        "fallback": fallback,
        "attribution": common.ATTRIBUTION,
        "warnings": entries,
        "no_warnings_message": NO_WARNINGS if not entries else None,
    }
    common.DIGEST_JSON.write_text(json.dumps(digest, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [f"# Farevarsler for Innlandet ({digest['generated_at'][:10]})", ""]
    if not entries:
        lines.append(NO_WARNINGS)
    for e in entries:
        lines += [f"## Flom, nivå {e['danger_level']}: {e['area']}",
                  f"*Gyldig {e['valid_from']} til {e['valid_to']} (varsel-ID {e['warning_id']})*", "",
                  e["summary_no"], ""]
    lines += ["---"] + [f"_{a}_" for a in common.ATTRIBUTION]
    common.DIGEST_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return digest
