"""
scripts/simulate_rogue_v2.py

Red-team v2: concurrent + multi-context + multi-agent attacks against /kernel/dispatch sys_claim.

Goals:
A) Same resource_id, DIFFERENT context_hash (should NOT all succeed; should be single winner, others CONFLICT/REPLAY)
B) Same resource_id, DIFFERENT owner_id (should be single winner; others conflict)
C) Hot-loop retry with tiny sleeps (backoff violation) + jittered context attempts
D) Decision-id games (reuse / collide) to prove decision_id is NOT the idempotency anchor

Usage:
  python3 scripts/simulate_rogue_v2.py
"""

import hashlib
import json
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

URL = "http://localhost:8001/kernel/dispatch"


def sha256_json(material) -> str:
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def post_sys_claim(payload: dict, timeout=8):
    r = requests.post(URL, json=payload, timeout=timeout)
    try:
        data = r.json()
    except Exception:
        data = {"_raw": r.text}
    return r.status_code, data


def mk_payload(*, decision_id, context_hash, resource_type, resource_id, owner_id, duration_seconds=60):
    return {
        "syscall_name": "sys_claim",
        "payload": {
            "decision_id": decision_id,
            "context_hash": context_hash,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "owner_id": owner_id,
            "duration_seconds": duration_seconds,
        },
    }


def print_result(tag, i, status, data):
    outcome = data.get("outcome_code")
    trace = data.get("trace_id") or data.get("_trace_id") or data.get("trace")  # best-effort
    extra = ""
    if "error_code" in data:
        extra += f" error_code={data.get('error_code')}"
    if "message" in data:
        extra += f" msg={str(data.get('message'))[:80]}"
    if trace:
        extra += f" trace={trace}"
    print(f"[{tag}] #{i} HTTP {status} outcome={outcome}{extra}")


# ---------------------------
# Attack A: multi-context, same resource
# ---------------------------
def attack_multi_context_same_resource(n=24, resource_id=42001):
    print("\n🚨 Attack A: multi-context SAME resource_id (expect: ONE success, rest conflict/replay)")
    tag = "A"
    start_barrier = threading.Barrier(n)

    def worker(i):
        agent_id = f"evil-agent-{i%6}"  # a few distinct agents
        # NOTE: vary semantic intent to force different context_hash
        context_material = {
            "agent_id": agent_id,
            "task_id": "demo-task",
            "plan_step": "claim_resource",
            "intent_code": "CLAIM",
            # semantic variance (this SHOULD make a new context hash)
            "subgoal": f"subgoal-{i}",
            "nonce": random.randint(1, 10_000_000),
        }
        ch = sha256_json(context_material)
        payload = mk_payload(
            decision_id=f"evil-decision-A-{i}",
            context_hash=ch,
            resource_type="demo",
            resource_id=resource_id,
            owner_id=agent_id,
            duration_seconds=60,
        )
        start_barrier.wait()
        status, data = post_sys_claim(payload)
        return i, status, data

    with ThreadPoolExecutor(max_workers=min(n, 64)) as ex:
        futures = [ex.submit(worker, i) for i in range(n)]
        for f in as_completed(futures):
            i, status, data = f.result()
            print_result(tag, i, status, data)


# ---------------------------
# Attack B: same context_hash, different owners
# ---------------------------
def attack_same_context_different_owner(n=12, resource_id=42001):
    print("\n🚨 Attack B: SAME context_hash, DIFFERENT owner_id (expect: deterministic single winner; others conflict/replay)")
    tag = "B"
    # Everyone shares identical context -> same context_hash
    shared_context = {
        "agent_id": "evil-swarm",
        "task_id": "demo-task",
        "plan_step": "claim_resource",
        "intent_code": "CLAIM",
        "shared": True,
    }
    ch = sha256_json(shared_context)

    start_barrier = threading.Barrier(n)

    def worker(i):
        owner = f"evil-owner-{i}"
        payload = mk_payload(
            decision_id=f"evil-decision-B-{i}",
            context_hash=ch,
            resource_type="demo",
            resource_id=resource_id,
            owner_id=owner,
            duration_seconds=60,
        )
        start_barrier.wait()
        status, data = post_sys_claim(payload)
        return i, status, data

    with ThreadPoolExecutor(max_workers=min(n, 64)) as ex:
        futures = [ex.submit(worker, i) for i in range(n)]
        for f in as_completed(futures):
            i, status, data = f.result()
            print_result(tag, i, status, data)


# ---------------------------
# Attack C: backoff violation loop + jittered contexts
# ---------------------------
def attack_backoff_violation_loop(rounds=20, resource_id=42001):
    print("\n🚨 Attack C: backoff violation loop (tiny sleep) + jittered context (expect: conflict/replay; kernel should not melt)")
    tag = "C"
    for i in range(rounds):
        agent_id = "evil-agent"
        # jitter context each time (new hash)
        context_material = {
            "agent_id": agent_id,
            "task_id": "demo-task",
            "plan_step": "claim_resource",
            "intent_code": "CLAIM",
            "retry_epoch": i,
            "jitter": random.randint(1, 10_000_000),
        }
        ch = sha256_json(context_material)
        payload = mk_payload(
            decision_id=f"evil-decision-C-{i}",
            context_hash=ch,
            resource_type="demo",
            resource_id=resource_id,
            owner_id=agent_id,
            duration_seconds=60,
        )
        status, data = post_sys_claim(payload)
        print_result(tag, i, status, data)

        # ❌ explicit backoff violation
        time.sleep(0.05)


# ---------------------------
# Attack D: decision_id collision games
# ---------------------------
def attack_decision_id_collision(attempts=10, resource_id=42001):
    print("\n🚨 Attack D: decision_id collision (same decision_id, different context_hash) (expect: kernel should ignore decision_id as anchor)")
    tag = "D"
    decision_id = "evil-decision-COLLIDE"

    for i in range(attempts):
        agent_id = f"evil-agent-{i%3}"
        context_material = {
            "agent_id": agent_id,
            "task_id": "demo-task",
            "plan_step": "claim_resource",
            "intent_code": "CLAIM",
            "variant": i,  # ensures different context_hash
        }
        ch = sha256_json(context_material)
        payload = mk_payload(
            decision_id=decision_id,      # 👈 collision
            context_hash=ch,              # 👈 different
            resource_type="demo",
            resource_id=resource_id,
            owner_id=agent_id,
            duration_seconds=60,
        )
        status, data = post_sys_claim(payload)
        print_result(tag, i, status, data)
        time.sleep(0.1)


def main():
    random.seed(7)

    # Use separate resource IDs per attack if you want to avoid interference between them.
    # For now, all hit 42001 so you can observe cross-attack interactions too.

    attack_multi_context_same_resource(n=24, resource_id=42001)
    attack_same_context_different_owner(n=12, resource_id=42001)
    attack_backoff_violation_loop(rounds=20, resource_id=42001)
    attack_decision_id_collision(attempts=10, resource_id=42001)


if __name__ == "__main__":
    main()
