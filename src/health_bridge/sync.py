from __future__ import annotations

import argparse
import logging
import os
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path

from .config import Settings, get_settings
from .db import Database
from .source import DOMAINS, AuthExpiredError, MiFitnessSource

log = logging.getLogger("health_bridge.sync")

CHUNK_DAYS = 31
DEFAULT_SYNC_DAYS = 7
LOCK_STALE_SECONDS = 900


class SyncBusyError(RuntimeError):
    """Another process is already syncing; retry shortly instead of queuing up."""


@contextmanager
def sync_lock(db_path: str):
    """Cross-process guard so the daemon and an MCP/REST trigger never overlap.

    A plain O_EXCL lock file works on Windows and Linux; a lock older than
    LOCK_STALE_SECONDS is treated as a crashed run and removed.
    """

    path = Path(db_path).parent / "sync.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            try:
                age = time.time() - path.stat().st_mtime
            except OSError:
                continue
            if age > LOCK_STALE_SECONDS:
                try:
                    path.unlink()
                except OSError:
                    pass
                continue
            raise SyncBusyError("a sync is already running; try again in a minute")
    try:
        yield
    finally:
        try:
            path.unlink()
        except OSError:
            pass


def read_schedule(db: Database, settings: Settings) -> dict:
    """Effective auto-sync schedule: DB overrides survive restarts and UI edits."""

    def _int(key: str, default: int) -> int:
        raw = db.get_setting(key)
        if raw is None:
            return default
        try:
            return int(raw)
        except (TypeError, ValueError):
            return default

    return {
        "interval_minutes": max(0, _int("sync_interval_minutes", 0)),
        "hour": min(23, max(0, _int("sync_hour", settings.sync_hour))),
        "minute": min(59, max(0, _int("sync_minute", settings.sync_minute))),
        "days": min(31, max(1, _int("sync_days", DEFAULT_SYNC_DAYS))),
    }


def compute_next_run(schedule: dict, now: datetime, last_run: datetime | None) -> datetime:
    if schedule["interval_minutes"] > 0:
        if last_run is None:
            return now
        return last_run + timedelta(minutes=schedule["interval_minutes"])
    target = now.replace(hour=schedule["hour"], minute=schedule["minute"], second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


def _record_run(db: Database, settings: Settings) -> None:
    db.set_setting("last_auto_sync_at", datetime.now(settings.tzinfo).isoformat())



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

    with sync_lock(settings.db_path):
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
    schedule = read_schedule(db, settings)
    if db.latest_date() is None:
        log.info("no data yet; running initial backfill of %s days", settings.backfill_days)
        try:
            run_sync(settings, db, source, settings.backfill_days)
        except AuthExpiredError:
            log.error("mifit session expired; waiting for a fresh `mifit login`")
        except SyncBusyError:
            log.warning("another sync is running; skipping the startup backfill")
    else:
        log.info("startup incremental sync (%s days)", schedule["days"])
        try:
            run_sync(settings, db, source, schedule["days"])
        except AuthExpiredError:
            log.error("mifit session expired")
        except SyncBusyError:
            log.warning("another sync is running; skipping the startup sync")
    _record_run(db, settings)

    logged_target: datetime | None = None
    while True:
        schedule = read_schedule(db, settings)
        now = datetime.now(settings.tzinfo)
        raw_last = db.get_setting("last_auto_sync_at")
        last_run = datetime.fromisoformat(raw_last) if raw_last else None
        target = compute_next_run(schedule, now, last_run)
        if target != logged_target:
            log.info("next automatic sync at %s", target.isoformat(timespec="minutes"))
            logged_target = target
        wait = (target - now).total_seconds()
        if wait > 0:
            # Wake at least every 30 s so schedule edits from the admin UI apply quickly.
            time.sleep(min(wait, 30))
            continue
        try:
            result = run_sync(settings, db, source, schedule["days"])
            log.info("scheduled sync done: %s", result)
        except AuthExpiredError:
            log.error("mifit session expired; re-login required")
        except Exception:  # noqa: BLE001
            log.exception("scheduled sync failed")
        _record_run(db, settings)


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
