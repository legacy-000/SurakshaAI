import time
import logging
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional

from models.dto import ForecastRequestDTO, ForecastResultDTO

logger = logging.getLogger(__name__)


class ForecastScheduler:
    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ForecastScheduler, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        with self._lock:
            if getattr(self, "_initialized", False):
                return
            self._initialized = True
            self._jobs = {}
            self._history = {}
            self._thread = None
            self._stop_event = threading.Event()

    def schedule_job(self, name: str, request_dto: ForecastRequestDTO, interval_seconds: int):
        """Register/Schedule a forecasting job with a specific interval."""
        with self._lock:
            next_run = time.time() + interval_seconds
            self._jobs[name] = {
                "name": name,
                "request_dto": request_dto,
                "interval_seconds": interval_seconds,
                "last_run": None,
                "next_run": next_run,
                "status": "scheduled",
            }
            logger.info("Scheduled job '%s' with interval %ds (next run at %s)",
                        name, interval_seconds, datetime.fromtimestamp(next_run).isoformat())

    def start(self):
        """Start the background scheduler thread loop."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                logger.warning("ForecastScheduler is already running.")
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True, name="ForecastSchedulerThread")
            self._thread.start()
            logger.info("ForecastScheduler background thread started.")

    def stop(self):
        """Stop the background scheduler thread loop."""
        with self._lock:
            if self._thread is None:
                logger.warning("ForecastScheduler is not running.")
                return
            self._stop_event.set()
            # Join thread briefly to allow graceful shutdown
            self._thread.join(timeout=1.0)
            self._thread = None
            logger.info("ForecastScheduler background thread stopped.")

    def get_active_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Return a copy of all active registered jobs."""
        with self._lock:
            # Create a safe copy of jobs details
            return {
                name: {
                    "name": job["name"],
                    "request_dto": job["request_dto"],
                    "interval_seconds": job["interval_seconds"],
                    "last_run": job["last_run"],
                    "next_run": job["next_run"],
                    "status": job["status"],
                }
                for name, job in self._jobs.items()
            }

    def trigger_job_now(self, name: str) -> Optional[ForecastResultDTO]:
        """Trigger a registered job immediately and return the result."""
        # Find job configuration
        with self._lock:
            job = self._jobs.get(name)
            if not job:
                logger.error("Job '%s' not found for immediate execution.", name)
                raise ValueError(f"Job '{name}' not found.")

            # Temporarily mark as running
            job["status"]
            job["status"] = "running"
            request_dto = job["request_dto"]
            interval = job["interval_seconds"]

        # Run execution outside of the lock to prevent blocking database operations
        hist_record = self._execute_job(name, request_dto)

        # Update job stats and history
        with self._lock:
            if name in self._jobs:
                self._jobs[name]["last_run"] = time.time()
                # Recalculate next run from now
                self._jobs[name]["next_run"] = time.time() + interval
                self._jobs[name]["status"] = "scheduled"

            self._history.setdefault(name, []).append(hist_record)
            if len(self._history[name]) > 100:
                self._history[name].pop(0)

        if hist_record["status"] == "success":
            return hist_record["result"]
        else:
            raise RuntimeError(f"Job execution failed: {hist_record['error']}")

    def get_job_history(self, name: str) -> List[Dict[str, Any]]:
        """Return a list of execution history for the given job."""
        with self._lock:
            return list(self._history.get(name, []))

    def _execute_job(self, name: str, request_dto: ForecastRequestDTO) -> Dict[str, Any]:
        """Execute a job and return a history record dict."""
        from forecast.forecaster import build_forecaster
        forecaster = build_forecaster()

        db = None
        try:
            from common.db.datastore_client import DatastoreClient
            db = DatastoreClient()
        except Exception:
            pass

        try:
            result = forecaster.forecast(request_dto, db=db)
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "result": result,
                "error": None
            }
        except Exception as e:
            logger.exception("Error executing forecast job '%s'", name)
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "failed",
                "result": None,
                "error": str(e)
            }

    def _run_loop(self):
        """Internal runner loop for checking and executing scheduled jobs."""
        while not self._stop_event.is_set():
            now = time.time()
            jobs_to_run = []

            with self._lock:
                for name, job in self._jobs.items():
                    if job["status"] == "scheduled" and now >= job["next_run"]:
                        job["status"] = "running"
                        jobs_to_run.append((name, job["request_dto"], job["interval_seconds"]))

            for name, request_dto, interval in jobs_to_run:
                if self._stop_event.is_set():
                    break

                hist_record = self._execute_job(name, request_dto)

                with self._lock:
                    if name in self._jobs:
                        self._jobs[name]["last_run"] = time.time()
                        self._jobs[name]["next_run"] = time.time() + interval
                        self._jobs[name]["status"] = "scheduled"

                    self._history.setdefault(name, []).append(hist_record)
                    if len(self._history[name]) > 100:
                        self._history[name].pop(0)

            # Sleep briefly to avoid busy-waiting
            time.sleep(0.5)
