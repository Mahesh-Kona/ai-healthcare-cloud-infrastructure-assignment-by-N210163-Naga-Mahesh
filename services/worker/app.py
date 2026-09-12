"""
Background worker for asynchronous healthcare processing.

This worker consumes jobs from Redis and simulates the background processing
work expected in an AI-driven healthcare platform. It demonstrates queue depth,
processing latency, retry handling, and failure recovery in a local environment.
"""

import json
import os
import time
from datetime import datetime
from threading import Thread

import psycopg2
import redis
import requests
from flask import Flask, Response, jsonify
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

APP_PORT = int(os.environ.get("PORT", 9002))
REDIS_HOST = os.environ.get("REDIS_HOST", "queue")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "healthcare")
DB_USER = os.environ.get("DB_USER", "healthcare")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
EHR_BASE_URL = os.environ.get("EHR_BASE_URL", "http://ehr-mock:9000")
AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://ai-agent:9001")

app = Flask(__name__)

QUEUE_DEPTH = Gauge("worker_queue_depth", "Current queue depth")
PROCESSED_COUNT = Counter("worker_jobs_processed_total", "Jobs completed by the worker")
FAILED_COUNT = Counter("worker_jobs_failed_total", "Jobs failed by the worker")
JOB_LATENCY = Histogram("worker_job_latency_seconds", "Worker job latency")
WORKER_RESTARTS = Counter("worker_restarts_total", "Worker restart count")


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------
def get_db_connection():
    last_error = None
    for attempt in range(15):
        try:
            return psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=3,
            )
        except psycopg2.OperationalError as exc:
            last_error = exc
            if attempt < 14:
                time.sleep(2)
    raise last_error


def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def update_appointment_status(appointment_id: str, status: str):
    """Update the database row for the appointment task."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE appointments SET status = %s, updated_at = NOW() WHERE id = %s",
                (status, appointment_id),
            )
        conn.commit()
    finally:
        conn.close()


def call_ai_service(payload: dict):
    """Send the request to the mock AI service."""
    response = requests.post(f"{AI_SERVICE_URL}/process", json=payload, timeout=5)
    response.raise_for_status()
    return response.json()


def call_ehr_service(payload: dict):
    """Call the mock external EHR service. This intentionally allows failure modes."""
    response = requests.post(f"{EHR_BASE_URL}/sync", json=payload, timeout=5)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Worker loop
# ---------------------------------------------------------------------------
def process_job(job: dict):
    """Process a single queued job and simulate realistic steps."""
    appointment_id = job.get("id")
    patient_id = job.get("patient_id", 0)

    # Simulate the worker doing real asynchronous work.
    start_time = time.time()

    # Step 1: consult the AI/agent mock.
    ai_response = call_ai_service({
        "patient_id": patient_id,
        "appointment_id": appointment_id,
        "details": job.get("details", {}),
    })

    # Step 2: integrate with the mock EHR service.
    ehr_response = call_ehr_service({
        "appointment_id": appointment_id,
        "patient_id": patient_id,
        "action": job.get("action", "create_appointment"),
        "ai_decision": ai_response,
    })

    # Step 3: update local state to reflect success.
    update_appointment_status(appointment_id, "processed")

    elapsed = time.time() - start_time
    JOB_LATENCY.observe(elapsed)
    PROCESSED_COUNT.inc()

    return {
        "appointment_id": appointment_id,
        "ai_response": ai_response,
        "ehr_response": ehr_response,
        "elapsed": elapsed,
    }


# ---------------------------------------------------------------------------
# Health and metrics
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "worker",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


@app.route("/metrics", methods=["GET"])
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/status", methods=["GET"])
def status():
    """Return worker operational status for operators and scripts."""
    client = get_redis_client()
    queue_depth = int(client.llen("appointments") or 0)
    QUEUE_DEPTH.set(queue_depth)
    return jsonify({
        "service": "worker",
        "queue_depth": queue_depth,
        "processed_jobs": PROCESSED_COUNT._value.get(),
        "failed_jobs": FAILED_COUNT._value.get(),
    })


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def run_worker_loop():
    """
    Poll Redis for new jobs and process them one by one.

    This loop deliberately keeps the worker simple so that failure behavior can
    be demonstrated clearly during the assessment.
    """
    client = get_redis_client()

    while True:
        # Show current queue depth with a gauge.
        queue_depth = int(client.llen("appointments") or 0)
        QUEUE_DEPTH.set(queue_depth)

        if queue_depth == 0:
            time.sleep(1)
            continue

        raw_job = client.lpop("appointments")
        if not raw_job:
            continue

        job = json.loads(raw_job)

        try:
            process_job(job)
        except Exception as exc:
            FAILED_COUNT.inc()
            update_appointment_status(job.get("id"), "failed")
            print(f"Worker failed to process {job.get('id')}: {exc}")

            # Requeue only if the job is not lost. This demonstrates retry logic
            # in a simple, observable way.
            client.rpush("appointments", json.dumps(job))

            # Sleep briefly to allow operators to observe the failure state.
            time.sleep(2)


if __name__ == "__main__":
    WORKER_RESTARTS.inc()
    worker_thread = Thread(target=run_worker_loop, daemon=True)
    worker_thread.start()
    app.run(host="0.0.0.0", port=APP_PORT, debug=False, threaded=True)
