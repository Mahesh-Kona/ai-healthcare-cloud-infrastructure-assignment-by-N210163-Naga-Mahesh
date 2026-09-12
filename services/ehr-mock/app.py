"""
Mock external EHR system for infrastructure simulation.

This service intentionally exposes realistic failure modes for the assessment,
including success, slow responses, timeouts, temporary failures, and auth
failures. It is used to demonstrate dependency-aware resilience and failure
handling.
"""

import os
import random
import time
from datetime import datetime

from flask import Flask, Response, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

APP_PORT = int(os.environ.get("PORT", 9000))

app = Flask(__name__)

REQUEST_COUNT = Counter("ehr_mock_requests_total", "Total EHR mock requests")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "ehr-mock",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


@app.route("/metrics", methods=["GET"])
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/sync", methods=["POST"])
def sync_record():
    """
    Simulate several external-system outcomes.

    The outcome is chosen randomly to allow the evaluator to observe handling for:
    - success
    - slow response
    - timeout
    - temporary failure
    - authentication failure
    - unavailable service
    """
    REQUEST_COUNT.inc()

    payload = request.get_json(force=True, silent=True) or {}
    choice = random.choice(["success", "slow", "timeout", "temporary_failure", "auth_failure", "unavailable"])

    if choice == "slow":
        time.sleep(4)
        return jsonify({"status": "delayed", "message": "EHR responded slowly."}), 200

    if choice == "timeout":
        time.sleep(7)
        return jsonify({"status": "timeout", "message": "EHR timed out."}), 504

    if choice == "temporary_failure":
        return jsonify({"status": "retryable_error", "message": "Temporary EHR failure."}), 503

    if choice == "auth_failure":
        return jsonify({"status": "unauthorized", "message": "Authentication failed."}), 401

    if choice == "unavailable":
        return jsonify({"status": "unavailable", "message": "EHR unavailable."}), 503

    return jsonify({
        "status": "success",
        "message": "EHR synchronization completed.",
        "patient_id": payload.get("patient_id"),
        "appointment_id": payload.get("appointment_id"),
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT, debug=False)
