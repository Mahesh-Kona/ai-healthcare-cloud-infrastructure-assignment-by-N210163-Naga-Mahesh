"""
API service for the cloud infrastructure simulation.

This service is the public-facing entry point for the simulated healthcare
platform. It accepts appointment requests, stores state in the private
PostgreSQL database, and pushes asynchronous work into Redis for the worker
service. The implementation is intentionally simple, readable, and suitable
for local simulation and demonstration.
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, Any
from uuid import uuid4

import psycopg2
import redis
import requests
from flask import Flask, Response, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
APP_PORT = int(os.environ.get("PORT", 8080))
DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "healthcare")
DB_USER = os.environ.get("DB_USER", "healthcare")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
REDIS_HOST = os.environ.get("REDIS_HOST", "queue")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
EHR_BASE_URL = os.environ.get("EHR_BASE_URL", "http://ehr-mock:9000")
AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://ai-agent:9001")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------
REQUEST_COUNT = Counter("api_requests_total", "Total number of API requests")
ERROR_COUNT = Counter("api_errors_total", "Total number of API errors")
REQUEST_LATENCY = Histogram("api_request_latency_seconds", "API request latency")
JOB_ENQUEUED = Counter("api_jobs_enqueued_total", "Jobs pushed to Redis queue")


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------
def get_db_connection():
    """Create a database connection using environment values."""
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


def init_db():
    """Ensure the required tables exist when the service starts."""
    for attempt in range(15):
        try:
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS appointments (
                            id VARCHAR(64) PRIMARY KEY,
                            patient_id INTEGER NOT NULL,
                            action VARCHAR(64) NOT NULL,
                            details JSONB,
                            status VARCHAR(32) NOT NULL DEFAULT 'pending',
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )
                conn.commit()
                return
            finally:
                conn.close()
        except Exception as exc:
            app.logger.warning("Database not ready yet (attempt %s/15): %s", attempt + 1, exc)
            if attempt < 14:
                time.sleep(2)
    raise RuntimeError("Database initialization failed after waiting for PostgreSQL.")


def get_redis_client():
    """Return a Redis client for queueing jobs."""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def store_appointment(record: Dict[str, Any]):
    """Persist the appointment request in PostgreSQL."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO appointments (id, patient_id, action, details, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                """,
                (
                    record["id"],
                    record["patient_id"],
                    record["action"],
                    json.dumps(record.get("details", {})),
                    "queued",
                ),
            )
        conn.commit()
    finally:
        conn.close()


def push_job_to_queue(record: Dict[str, Any]):
    """Push the appointment job into the Redis queue."""
    client = get_redis_client()
    client.rpush("appointments", json.dumps(record))
    JOB_ENQUEUED.inc()


def is_valid_request(payload: Dict[str, Any]) -> bool:
    """Basic validation intentionally kept small and explicit."""
    required_fields = ["patient_id", "action"]
    return all(field in payload for field in required_fields)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    """Simple liveness check for health verification and deployment gating."""
    return jsonify({
        "status": "ok",
        "service": "api",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


@app.route("/metrics", methods=["GET"])
def metrics():
    """Expose Prometheus metrics so the monitoring stack can scrape this service."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/api/appointments", methods=["POST"])
def create_appointment():
    """
    Accept a simulated appointment request from the public API.

    The request is validated, stored in the private database, then added to the
    worker queue. This demonstrates a controlled public entry point with private
    backend processing.
    """
    REQUEST_COUNT.inc()
    start_time = datetime.utcnow()

    try:
        payload = request.get_json(force=True, silent=True) or {}
        if not is_valid_request(payload):
            ERROR_COUNT.inc()
            return jsonify({"error": "Invalid request payload"}), 400

        appointment_id = str(uuid4())
        record = {
            "id": appointment_id,
            "patient_id": int(payload["patient_id"]),
            "action": payload["action"],
            "details": payload.get("details", {}),
            "status": "queued",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

        store_appointment(record)
        push_job_to_queue(record)

        REQUEST_LATENCY.observe((datetime.utcnow() - start_time).total_seconds())
        return jsonify({
            "status": "accepted",
            "appointment_id": appointment_id,
            "message": "Appointment request accepted and queued for processing.",
        }), 202

    except Exception as exc:
        ERROR_COUNT.inc()
        app.logger.exception("Appointment creation failed: %s", exc)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/appointments", methods=["GET"])
def list_appointments():
    """Return recent appointments for demonstration and troubleshooting."""
    REQUEST_COUNT.inc()
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, patient_id, action, status, details, created_at
                FROM appointments
                ORDER BY created_at DESC
                LIMIT 20
                """
            )
            rows = cur.fetchall()

        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "patient_id": row[1],
                "action": row[2],
                "status": row[3],
                "details": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
            })

        return jsonify({"appointments": results}), 200
    except Exception as exc:
        ERROR_COUNT.inc()
        app.logger.exception("Failed to list appointments: %s", exc)
        return jsonify({"error": "Unable to fetch appointments"}), 500
    finally:
        conn.close()


@app.route("/api/health", methods=["GET"])
def api_service_health():
    """Health endpoint designed for lower-level API checks during deployment."""
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({"status": "healthy", "db": "reachable"}), 200
    except Exception as exc:
        app.logger.error("API health check failed: %s", exc)
        return jsonify({"status": "degraded", "db": "unreachable"}), 503


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=APP_PORT, debug=False)
