"""
FSMScheduler — APScheduler-based timed side-effects.

Primary use case: alert when a sensor stays HORS_SERVICE longer than the
configured threshold (default 24h, overridable via HORS_SERVICE_ALERT_DELAY_SECONDS).
"""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore

from config.settings import get_settings
from fsm.persistence import FSMStateRepository


class FSMScheduler:

    def __init__(self, repo: FSMStateRepository | None = None):
        self._repo = repo or FSMStateRepository()
        self._scheduler = BackgroundScheduler(
            jobstores={"default": MemoryJobStore()},
            timezone="UTC",
        )
        self._started = False

    def start(self) -> None:
        if not self._started:
            self._scheduler.start()
            self._started = True

    def shutdown(self) -> None:
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False

    # ──────────────────────────────────────────────────────────

    def schedule_hors_service_alert(self, sensor_id: int) -> None:
        """
        Schedule an alert to fire if the sensor is still HORS_SERVICE
        after HORS_SERVICE_ALERT_DELAY_SECONDS.
        """
        delay = get_settings().hors_service_alert_delay_seconds
        run_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        job_id = f"hors_service_{sensor_id}"

        self._scheduler.add_job(
            func=self._check_and_alert,
            trigger="date",
            run_date=run_at,
            args=[sensor_id],
            id=job_id,
            replace_existing=True,
        )

    def cancel_hors_service_alert(self, sensor_id: int) -> None:
        """Cancel the scheduled alert (e.g., sensor was repaired)."""
        job_id = f"hors_service_{sensor_id}"
        try:
            self._scheduler.remove_job(job_id)
        except Exception:
            pass

    def _check_and_alert(self, sensor_id: int) -> None:
        state = self._repo.get_state("capteur", sensor_id)
        if state == "HORS_SERVICE":
            self._persist_critical_alert(sensor_id)

    def _persist_critical_alert(self, sensor_id: int) -> None:
        try:
            from database.connection import execute_query
            execute_query(
                """INSERT INTO alertes (type, entity_type, entity_id, message, severity)
                   VALUES ('hors_service_prolongé', 'capteur', :id, :msg, 'CRITICAL')""",
                {
                    "id": sensor_id,
                    "msg": (
                        f"Capteur {sensor_id} est HORS SERVICE depuis plus de "
                        f"{get_settings().hors_service_alert_delay_seconds // 3600}h — "
                        f"intervention urgente requise."
                    ),
                },
            )
        except Exception:
            pass  # Scheduler is best-effort; DB may not be available in all test contexts
