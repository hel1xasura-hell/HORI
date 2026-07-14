"""Wrapper around APScheduler's AsyncIOScheduler for background job management."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Awaitable, Callable

from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.base import BaseTrigger

from core.exceptions import SchedulerError
from core.logger import get_logger

logger = get_logger(__name__)


class BotScheduler:
    """Thin, application-specific wrapper around `AsyncIOScheduler`.

    This class centralizes scheduler lifecycle management (start/shutdown) and
    provides a single method for registering background jobs such as flood
    counter resets, scheduled unmutes, and federation cache refreshes.
    """

    def __init__(self) -> None:
        """Initialize the underlying AsyncIOScheduler instance without starting it."""
        self._scheduler = AsyncIOScheduler(timezone="UTC")
        self._started = False

    def start(self) -> None:
        """Start the scheduler.

        Raises:
            SchedulerError: If the scheduler is already running.
        """
        if self._started:
            raise SchedulerError("Scheduler is already running.")
        self._scheduler.start()
        self._started = True
        logger.info("Scheduler started successfully.")

    def shutdown(self, wait: bool = True) -> None:
        """Shut down the scheduler and stop executing further jobs.

        Args:
            wait: Whether to wait for currently executing jobs to finish.

        Raises:
            SchedulerError: If the scheduler is not currently running.
        """
        if not self._started:
            raise SchedulerError("Scheduler is not running.")
        self._scheduler.shutdown(wait=wait)
        self._started = False
        logger.info("Scheduler shut down successfully.")

    def add_job(
        self,
        func: Callable[..., Awaitable[Any]],
        trigger: str | BaseTrigger = "date",
        job_id: str | None = None,
        run_date: datetime | None = None,
        replace_existing: bool = True,
        **trigger_args: Any,
    ) -> Job:
        """Schedule a coroutine function to run according to a trigger.

        Args:
            func: The coroutine function to execute.
            trigger: The trigger type ("date", "interval", "cron") or a
                `BaseTrigger` instance.
            job_id: An optional unique identifier for the job, used to prevent
                duplicate scheduling and to allow later removal.
            run_date: The datetime to run at, when `trigger` is "date".
            replace_existing: Whether to replace an existing job with the same ID.
            **trigger_args: Additional keyword arguments forwarded to the trigger
                (e.g. `seconds=30` for an interval trigger).

        Returns:
            The scheduled `Job` instance.

        Raises:
            SchedulerError: If the scheduler has not been started yet.
        """
        if not self._started:
            raise SchedulerError("Cannot schedule a job before the scheduler has started.")

        if trigger == "date" and run_date is not None:
            trigger_args.setdefault("run_date", run_date)

        job = self._scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            replace_existing=replace_existing,
            **trigger_args,
        )
        logger.debug("Scheduled job '%s' with trigger '%s'.", job.id, trigger)
        return job

    def remove_job(self, job_id: str) -> None:
        """Remove a previously scheduled job by ID, ignoring if it no longer exists.

        Args:
            job_id: The identifier of the job to remove.
        """
        try:
            self._scheduler.remove_job(job_id)
            logger.debug("Removed scheduled job '%s'.", job_id)
        except Exception:  # noqa: BLE001 - APScheduler raises a generic JobLookupError
            logger.debug("Job '%s' was not found; nothing to remove.", job_id)

    @property
    def is_running(self) -> bool:
        """Return whether the scheduler is currently running."""
        return self._started


_scheduler_instance = BotScheduler()


def get_scheduler() -> BotScheduler:
    """Return the process-wide `BotScheduler` singleton.

    Returns:
        The shared `BotScheduler` instance.
    """
    return _scheduler_instance
