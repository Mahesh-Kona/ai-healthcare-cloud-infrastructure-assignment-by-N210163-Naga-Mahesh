#!/usr/bin/env python3
"""
Simple load generator for the healthcare cloud simulation.

This script sends a configurable number of requests to the public API
and can also enqueue worker jobs for asynchronous processing.
"""

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from urllib import request, error

API_URL = 'http://localhost:18080'


def call_api(patient_id: int):
    payload = {
        'patient_id': patient_id,
        'action': 'create_appointment',
        'details': {
            'doctor_id': 'dr-001',
            'slot': '2026-09-12T10:00:00Z'
        }
    }

    req = request.Request(
        f'{API_URL}/api/appointments',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        with request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode('utf-8', errors='ignore')
            print(f"patient={patient_id} status={resp.status} body={body}")
    except error.HTTPError as exc:
        print(f"patient={patient_id} http_error={exc.code}")
    except Exception as exc:
        print(f"patient={patient_id} error={exc}")


def main():
    if len(sys.argv) < 2:
        print('Usage: python generate_load.py <request_count>')
        sys.exit(1)

    try:
        count = int(sys.argv[1])
    except ValueError:
        print('Request count must be an integer.')
        sys.exit(1)

    print(f"Generating {count} API requests...")

    start = time.time()
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = [pool.submit(call_api, i) for i in range(count)]
        for future in futures:
            future.result()

    elapsed = time.time() - start
    print(f"Completed in {elapsed:.2f} seconds")


if __name__ == '__main__':
    main()
