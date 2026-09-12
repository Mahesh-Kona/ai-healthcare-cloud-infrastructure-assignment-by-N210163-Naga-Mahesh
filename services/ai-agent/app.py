"""
AI/agent mock service for the cloud infrastructure simulation.

The assignment does not require a real AI model. This service simulates an
internal AI component that may receive requests from the worker and return a
structured decision. It also serves as an example of an internal service with
controlled communication and metrics exposure.
"""

import os
from datetime import datetime

from flask import Flask, Response, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

APP_PORT = int(os.environ.get("PORT", 9001))

app = Flask(__name__)

REQUEST_COUNT = Counter("ai_agent_requests_total", "Total AI agent requests")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "ai-agent",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


@app.route("/metrics", methods=["GET"])
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route("/process", methods=["POST"])
def process_request():
    """Return a structured AI-style decision without requiring a real model."""
    REQUEST_COUNT.inc()

    payload = request.get_json(force=True, silent=True) or {}
    patient_id = payload.get("patient_id", 0)

    # This mock decision intentionally demonstrates that the AI/agent service
    # can return a structured response which the worker can evaluate.
    response = {
        "service": "ai-agent",
        "patient_id": patient_id,
        "decision": "approve",
        "confidence": 0.92,
        "recommendation": "Proceed with asynchronous healthcare workflow.",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    return jsonify(response), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT, debug=False)
