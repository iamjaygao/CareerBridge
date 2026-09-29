#!/usr/bin/env python3
"""
HTTP-level booking race against the running stack (nginx -> gunicorn workers).

For each slot, every user POSTs lock-slot at the same instant (barrier).
Exactly one request may get 201; every other must be 409 (a real conflict,
not a 5xx or a rate-limit response). Rounds are spaced so nginx's per-IP
burst allowance refills between them.

Usage: http_booking_race.py <setup-json-file> [base-url]
"""
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter

setup = json.load(open(sys.argv[1]))
base = sys.argv[2] if len(sys.argv) > 2 else "http://localhost"
url = f"{base}/api/v1/decision-slots/lock-slot/"
PAUSE_SECONDS = 12  # nginx api_limit: 60r/m, burst 20


def post(token, slot_id):
    body = json.dumps({"time_slot_id": slot_id, "service_id": setup["service_id"]}).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


failures = 0
for round_no, slot_id in enumerate(setup["slots"]):
    tokens = setup["tokens"]
    barrier = threading.Barrier(len(tokens))
    codes = [None] * len(tokens)

    def worker(i):
        barrier.wait()
        codes[i] = post(tokens[i], slot_id)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(len(tokens))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    counts = Counter(codes)
    ok = counts == Counter({201: 1, 409: len(tokens) - 1})
    failures += not ok
    print(f"round {round_no} slot {slot_id}: {dict(counts)} {'OK' if ok else 'FAIL'}", flush=True)
    time.sleep(PAUSE_SECONDS)

print(f"{len(setup['slots']) - failures}/{len(setup['slots'])} rounds had exactly one winner")
sys.exit(1 if failures else 0)
