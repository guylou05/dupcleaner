import threading
import schedule
import time
import json
from db.database import get_setting, set_setting

_scheduler_thread: threading.Thread | None = None
_stop_event = threading.Event()


def get_schedule_config() -> dict:
    raw = get_setting("schedule_config", "{}")
    try:
        return json.loads(raw)
    except Exception:
        return {}


def save_schedule_config(config: dict):
    set_setting("schedule_config", json.dumps(config))


def _run_scheduled_scan(on_complete=None):
    from db.database import get_profiles
    config = get_schedule_config()
    profile_name = config.get("profile", "")
    profiles = get_profiles()
    profile = next((p for p in profiles if p["name"] == profile_name), None)
    if not profile:
        return

    import json as _json
    from db.models import ScanOptions
    from core.scanner import DuplicateScanner
    folders = _json.loads(profile["folders"])
    opts_dict = _json.loads(profile["options"])
    opts = ScanOptions.from_dict(folders, opts_dict)
    scanner = DuplicateScanner(opts)

    result_holder = []

    def on_done(groups, scanned, errors, cancelled):
        result_holder.append((groups, scanned, errors))
        if on_complete:
            on_complete(groups, scanned, errors)

    scanner.start(lambda *a: None, on_done)


def _scheduler_loop(on_complete=None):
    while not _stop_event.is_set():
        schedule.run_pending()
        time.sleep(30)


def start_scheduler(on_complete=None):
    global _scheduler_thread
    config = get_schedule_config()
    if not config.get("enabled"):
        return

    schedule.clear()
    freq = config.get("frequency", "weekly")
    day  = config.get("day", "sunday").lower()
    time_str = config.get("time", "02:00")

    job_func = lambda: _run_scheduled_scan(on_complete)

    if freq == "daily":
        schedule.every().day.at(time_str).do(job_func)
    elif freq == "weekly":
        getattr(schedule.every(), day).at(time_str).do(job_func)
    elif freq == "monthly":
        schedule.every(30).days.at(time_str).do(job_func)

    _stop_event.clear()
    _scheduler_thread = threading.Thread(target=_scheduler_loop, args=(on_complete,), daemon=True)
    _scheduler_thread.start()


def stop_scheduler():
    _stop_event.set()
    schedule.clear()
