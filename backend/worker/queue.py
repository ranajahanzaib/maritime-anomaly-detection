import threading
import queue
import time
import uuid
import traceback
from typing import Callable, Dict, Any, Optional

from backend.app.db.session import SessionLocal
from backend.app.models.entities import JobRecord


class BackgroundJobWorker:
    """
    Dedicated local background task worker.
    Runs asynchronous tasks (dataset ingestion, model training, batch detection, evaluations)
    with safe claiming, status tracking, logging, error handling, and progress updates.
    """
    def __init__(self, poll_interval: float = 1.0):
        self.poll_interval = poll_interval
        self._task_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None
        self._active_job_id = None

    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="vessel-worker")
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def submit_job(
        self,
        job_type: str,
        task_fn: Callable[..., Any],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        job_id = f"job_{job_type.lower()}_{uuid.uuid4().hex[:8]}"
        db = SessionLocal()
        try:
            job_rec = JobRecord(
                id=job_id,
                job_type=job_type,
                status="PENDING",
                progress=0.0,
                parameters=parameters or {},
                log_messages=[f"Job {job_id} submitted."],
            )
            db.add(job_rec)
            db.commit()
        finally:
            db.close()

        self._task_queue.put((job_id, task_fn, parameters or {}))
        return job_id

    def _worker_loop(self):
        while not self._stop_event.is_set():
            try:
                job_id, task_fn, params = self._task_queue.get(timeout=self.poll_interval)
            except queue.Empty:
                continue

            self._active_job_id = job_id
            self._update_job_status(job_id, "RUNNING", progress=0.05, log="Worker claimed task.")

            try:
                def progress_cb(pct: float, msg: str = ""):
                    self._update_job_status(job_id, "RUNNING", progress=pct, log=msg)

                result = task_fn(progress_callback=progress_cb, **params)
                self._update_job_status(
                    job_id, "COMPLETED", progress=1.0, log="Task completed successfully.", result=result
                )
            except Exception as e:
                err_msg = traceback.format_exc()
                self._update_job_status(
                    job_id, "FAILED", progress=0.0, log=f"Error: {str(e)}", error=err_msg
                )
            finally:
                self._active_job_id = None
                self._task_queue.task_done()

    def _update_job_status(
        self,
        job_id: str,
        status: str,
        progress: Optional[float] = None,
        log: Optional[str] = None,
        error: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
    ):
        db = SessionLocal()
        try:
            job = db.query(JobRecord).filter(JobRecord.id == job_id).first()
            if job:
                job.status = status
                if progress is not None:
                    job.progress = round(progress, 2)
                if log:
                    logs = list(job.log_messages or [])
                    logs.append(f"[{time.strftime('%H:%M:%S')}] {log}")
                    job.log_messages = logs
                if error:
                    job.error_message = error
                if result:
                    job.result = result
                db.commit()
        finally:
            db.close()


worker = BackgroundJobWorker()
