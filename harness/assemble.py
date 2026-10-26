"""Stage 4 - Assemble: join code-copied facts with the model's summaries.

Writes out/digest.json (checked by eval/check_digest.py) and out/digest.md (for people).
"""
import json
from datetime import datetime, timezone

import common

NO_WARNINGS = "Ingen aktive flomvarsler (gult nivå eller høyere) for Innlandet i perioden."


def assemble(warnings, summaries, mode):
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
