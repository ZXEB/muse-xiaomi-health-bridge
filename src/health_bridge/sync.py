from __future__ import annotations

import argparse
import logging
import time
from datetime import date, datetime, timedelta

from .config import Settings, get_settings
from .db import Database
from .source import DOMAINS, AuthExpiredError, MiFitnessSource

log = logging.getLogger("health_bridge.sync")

CHUNK_DAYS = 31


def today_local(settings: Settings) -> date:
    return datetime.now(settings.tzinfo).date()


def iter_chunks(start: date, end: date, size: int = CHUNK_DAYS):
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=size - 1), end)
        yield cursor, chunk_end
        cursor = chunk_end + timedelta(days=1)


def run_sync(
    settings: Settings,
    db: Database,
    source: MiFitnessSource,
    days: int,
    today: date | None = None,
) -> dict:
    days = max(1, min(int(days), 3660))
    end = today or today_local(settings)
    start = end - timedelta(days=days - 1)
    errors: list[str] = []
    chunks = 0

    for chunk_start, chunk_end in iter_chunks(start, end):
        chunks += 1
        for domain, fn in DOMAINS.items():
            try:
                rows = fn(source, chunk_start.isoformat(), chunk_end.isoformat())
                db.upsert_daily(rows)
                db.set_sync_state(domain, chunk_end.isoformat(), None)
            except AuthExpiredError:
                raise
            except Exception as exc:  # noqa: BLE001 - report and continue
                message = f"{domain} {chunk_start}..{chunk_end}: {exc}"[:500]
                errors.append(message)
                db.set_sync_state(domain, None, message)
                log.warning("sync failed: %s", message)

        try:
            rows = source.workouts(chunk_start.isoformat(), chunk_end.isoformat())
            db.upsert_workouts(rows)
            db.set_sync_state("workouts", chunk_end.isoformat(), None)
        except AuthExpiredError:
            raise
        except Exception as exc:  # noqa: BLE001
            message = f"workouts {chunk_start}..{chunk_end}: {exc}"[:500]
            errors.append(message)
            db.set_sync_state("workouts", None, message)
            log.warning("sync failed: %s", message)

    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "days": (end - start).days + 1,
        "chunks": chunks,
        "errors": errors,
    }


def daemon(settings: Settings, db: Database, source: MiFitnessSource) -> None:
    if db.latest_date() is None:
        log.info("no data yet; running initial backfill of %s days", settings.backfill_days)
        try:
            run_sync(settings, db, source, settings.backfill_days)
        except AuthExpiredError:
            log.error("mifit session expired; waiting for a fresh `mifit login`")
    else:
        log.info("startup incremental sync (7 days)")
        try:
            run_sync(settings, db, source, 7)
        except AuthExpiredError:
            log.error("mifit session expired")

    while True:
        now = datetime.now(settings.tzinfo)
        target = now.replace(
            hour=settings.sync_hour,
            minute=settings.sync_minute,
            second=0,
            microsecond=0,
        )
        if target <= now:
            target += timedelta(days=1)
        sleep_for = (target - now).total_seconds()
        log.info("next sync at %s (%.0f s)", target.isoformat(timespec="minutes"), sleep_for)
        time.sleep(sleep_for)
        try:
            result = run_sync(settings, db, source, 7)
            log.info("scheduled sync done: %s", result)
        except AuthExpiredError:
            log.error("mifit session expired; re-login required")
        except Exception:  # noqa: BLE001
            log.exception("scheduled sync failed")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Sync Mi Fitness data into the local SQLite store.")
    parser.add_argument("--days", type=int, default=7, help="how many days back to sync")
    parser.add_argument("--daemon", action="store_true", help="run forever, syncing daily at 04:30")
    parser.add_argument("--backfill", action="store_true", help="sync BACKFILL_DAYS days instead of --days")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    settings = get_settings()
    db = Database(settings.db_path)
    source = MiFitnessSource(settings)

    if args.daemon:
        daemon(settings, db, source)
        return

    days = settings.backfill_days if args.backfill else args.days
    result = run_sync(settings, db, source, days)
    print(result)


if __name__ == "__main__":
    main()
