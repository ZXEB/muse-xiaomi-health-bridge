from __future__ import annotations

from typing import Any


# Mi Fitness exposes stage minutes but no explicit session type in its daily report.
# A long unstaged session is kept separate instead of being labeled a nap.
NAP_LIMIT_MIN = 180


def _has_sleep_stages(session: dict[str, Any]) -> bool:
    return any((session.get(stage) or 0) > 0 for stage in ("deep_min", "light_min", "rem_min"))


def describe_sleep_day(day: str, total_min: int, sessions: list[dict[str, Any]]) -> dict[str, Any]:
    main = max((s for s in sessions if _has_sleep_stages(s)), key=lambda s: s["asleep_min"], default=None)
    naps = [s for s in sessions if not _has_sleep_stages(s) and s["asleep_min"] < NAP_LIMIT_MIN]
    other = [s for s in sessions if s is not main and s not in naps]
    if not sessions:
        detail_status = "missing"
    elif sum(s["asleep_min"] for s in sessions) == total_min:
        detail_status = "complete"
    else:
        detail_status = "partial"
    return {
        "date": day,
        "main": main,
        "naps": naps,
        "other": other,
        "nap_min": sum(s["asleep_min"] for s in naps) if naps or detail_status == "complete" else None,
        "total_min": total_min,
        "detail_status": detail_status,
    }
