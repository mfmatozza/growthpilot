"""Thin wrapper around APScheduler so pipelines never import it directly
(docs/DECISIONS.md #5). Swapping to Celery + Redis later means writing one
new module with the same three functions, not touching any pipeline.

No jobs are registered yet — Module 3's weekly Lighthouse audit and
Module 4's weekly GEO check are the first real consumers of this, added
when those pipelines land per the build order.
"""

from collections.abc import Callable

from apscheduler.schedulers.background import BackgroundScheduler

_scheduler = BackgroundScheduler()
_started = False


def start() -> None:
    global _started
    if not _started:
        _scheduler.start()
        _started = True


def shutdown() -> None:
    global _started
    if _started:
        _scheduler.shutdown(wait=False)
        _started = False


def add_cron_job(func: Callable[[], None], *, job_id: str, day_of_week: str, hour: int) -> None:
    """Weekly-cadence jobs are all Module 3/4 needs for now; extend with
    more params if a pipeline needs finer-grained scheduling."""
    _scheduler.add_job(func, "cron", id=job_id, day_of_week=day_of_week, hour=hour, replace_existing=True)


def list_jobs() -> list[str]:
    return [job.id for job in _scheduler.get_jobs()]
